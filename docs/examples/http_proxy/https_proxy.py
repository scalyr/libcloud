import os.path

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import libcloud.security

HTTPS_PROXY_URL_NO_AUTH_ = 'https://<proxy hostname 1>:<proxy port 2>'

# 1. Use a custom CA bundle which is used by proxy server
# This example uses CA cert bundle used by mitmproxy proxy server
libcloud.security.CA_CERTS_PATH = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.pem')

# User an https proxy for subsequent requests
driver.connection.connection.set_http_proxy(proxy_url=PROXY_URL_NO_AUTH_1)
pprint(driver.list_nodes())