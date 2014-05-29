"""
Mixin classes which implement different OpenStack extensions functionality.
"""

import httplib

__all__ = [
    'OpenStackFloatingIPsExtensionMixin',
    'OpenStackFloatingIPPoolsExtensionMixin',

    'OpenStack_1_1_FloatingIpPool',
    'OpenStack_1_1_FloatingIpAddress'
]


class OpenStack_1_1_FloatingIpPool(object):
    """
    Floating IP Pool info.
    """

    def __init__(self, name, connection):
        self.name = name
        self.connection = connection

    def list_floating_ips(self):
        """
        List floating IPs in the pool

        :rtype: ``list`` of :class:`OpenStack_1_1_FloatingIpAddress`
        """
        return self._to_floating_ips(
            self.connection.request('/os-floating-ips').object)

    def _to_floating_ips(self, obj):
        ip_elements = obj['floating_ips']
        return [self._to_floating_ip(ip) for ip in ip_elements]

    def _to_floating_ip(self, obj):
        return OpenStack_1_1_FloatingIpAddress(obj['id'], obj['ip'], self,
                                               obj['instance_id'])

    def get_floating_ip(self, ip):
        """
        Get specified floating IP from the pool

        :param      ip: floating IP to get
        :type       ip: ``str``

        :rtype: :class:`OpenStack_1_1_FloatingIpAddress`
        """
        ip_obj, = [x for x in self.list_floating_ips() if x.ip_address == ip]
        return ip_obj

    def create_floating_ip(self):
        """
        Create new floating IP in the pool

        :rtype: :class:`OpenStack_1_1_FloatingIpAddress`
        """
        resp = self.connection.request('/os-floating-ips',
                                       method='POST',
                                       data={'pool': self.name})
        data = resp.object['floating_ip']
        id = data['id']
        ip_address = data['ip']
        return OpenStack_1_1_FloatingIpAddress(id, ip_address, self)

    def delete_floating_ip(self, ip):
        """
        Delete specified floating IP from the pool

        :param      ip: floating IP to remove
        :type       ip::class:`OpenStack_1_1_FloatingIpAddress`

        :rtype: ``bool``
        """
        resp = self.connection.request('/os-floating-ips/%s' % ip.id,
                                       method='DELETE')
        return resp.status in (httplib.NO_CONTENT, httplib.ACCEPTED)

    def __repr__(self):
        return ('<OpenStack_1_1_FloatingIpPool: name=%s>' % self.name)


class OpenStack_1_1_FloatingIpAddress(object):
    """
    Floating IP info.
    """

    def __init__(self, id, ip_address, pool, node_id=None, driver=None):
        self.id = str(id)
        self.ip_address = ip_address
        self.pool = pool
        self.node_id = node_id
        self.driver = driver

    def delete(self):
        """
        Delete this floating IP

        :rtype: ``bool``
        """
        if self.pool is not None:
            return self.pool.delete_floating_ip(self)
        elif self.driver is not None:
            return self.driver.ex_delete_floating_ip(self)

    def __repr__(self):
        return ('<OpenStack_1_1_FloatingIpAddress: id=%s, ip_addr=%s,'
                ' pool=%s, driver=%s>'
                % (self.id, self.ip_address, self.pool, self.driver))


class OpenStackFloatingIPsExtensionMixin(object):
    """
    Floating IPs extension.

    http://docs.openstack.org/api/openstack-compute/2/content/ext-os-floating-ips.html
    """
    def ex_list_floating_ips(self):
        """
        List floating IPs

        :rtype: ``list`` of :class:`OpenStack_1_1_FloatingIpAddress`
        """
        return self._to_floating_ips(
            self.connection.request('/os-floating-ips').object)

    def ex_get_floating_ip(self, ip):
        """
        Get specified floating IP

        :param      ip: floating IP to get
        :type       ip: ``str``

        :rtype: :class:`OpenStack_1_1_FloatingIpAddress`
        """
        floating_ips = self.ex_list_floating_ips()
        ip_obj, = [x for x in floating_ips if x.ip_address == ip]
        return ip_obj

    def ex_create_floating_ip(self):
        """
        Create new floating IP

        :rtype: :class:`OpenStack_1_1_FloatingIpAddress`
        """
        resp = self.connection.request('/os-floating-ips',
                                       method='POST',
                                       data={})
        data = resp.object['floating_ip']
        id = data['id']
        ip_address = data['ip']
        return OpenStack_1_1_FloatingIpAddress(id, ip_address, self)

    def ex_delete_floating_ip(self, ip):
        """
        Delete specified floating IP

        :param      ip: floating IP to remove
        :type       ip::class:`OpenStack_1_1_FloatingIpAddress`

        :rtype: ``bool``
        """
        resp = self.connection.request('/os-floating-ips/%s' % ip.id,
                                       method='DELETE')
        return resp.status in (httplib.NO_CONTENT, httplib.ACCEPTED)

    def ex_attach_floating_ip_to_node(self, node, ip):
        """
        Attach the floating IP to the node

        :param      node: node
        :type       node: :class:`Node`

        :param      ip: floating IP to attach
        :type       ip: ``str`` or :class:`OpenStack_1_1_FloatingIpAddress`

        :rtype: ``bool``
        """
        address = ip.ip_address if hasattr(ip, 'ip_address') else ip
        data = {
            'addFloatingIp': {'address': address}
        }
        resp = self.connection.request('/servers/%s/action' % node.id,
                                       method='POST', data=data)
        return resp.status == httplib.ACCEPTED

    def ex_detach_floating_ip_from_node(self, node, ip):
        """
        Detach the floating IP from the node

        :param      node: node
        :type       node: :class:`Node`

        :param      ip: floating IP to remove
        :type       ip: ``str`` or :class:`OpenStack_1_1_FloatingIpAddress`

        :rtype: ``bool``
        """
        address = ip.ip_address if hasattr(ip, 'ip_address') else ip
        data = {
            'removeFloatingIp': {'address': address}
        }
        resp = self.connection.request('/servers/%s/action' % node.id,
                                       method='POST', data=data)
        return resp.status == httplib.ACCEPTED


    def _to_floating_ips(self, obj):
        ip_elements = obj['floating_ips']
        return [self._to_floating_ip(ip) for ip in ip_elements]

    def _to_floating_ip(self, obj):
        return OpenStack_1_1_FloatingIpAddress(obj['id'], obj['ip'], self,
                                               obj['instance_id'])


class OpenStackFloatingIPPoolsExtensionMixin(object):
    """
    Floating IP pools extension.

    http://docs.openstack.org/api/openstack-compute/2/content/ext-os-floating-ip-pools.html
    """
    def ex_list_floating_ip_pools(self):
        """
        List available floating IP pools

        :rtype: ``list`` of :class:`OpenStack_1_1_FloatingIpPool`
        """
        return self._to_floating_ip_pools(
            self.connection.request('/os-floating-ip-pools').object)

    def _to_floating_ip_pools(self, obj):
        pool_elements = obj['floating_ip_pools']
        return [self._to_floating_ip_pool(pool) for pool in pool_elements]

    def _to_floating_ip_pool(self, obj):
        return OpenStack_1_1_FloatingIpPool(obj['name'], self.connection)
