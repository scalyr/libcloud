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

# Backward compatibility for Python 2.5
from __future__ import with_statement

import os
import os.path
import mimetypes
from os.path import join as pjoin

from libcloud.types import LibcloudError
from libcloud.base import ConnectionKey

CHUNK_SIZE = 8096

class Object(object):
    """
    Represents an object (BLOB).
    """

    def __init__(self, name, size, hash, extra, meta_data, container,
                 driver):
        """
        @type name: C{str}
        @param name: Object name (must be unique per container).

        @type size: C{int}
        @param size: Object size in bytes.

        @type hash: C{string}
        @param hash Object hash.

        @type container: C{Container}
        @param container: Object container.

        @type extra: C{dict}
        @param extra: Extra attributes.

        @type meta_data: C{dict}
        @param meta_data: Optional object meta data.

        @type driver: C{StorageDriver}
        @param driver: StorageDriver instance.
        """

        self.name = name
        self.size = size
        self.hash = None
        self.container = container
        self.extra = extra or {}
        self.meta_data = meta_data or {}
        self.driver = driver

    def download(self, destination_path, overwrite_existing=False,
                 delete_on_failure=True):
        return self.driver.download_object(self, destination_path,
                                           overwrite_existing,
                                           delete_on_failure)

    def as_stream(self, chunk_size=None):
        return self.driver.object_as_stream(self, chunk_size)

    def delete(self):
        return self.driver.delete_object(self)

    def __repr__(self):
        return '<Object: name=%s, size=%s, hash=%s, provider=%s ...>' % \
        (self.name, self.size, self.hash, self.driver.name)


class Container(object):
    """
    Represents a container (bucket) which can hold multiple objects.
    """

    def __init__(self, name, extra, driver):
        """
        @type name: C{str}
        @param name: Container name (must be unique).

        @type extra: C{dict}
        @param extra: Extra attributes.

        @type driver: C{StorageDriver}
        @param driver: StorageDriver instance.
        """

        self.name = name
        self.extra = extra or {}
        self.driver = driver

    def list_objects(self):
        return self.driver.list_container_objects(self)

    def upload_object(self, file_path, object_name, file_hash=None):
        return self.driver.upload_object(file_path, object_name, file_hash)

    def download_object(self, obj, destination_path, overwrite_existing=False,
                        delete_on_failure=True):
        return self.driver.download_object(obj, destination_path)

    def object_as_stream(self, obj, chunk_size=None):
        return self.driver.object_as_stream(obj, chunk_size)

    def delete_object(self, obj):
        return self.driver.delete_object(obj)

    def delete(self):
        return self.driver.delete_container(self)

    def __repr__(self):
        return '<Container: name=%s, provider=%s>' % (self.name, self.driver.name)


