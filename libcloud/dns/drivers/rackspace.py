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

__all__ = [
    'RackspaceUSDNSDriver',
    'RackspaceUKDNSDriver'
]

import copy

from libcloud.common.base import AsyncConnection
from libcloud.common.types import LibcloudError
from libcloud.utils import merge_valid_keys, get_new_obj
from libcloud.common.rackspace import AUTH_URL_US, AUTH_URL_UK
from libcloud.compute.drivers.openstack import OpenStack_1_1_Connection
from libcloud.compute.drivers.openstack import OpenStack_1_1_Response

from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record

VALID_ZONE_EXTRA_PARAMS = ['email', 'comment', 'ns1']
VALID_RECORD_EXTRA_PARAMS = ['ttl', 'comment']

RECORD_TYPE_MAP = {
    RecordType.A: 'A',
    RecordType.AAAA: 'AAAA',
    RecordType.CNAME: 'CNAME',
    RecordType.MX: 'MX',
    RecordType.NS: 'NS',
    RecordType.TXT: 'TXT',
    RecordType.SRV: 'SRV',
}


class RackspaceDNSResponse(OpenStack_1_1_Response):
    """
    Rackspace DNS Response class.
    """

    def parse_error(self):
        # Holy fucking jesus,
        # "The request could not be understood by the server due to malformed
        # syntax." is returned if record already exists
        status = int(self.status)
        context = self.connection.context
        body = self.parse_body()

        if status == 404:
            if context['resource'] == 'zone':
                raise ZoneDoesNotExistError(value='', driver=self,
                                            zone_id=context['id'])
            elif context['resource'] == 'record':
                raise RecordDoesNotExistError(value='', driver=self,
                                              record_id=context['id'])

        if 'code' and 'message' in body:
            err = '%s - %s (%s)' % (body['code'], body['message'],
                                    body['details'])
        elif 'validationErrors' in body:
            errors = [m for m in body['validationErrors']['messages']]
            err = 'Validation errors: %s' % ', '.join(errors)

        return err


class RackspaceDNSConnection(OpenStack_1_1_Connection, AsyncConnection):
    """
    Rackspace DNS Connection class.
    """

    responseCls = RackspaceDNSResponse
    _url_key = 'dns_url'
    XML_NAMESPACE = None

    def get_poll_request_kwargs(self, response, context):
        job_id = response.object['jobId']
        kwargs = {'action': '/status/%s' % (job_id),
                'params': {'showDetails': True}}
        return kwargs

    def has_completed(self, response):
        status = response.object['status']
        if status == 'ERROR':
            raise LibcloudError(response.object['error']['message'],
                                driver=self.driver)

        return status == 'COMPLETED'


class RackspaceUSDNSConnection(RackspaceDNSConnection):
    auth_url = AUTH_URL_US


class RackspaceUKDNSConnection(RackspaceDNSConnection):
    auth_url = AUTH_URL_UK


