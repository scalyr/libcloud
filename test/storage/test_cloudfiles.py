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
import sys
import unittest
import httplib

from libcloud.storage.base import Container
from libcloud.storage.drivers.cloudfiles import CloudFilesStorageDriver

from test import MockHttp
from test.file_fixtures import StorageFileFixtures

class CloudFilesTests(unittest.TestCase):

    def setUp(self):
        CloudFilesStorageDriver.connectionCls.conn_classes = (None,
                                                              CloudFilesMockHttp)
        CloudFilesMockHttp.type = None
        self.driver = CloudFilesStorageDriver('dummy', 'dummy')

    def test_get_meta_data(self):
        meta_data = self.driver.get_meta_data()

    def test_list_containers(self):
        CloudFilesMockHttp.type = 'EMPTY'
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 0)

        CloudFilesMockHttp.type = None
        containers = self.driver.list_containers()
        self.assertEqual(len(containers), 3)

        container = [c for c in containers if c.name == 'container2'][0]
        self.assertEqual(container.extra['object_count'], 120)
        self.assertEqual(container.extra['size'], 340084450)

    def test_list_container_objects(self):
        CloudFilesMockHttp.type = 'EMPTY'
        container = Container(name='test_container', extra={}, driver=self.driver)
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 0)

        CloudFilesMockHttp.type = None
        objects = self.driver.list_container_objects(container=container)
        self.assertEqual(len(objects), 4)

        obj = [o for o in objects if o.name == 'foo test 1'][0]
        self.assertEqual(obj.hash, '16265549b5bda64ecdaa5156de4c97cc')
        self.assertEqual(obj.size, 1160520)
        self.assertEqual(obj.container.name, 'test_container')

    def test_get_container(self):
        container = self.driver.get_container(container_name='test_container')
        self.assertEqual(container.name, 'test_container')
        self.assertEqual(container.extra['object_count'], 800)
        self.assertEqual(container.extra['size'], 1234568)

    def test_get_object(self):
        obj = self.driver.get_object(container_name='test_container',
                                     object_name='test_object')
        self.assertEqual(obj.container.name, 'test_container')
        self.assertEqual(obj.size, 555)
        self.assertEqual(obj.extra['content_type'], 'application/zip')
        self.assertEqual(obj.extra['etag'], '6b21c4a111ac178feacf9ec9d0c71f17')
        self.assertEqual(obj.extra['last_modified'], 'Tue, 25 Jan 2011 22:01:49 GMT')
        self.assertEqual(obj.meta_data['foo-bar'], 'test 1')
        self.assertEqual(obj.meta_data['bar-foo'], 'test 2')

class CloudFilesMockHttp(MockHttp):

    fixtures = StorageFileFixtures('cloudfiles')

    # fake auth token response
    def _v1_0(self, method, url, body, headers):
        headers = {'x-server-management-url': 'https://servers.api.rackspacecloud.com/v1.0/slug',
                   'x-auth-token': 'FE011C19',
                   'x-cdn-management-url': 'https://cdn.clouddrive.com/v1/MossoCloudFS',
                   'x-storage-token': 'FE011C19',
                   'x-storage-url': 'https://storage4.clouddrive.com/v1/MossoCloudFS'}
        return (httplib.NO_CONTENT, "", headers, httplib.responses[httplib.NO_CONTENT])

    def _v1_MossoCloudFS_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_containers_empty.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS(self, method, url, body, headers):
        if method == 'GET':
            # list_containers
            body = self.fixtures.load('list_containers.json')
            status_code = httplib.OK
            headers = {}
        elif method == 'HEAD':
            # get_meta_data
            body = self.fixtures.load('meta_data.json')
            status_code = httplib.NO_CONTENT
            headers = { 'x-account-container-count': 10,
                        'x-account-object-count': 400,
                        'x-account-bytes-used': 1234567
                      }
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_EMPTY(self, method, url, body, headers):
        body = self.fixtures.load('list_container_objects_empty.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container(self, method, url, body, headers):
        if method == 'GET':
            # list_container_objects
            body = self.fixtures.load('list_container_objects.json')
            status_code = httplib.OK
            headers = {}
        elif method == 'HEAD':
            # get_container
            body = self.fixtures.load('list_container_objects_empty.json')
            status_code = httplib.NO_CONTENT
            headers = { 'x-container-object-count': 800,
                        'x-container-bytes-used': 1234568
                      }
        return (status_code, body, headers, httplib.responses[httplib.OK])

    def _v1_MossoCloudFS_test_container_test_object(self, method, url, body,
                                                    headers):
        if method == 'HEAD':
            # get_object
            body = self.fixtures.load('list_container_objects_empty.json')
            status_code = httplib.NO_CONTENT
            headers = { 'content-length': 555,
                        'last-modified': 'Tue, 25 Jan 2011 22:01:49 GMT',
                        'etag': '6b21c4a111ac178feacf9ec9d0c71f17',
                        'x-object-meta-foo-bar': 'test 1',
                        'x-object-meta-bar-foo': 'test 2',
                        'content-type': 'application/zip'}
        return (status_code, body, headers, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())