class StorageDriver(object):
    """
    A base StorageDriver to derive from.
    """

    connectionCls = ConnectionKey
    name = None
    hash_type = 'md5'

    def __init__(self, key, secret=None, secure=True, host=None, port=None):
        self.key = key
        self.secret = secret
        self.secure = secure
        args = [self.key]

        if self.secret != None:
            args.append(self.secret)

        args.append(secure)

        if host != None:
            args.append(host)

        if port != None:
            args.append(port)

        self.connection = self.connectionCls(*args)

        self.connection.driver = self
        self.connection.connect()

    def list_containters(self):
        raise NotImplementedError, \
            'list_containers not implemented for this driver'

    def list_objects(self, container):
        raise NotImplementedError, \
            'list_objects not implemented for this driver'

    def get_container(self, container_name):
        """
        Return a container instance.

        @type container_name: C{str}
        @param container_name: Container name.

        @return: C{Container} instance.
        """
        raise NotImplementedError, \
            'get_object not implemented for this driver'

    def get_object(self, container_name, object_name):
        """
        Return an object instance.

        @type container_name: C{str}
        @param container_name: Container name.

        @type object_name: C{str}
        @param object_name: Object name.

        @return: C{Object} instance.
        """
        raise NotImplementedError, \
            'get_object not implemented for this driver'

    def download_object(self, obj, destination_path, delete_on_failure=True):
        """
        Download an object to the specified destination path.

        @type obj; C{Object}
        @param obj: Object instance.

        @type destination_path: C{str}
        @type destination_path: Path where an object will  be downloaded to.

        @type overwrite_existing: C{bool}
        @type overwrite_existing: True to overwrite an existing file.

        @type delete_on_failure: C{bool}
        @param delete_on_failure: True to delete a partially downloaded file if
        the download was not successful (hash mismatch / file size).

        @return C{bool} True if an object has been successfully downloaded, False
        otherwise.
        """
        raise NotImplementedError, \
            'download_object not implemented for this driver'

    def object_as_stream(self, obj, chunk_size=None):
        """
        Return a generator which yields object data.

        @type obj: C{Object}
        @param obj: Object instance

        @type chunk_size: C{int}
        @param chunk_size: Optional chunk size (in bytes).
        """
        raise NotImplementedError, \
            'object_as_stream not implemented for this driver'

    def upload_object(self, file_path, container, object_name, extra=None,
                      file_hash=None):
        raise NotImplementedError, \
            'upload_object not implemented for this driver'

    def object_as_file(self, obj):
        raise NotImplementedError, \
            'object_as_file not implemented for this driver'

    def delete_container(self, obj):
        raise NotImplementedError, \
            'delete_container not implemented for this driver'

    def delete_object(self, obj):
        """
        Delete an object.

        @type obj: C{Object}
        @param obj: Object instance.

        @return: C{bool} True on success.
        """
        raise NotImplementedError, \
            'delete_object not implemented for this driver'

    def create_container(self, container):
        raise NotImplementedError, \
            'create_container not implemented for this driver'

    def delete_container(self, container):
        raise NotImplementedError, \
            'delete_container not implemented for this driver'

    def _guess_file_mime_type(self, file_path):
        filename = os.path.basename(file_path)
        (mimetype, encoding) = mimetypes.guess_type(filename)
        return mimetype, encoding

    def _get_object_as_stream(self, response, chunk_size=None):
        """
        Generator which reads and yields object data in chunks.

        @type response: C{HTTPResponse}
        @param response: HTTP response.

        @type obj: C{obj}
        @param obj: Object instance.

        @type chunk_size: C{int}
        @param chunk_size: Optional chunk size (defaults to CHUNK_SIZE)
        """
        chunk_size = chunk_size or CHUNK_SIZE

        try:
            data_read = response.read(chunk_size)

            while len(data_read) > 0:
                yield data_read
                data_read = response.read(chunk_size)
        except Exception, e:
            raise e

    def _save_object(self, response, obj, destination_path,
                     overwrite_existing=False, delete_on_failure=True):

        if not os.path.exists(destination_path):
            raise LibcloudError(value='Path %s does not exist' % (destination_path),
                                driver=self)

        file_path = pjoin(destination_path, obj.name)

        if os.path.exists(file_path) and not overwrite_existing:
            raise LibcloudError(value='File %s already exists, but ' % (file_path) +
                                'overwrite_existing=False',
                                driver=self)

        stream = self._get_object_as_stream(response)

        data_read = stream.next()
        bytes_transferred = 0

        with open(file_path, 'wb') as file_handle:
            while len(data_read) > 0:
                file_handle.write(data_read)
                bytes_transferred += len(data_read)

                try:
                    data_read = stream.next()
                except StopIteration:
                    data_read = ''

        if obj.size != bytes_transferred:
            # Transfer failed, support retry?
            if delete_on_failure:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

            return False

        return True

    def _upload_object(self, request, file_path, calculate_hash=True):
        file_hash = None
        if calculate_hash:
            object_hash = hashlib.md5()

        bytes_transferred = 0
        with open (file_path, 'rb') as file_handle:
            chunk = file_handle.read(CHUNK_SIZE)

            while len(chunk) > 0:
                if calculate_hash:
                    try:
                        request.write(chunk)
                    except Exception:
                        # Timeout, etc.
                        return False, None

                    object_hash.update(chunk)
                    chunk = file_handle.read(CHUNK_SIZE)
                    bytes_transferred += len(chunk)

        return True, file_hash.hexdigest()