class RackspaceDNSDriver(DNSDriver):
    def list_zones(self):
        response = self.connection.request(action='/domains')
        zones = self._to_zones(data=response.object['domains'])
        return zones

    def list_records(self, zone):
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        response = self.connection.request(action='/domains/%s' % (zone.id),
                                           params={'showRecord': True}).object
        records = self._to_records(data=response['recordsList']['records'],
                                   zone=zone)
        return records

    def get_zone(self, zone_id):
        self.connection.set_context({'resource': 'zone', 'id': zone_id})
        response = self.connection.request(action='/domains/%s' % (zone_id))
        zone = self._to_zone(data=response.object)
        return zone

    def get_record(self, zone_id, record_id):
        zone = self.get_zone(zone_id=zone_id)
        self.connection.set_context({'resource': 'record', 'id': record_id})
        response = self.connection.request(action='/domains/%s/records/%s' %
                                           (zone_id, record_id)).object
        record = self._to_record(data=response, zone=zone)
        return record

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        extra = extra if extra else {}

        # Email address is required
        if not 'email' in extra:
            raise ValueError('"email" key must be present in extra dictionary')

        payload = {'name': domain, 'emailAddress': extra['email'],
                   'recordsList': {'records': []}}

        if ttl:
            payload['ttl'] = ttl

        if 'comment' in extra:
            payload['comment'] = extra['comment']

        data = {'domains': [payload]}
        response = self.connection.async_request(action='/domains',
                                                 method='POST', data=data)
        zone = self._to_zone(data=response.object['response']['domains'][0])
        return zone

    def update_zone(self, zone, domain=None, type=None, ttl=None, extra=None):
        # Only ttl, comment and email address can be changed
        extra = extra if extra else {}

        if domain:
            raise LibcloudError('Domain cannot be changed', driver=self)

        data = {}

        if ttl:
            data['ttl'] = int(ttl)

        if 'email' in extra:
            data['emailAddress'] = extra['email']

        if 'comment' in extra:
            data['comment'] = extra['comment']

        type = type if type else zone.type
        ttl = ttl if ttl else zone.ttl

        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        self.connection.async_request(action='/domains/%s' % (zone.id),
                                      method='PUT', data=data)
        merged = merge_valid_keys(params=copy.deepcopy(zone.extra),
                                  valid_keys=VALID_ZONE_EXTRA_PARAMS,
                                  extra=extra)
        updated_zone = get_new_obj(obj=zone, klass=Zone,
                                   attributes={'type': type,
                                               'ttl': ttl,
                                               'extra': merged})
        return updated_zone

    def create_record(self, name, zone, type, data, extra=None):
        # Name must be a FQDN - e.g. if domain is "foo.com" then a record
        # name is "bar.foo.com"
        data = {'name': name, 'type': RECORD_TYPE_MAP[type], 'data': data}

        if 'ttl' in extra:
            data['ttl'] = int(extra['ttl'])

        payload = {'records': [data]}
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        response = self.connection.async_request(action='/domains/%s/records'
                                                 % (zone.id), data=payload,
                                                 method='POST').object
        record = self._to_record(data=response['response']['records'][0],
                                 zone=zone)
        return record

    def update_record(self, record, name=None, type=None, data=None,
                      extra=None):
        # Only data, ttl, and comment attributes can be modified, but name
        # attribute must always be present.
        extra = extra if extra else {}

        payload = {'name': record.name}

        if data:
            payload['data'] = data

        if 'ttl' in extra:
            payload['ttl'] = extra['ttl']

        if 'comment' in extra:
            payload['comment'] = extra['comment']

        type = type if type else record.type
        data = data if data else record.data

        self.connection.set_context({'resource': 'record', 'id': record.id})
        self.connection.async_request(action='/domains/%s/records/%s' %
                                      (record.zone.id, record.id),
                                      method='PUT', data=payload)

        merged = merge_valid_keys(params=copy.deepcopy(record.extra),
                                  valid_keys=VALID_RECORD_EXTRA_PARAMS,
                                  extra=extra)
        updated_record = get_new_obj(obj=record, klass=Record,
                                     attributes={'type': type,
                                                 'data': data,
                                                 'extra': merged})
        return updated_record

    def delete_zone(self, zone):
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        self.connection.async_request(action='/domains/%s' % (zone.id),
                                      method='DELETE')
        return True

    def delete_record(self, record):
        self.connection.set_context({'resource': 'record', 'id': record.id})
        self.connection.async_request(action='/domains/%s/records/%s' %
                                      (record.zone.id, record.id),
                                      method='DELETE')
        return True

    def _to_zones(self, data):
        zones = []
        for item in data:
            zone = self._to_zone(data=item)
            zones.append(zone)

        return zones

    def _to_zone(self, data):
        id = data['id']
        domain = data['name']
        type = 'master'
        ttl = data.get('ttl', 0)
        extra = {}

        if 'emailAddress' in data:
            extra['email'] = data['emailAddress']

        if 'comment' in data:
            extra['comment'] = data['comment']

        zone = Zone(id=str(id), domain=domain, type=type, ttl=int(ttl),
                    driver=self, extra=extra)
        return zone

    def _to_records(self, data, zone):
        records = []
        for item in data:
            record = self._to_record(data=item, zone=zone)
            records.append(record)

        return records

    def _to_record(self, data, zone):
        id = data['id']
        name = data['name']
        type = self._string_to_record_type(data['type'])
        record_data = data['data']
        extra = {}

        if 'ttl' in data:
            extra['ttl'] = data['ttl']

        record = Record(id=str(id), name=name, type=type, data=record_data,
                        zone=zone, driver=self, extra=extra)
        return record


class RackspaceUSDNSDriver(RackspaceDNSDriver):
    name = 'Rackspace DNS (US)'
    type = Provider.RACKSPACE_US
    connectionCls = RackspaceUSDNSConnection


class RackspaceUKDNSDriver(RackspaceDNSDriver):
    name = 'Rackspace DNS (UK)'
    type = Provider.RACKSPACE_UK
    connectionCls = RackspaceUKDNSConnection
