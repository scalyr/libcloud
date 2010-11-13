# -*- coding: utf-8 -*-
# Copyright (c) 2010, Tomaž Muraus
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Tomaž Muraus nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Based on example from post "HTTPS Certificate Verification in Python With urllib2" -
# http://www.muchtooscrawled.com/2010/03/https-certificate-verification-in-python-with-urllib2/

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

        if (hostname == common_name) or hostname in alt_names:
            return True

        return False

    def _get_subjectAltName(self, cert):
        if not cert.has_key('subjectAltName'):
            return None

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
