# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import httplib
import urlparse

try:
    import json
except:
    import simplejson as json

from libcloud.types import MalformedResponseError, LibcloudError
from libcloud.types import InvalidCredsError
from libcloud.base import ConnectionUserAndKey, Response

from libcloud.storage.providers import Provider
from libcloud.storage.base import Object, Container, StorageDriver
from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ContainerIsNotEmptyError
from libcloud.storage.types import ObjectDoesNotExistError

AUTH_HOST_US = 'auth.api.rackspacecloud.com'
AUTH_HOST_UK = 'lon.auth.api.rackspacecloud.com'
API_VERSION = 'v1.0'

class CloudFilesResponse(Response):

    def success(self):
        i = int(self.status)
        return i >= 200 and i <= 299

    def parse_body(self):
        if not self.body:
            return None

        try:
            data = json.loads(self.body)
        except:
            raise MalformedResponseError('Failed to parse JSON',
                                         body=self.body,
                                         driver=CloudFilesStorageDriver)

        return data


class CloudFilesConnection(ConnectionUserAndKey):
    """
    Base connection class for the Cloudfiles driver.
    """

    auth_host = None
    api_version = API_VERSION
    responseCls = CloudFilesResponse

    def __init__(self, user_id, key, secure=True):
        self.cdn_management_url = None
        self.storage_url = None
        self.auth_token = None
        self.request_path = None

        self.__host = None
        super(CloudFilesConnection, self).__init__(user_id, key, secure)

    def add_default_headers(self, headers):
        headers['X-Auth-Token'] = self.auth_token
        headers['Accept'] = 'application/json'
        return headers

    @property
    def host(self):
        """
        Rackspace uses a separate host for API calls which is only provided
        after an initial authentication request. If we haven't made that
        request yet, do it here. Otherwise, just return the management host.
        """
        if not self.__host:
            # Initial connection used for authentication
            conn = self.conn_classes[self.secure](self.auth_host, self.port[self.secure])
            conn.request(
                method='GET',
                url='/%s' % (self.api_version),
                headers={
                    'X-Auth-User': self.user_id,
                    'X-Auth-Key': self.key
                }
            )

            resp = conn.getresponse()

            if resp.status != httplib.NO_CONTENT:
                raise InvalidCredsError()

            headers = dict(resp.getheaders())

            try:
                self.storage_url = headers['x-storage-url']
                self.cdn_management_url = headers['x-cdn-management-url']
                self.auth_token = headers['x-auth-token']
            except KeyError:
                raise InvalidCredsError()

            scheme, server, self.request_path, param, query, fragment = (
                urlparse.urlparse(self.storage_url)
            )

            if scheme is "https" and self.secure is not True:
                raise InvalidCredsError()

            # Set host to where we want to make further requests to;
            self.__host = server
            conn.close()

        return self.__host

    def request(self, action, params=None, data='', headers=None, method='GET',
                raw=False):
        if not headers:
            headers = {}
        if not params:
            params = {}
        # Due to first-run authentication request, we may not have a path
        if self.request_path:
            action = self.request_path + action
            params['format'] = 'json'
        if method == "POST":
            headers = {'Content-Type': 'application/json; charset=UTF-8'}

        return super(CloudFilesConnection, self).request(
            action=action,
            params=params, data=data,
            method=method, headers=headers,
            raw=raw
        )


class CloudFilesUSConnection(CloudFilesConnection):
    """
    Connection class for the Cloudfiles US endpoint.
    """

    auth_host = AUTH_HOST_US


class CloudFilesUKConnection(CloudFilesConnection):
    """
    Connection class for the Cloudfiles UK endpoint.
    """

    auth_host = AUTH_HOST_UK


