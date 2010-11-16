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

import re
import socket
import ssl
import httplib
import urllib2

class VerifiedHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        from libcloud.base import CA_CERTS_FILE_PATH

        sock = socket.create_connection((self.host, self.port),
                                        self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, \
                                    cert_reqs = ssl.CERT_REQUIRED, \
                                    ca_certs = CA_CERTS_FILE_PATH, \
                                    ssl_version = ssl.PROTOCOL_TLSv1)

        cert = self.sock.getpeercert()
        if not self._verify_hostname(self.host, cert):
            raise ssl.SSLError('Failed to verify hostname')

    def _verify_hostname(self, hostname, cert):
        common_name = self._get_commonName(cert)
        alt_names = self._get_subjectAltName(cert)

        if self._is_wildcard_name(common_name):
            regex = self._to_regex(common_name)

            if regex.match(hostname):
                return True
        else:
            if hostname == common_name:
                return True

        for alt_name in alt_names:
            if self._is_wildcard_name(alt_name):
                regex = self._to_regex(alt_name)

                if regex.match(hostname):
                    return True
            else:
                if hostname == alt_name:
                    return True

        return False

    def _get_subjectAltName(self, cert):
        if not cert.has_key('subjectAltName'):
            return []

        alt_names = []
        for value in cert['subjectAltName']:
            if value[0].lower() == 'dns':
                alt_names.append(value[0])

        return alt_names

    def _get_commonName(self, cert):
        if not cert.has_key('subject'):
            return None

        for value in cert['subject']:
            if value[0][0].lower() == 'commonname':
                return value[0][1]

        return None

    def _is_wildcard_name(self, name):
        if name.find('*') != -1:
            return True

        return False

    def _to_regex(self, name):
        regex = name.replace('*', '([^.])+').replace('.', '\.')

        return re.compile(regex)
