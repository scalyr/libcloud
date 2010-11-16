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

from libcloud.httplib_ssl import VerifiedHTTPSConnection

class HttpLibTests(unittest.TestCase):
    def setUp(self):
        self.httplib_object = VerifiedHTTPSConnection('foo.bar')

    def test_is_valid_wildcard_name(self):
        self.assertFalse(self.httplib_object._is_wildcard_name('foo.bar'))
        self.assertFalse(self.httplib_object._is_wildcard_name('bar.foo'))
        self.assertTrue(self.httplib_object._is_wildcard_name('*.foo.bar'))
        self.assertTrue(self.httplib_object._is_wildcard_name('*.*.foo.bar'))

    def test_wildcard_match(self):
        # Reference: http://www.faqs.org/rfcs/rfc2818.html &
        #            http://www.faqs.org/rfcs/rfc2459.html
        matches_true = [
            ('*.a.com', 'foo.a.com'),
            ('f*.com', 'foo.com'),
            ('*.*.foo.com', 'bar.foo.foo.com'),
            ('*.*.foo.com', 'a.b.foo.com'),
            ('*.*.foo.com', 'a.a.foo.com'),
        ]

        matches_false = [
            ('*.a.com', 'bar.foo.a.com'),
            ('f*.com', 'bar.com'),
            ('f*.com', 'barfoo.com'),
            ('*.*.foo.com', 'foo.com'),
            ('*.*.foo.com', 'bar.foo.com'),
            ('*.*.foo.com', '.foo.com'),
            ('*.*.foo.com', '.bar.foo.com'),
        ]

        for wildcard_name, match_name in matches_true:
            regex = self.httplib_object._to_regex(wildcard_name)
            self.assertTrue(regex.match(match_name))

        for wildcard_name, match_name in matches_false:
            regex = self.httplib_object._to_regex(wildcard_name)
            self.assertFalse(regex.match(match_name))