class CloudFilesStorageDriver(StorageDriver):
    """
    Base CloudFiles driver.

    You should never create an instance of this class directly but use US/US
    class.
    """
    name = 'CloudFiles'
    connectionCls = CloudFilesConnection
    hash_type = 'md5'

    def list_containers(self):
        response = self.connection.request('')

        if response.status == httplib.NO_CONTENT:
            return []
        elif response.status == httplib.OK:
            return self._to_container_list(json.loads(response.body))

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def list_container_objects(self, container):
        response = self.connection.request('/%s' % (container.name))

        if response.status == httplib.NO_CONTENT:
            # Empty or inexistent container
            return []
        elif response.status == httplib.OK:
            return self._to_object_list(json.loads(response.body), container)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_container(self, container_name):
        response = self.connection.request('/%s' % (container_name),
                                                    method='HEAD')

        if response.status == httplib.NO_CONTENT:
            container = self._headers_to_container(container_name, response.headers)
            return container
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(None, self, container_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def get_object(self, container_name, object_name):
        container = self.get_container(container_name)
        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name),
                                                       method='HEAD')

        if response.status in [ httplib.OK, httplib.NO_CONTENT ]:
            obj = self._headers_to_object(object_name, container, response.headers)
            return obj
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(None, self, object_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def create_container(self, name):
        name = self._clean_container_name(name)
        response = self.connection.request('/%s' % (name), method='PUT')

        if response.status == httplib.CREATED:
            # Accepted mean that container is not yet created but it will be
            # eventually
            extra = { 'object_count': 0 }
            container = Container(name=name, extra=extra, driver=self)

            return container
        elif response.status == httplib.ACCEPTED:
            error = ContainerAlreadyExistsError(None, self, name)
            raise error

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def delete_container(self, container):
        name = self._clean_container_name(container.name)

        # Only empty container can be deleted
        response = self.connection.request('/%s' % (name), method='DELETE')

        if response.status == httplib.NO_CONTENT:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ContainerDoesNotExistError(name=name)
        elif response.status == httplib.CONFLICT:
            # @TODO: Add "delete_all_objects" parameter?
            raise ContainerIsNotEmptyError(name=name)

    def download_object(self, obj, destination_path, overwrite_existing=False,
                        delete_on_failure=True):
        return self._get_object(obj, self._save_object,
                                {'obj': obj, 
                                 'destination_path': destination_path,
                                 'overwrite_existing': overwrite_existing,
                                 'delete_on_failure': delete_on_failure})

    def object_as_stream(self, obj, chunk_size=None):
        return self._get_object(obj, self._get_object_as_stream,
                                {'chunk_size': chunk_size})

    def delete_object(self, obj):
        container_name = obj.container.name
        object_name = obj.name

        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name), method='DELETE')

        if response.status == httplib.NO_CONTENT:
            return True
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(name=object_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))

    def _get_object(self, obj, callback, callback_args):
        container_name = obj.container.name
        object_name = obj.name

        response = self.connection.request('/%s/%s' % (container_name,
                                                       object_name),
                                           raw=True)

        callback_args['response'] = response.response

        if response.status == httplib.OK:
            return callback(**callback_args)
        elif response.status == httplib.NOT_FOUND:
            raise ObjectDoesNotExistError(name=object_name)

        raise LibcloudError('Unexpected status code: %s' % (response.status))


    def _clean_container_name(self, name):
        """
        Remove leading slash from the container name.
        """
        if name.startswith('/'):
            name = name[1:]

        return name

    def _to_container_list(self, response):
        # @TODO: Handle more then 10k containers - use "lazy list"?
        containers = []

        for container in response:
            extra = { 'object_count': int(container['count']),
                      'size': int(container['bytes'])}
            containers.append(Container(name=container['name'], extra=extra,
                                        driver=self))

        return containers

    def _to_object_list(self, response, container):
        objects = []

        for obj in response:
            name = obj['name']
            size = int(obj['bytes'])
            hash = obj['hash']
            extra = { 'content_type': obj['content_type'],
                      'last_modified': obj['last_modified'] }
            objects.append(Object(name=name, size=size, hash=hash, extra=extra,
                                  meta_data=None, container=container, driver=self))

        return objects

    def _headers_to_container(self, name, headers):
        size = int(headers.get('x-container-bytes-used', 0))
        object_count = int(headers.get('x-container-object-count', 0))

        extra = { 'object_count': object_count,
                  'size': size }
        container = Container(name=name, extra=extra, driver=self)
        return container

    def _headers_to_object(self, name, container, headers):
        size = int(headers.pop('content-length', 0))
        last_modified = headers.pop('last-modified', None)
        etag = headers.pop('etag', None)
        content_type = headers.pop('content-type', None)

        meta_data = {}
        for key, value in headers.iteritems():
            if key.find('x-object-meta-') != -1:
                key = key.replace('x-object-meta-', '')
                meta_data[key] = value

        extra = { 'content_type': content_type, 'last_modified': last_modified,
                  'etag': etag }

        obj = Object(name=name, size=size, hash=None, extra=extra,
                     meta_data=meta_data, container=container, driver=self)
        return obj

class CloudFilesUSStorageDriver(CloudFilesStorageDriver):
    """
    Cloudfiles storage driver for the US endpoint.
    """

    type = Provider.CLOUDFILES_US
    name = 'CloudFiles (US)'
    connectionCls = CloudFilesUSConnection

class CloudFilesUKStorageDriver(CloudFilesStorageDriver):
    """
    Cloudfiles storage driver for the UK endpoint.
    """

    type = Provider.CLOUDFILES_UK
    name = 'CloudFiles (UK)'
    connectionCls = CloudFilesUKConnection
