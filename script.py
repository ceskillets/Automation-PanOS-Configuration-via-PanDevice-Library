# Copyright 2019 Palo Alto Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import click

from pandevice.base import PanDevice
from pandevice.errors import PanDeviceError
from pandevice.network import EthernetInterface, StaticRoute, VirtualRouter, Zone
from pandevice.objects import AddressObject, ServiceObject
from pandevice.policies import NatRule, Rulebase, SecurityRule


def configure_network(device):
    eth1 = EthernetInterface(name='ethernet1/1', mode='layer3', ip=('192.168.55.20/24',))
    eth2 = EthernetInterface(name='ethernet1/2', mode='layer3', ip=('192.168.45.20/24',))
    eth3 = EthernetInterface(name='ethernet1/3', mode='layer3', ip=('192.168.35.20/24',))

    device.add(eth1)
    device.add(eth2)
    device.add(eth3)

    eth1.create()
    eth2.create()
    eth3.create()

    untrust = Zone(name='untrust', mode='layer3', interface=['ethernet1/1'])
    web = Zone(name='web', mode='layer3', interface=['ethernet1/2'])
    db = Zone(name='db', mode='layer3', interface=['ethernet1/3'])

    device.add(untrust)
    device.add(web)
    device.add(db)

    untrust.create()
    web.create()
    db.create()

    vr_default = VirtualRouter(name='default', interface=['ethernet1/1', 'ethernet1/2', 'ethernet1/3'])
    device.add(vr_default)
    vr_default.create()

    default_route = StaticRoute(name='default', destination='0.0.0.0/0', nexthop='192.168.55.2')
    vr_default.add(default_route)
    default_route.create()


def configure_policy(device):
    web_srv = AddressObject(name='web-srv', value='192.168.45.5')
    db_srv = AddressObject(name='db-srv', value='192.168.35.5')

    device.add(web_srv)
    device.add(db_srv)

    web_srv.create()
    db_srv.create()

    service_tcp_221 = ServiceObject(name='service-tcp-221', protocol='tcp', destination_port='221')
    service_tcp_222 = ServiceObject(name='service-tcp-222', protocol='tcp', destination_port='222')

    device.add(service_tcp_221)
    device.add(service_tcp_222)

    service_tcp_221.create()
    service_tcp_222.create()

    rulebase = Rulebase()
    device.add(rulebase)

    allow_ping = SecurityRule(
        name='Allow ping',
        fromzone=['any'],
        source=['any'],
        tozone=['any'],
        destination=['any'],
        application=['ping'],
        service=['application-default'],
        action='allow'
    )
    ssh_inbound = SecurityRule(
        name='SSH inbound',
        fromzone=['untrust'],
        source=['any'],
        tozone=['web', 'db'],
        destination=['any'],
        application=['ping', 'ssh'],
        service=['service-tcp-221', 'service-tcp-222'],
        action='allow'
    )
    web_inbound = SecurityRule(
        name='Web inbound',
        fromzone=['untrust'],
        source=['any'],
        tozone=['web'],
        destination=['any'],
        application=['any'],
        service=['service-http'],
        action='allow'
    )
    web_to_db = SecurityRule(
        name='Web to DB',
        fromzone=['any'],
        source=['web-srv'],
        tozone=['any'],
        destination=['db-srv'],
        application=['mysql'],
        service=['application-default'],
        action='allow'
    )
    allow_outbound = SecurityRule(
        name='Allow outbound',
        fromzone=['web', 'db'],
        source=['any'],
        tozone=['untrust'],
        destination=['any'],
        application=['any'],
        service=['application-default'],
        action='allow'
    )

    rulebase.add(allow_ping)
    rulebase.add(ssh_inbound)
    rulebase.add(web_inbound)
    rulebase.add(web_to_db)
    rulebase.add(allow_outbound)

    allow_ping.create()
    ssh_inbound.create()
    web_inbound.create()
    web_to_db.create()
    allow_outbound.create()

    web_ssh = NatRule(
        name='Web SSH',
        fromzone=['untrust'],
        source=['any'],
        tozone=['untrust'],
        destination=['192.168.55.20'],
        service='service-tcp-221',
        source_translation_type='dynamic-ip-and-port',
        source_translation_address_type='interface-address',
        source_translation_interface='ethernet1/2',
        destination_translated_address='web-srv',
        destination_translated_port='22'
    )
    db_ssh = NatRule(
        name='DB SSH',
        fromzone=['untrust'],
        source=['any'],
        tozone=['untrust'],
        destination=['192.168.55.20'],
        service='service-tcp-222',
        source_translation_type='dynamic-ip-and-port',
        source_translation_address_type='interface-address',
        source_translation_interface='ethernet1/3',
        destination_translated_address='db-srv',
        destination_translated_port='22'
    )
    wordpress_nat = NatRule(
        name='WordPress NAT',
        fromzone=['untrust'],
        source=['any'],
        tozone=['untrust'],
        destination=['192.168.55.20'],
        service='service-http',
        source_translation_type='dynamic-ip-and-port',
        source_translation_address_type='interface-address',
        source_translation_interface='ethernet1/2',
        destination_translated_address='web-srv'
    )
    outgoing_traffic = NatRule(
        name='Outgoing traffic',
        fromzone=['web', 'db'],
        source=['any'],
        tozone=['untrust'],
        destination=['any'],
        source_translation_type='dynamic-ip-and-port',
        source_translation_address_type='interface-address',
        source_translation_interface='ethernet1/1',
    )

    rulebase.add(web_ssh)
    rulebase.add(db_ssh)
    rulebase.add(wordpress_nat)
    rulebase.add(outgoing_traffic)

    web_ssh.create()
    db_ssh.create()
    wordpress_nat.create()
    outgoing_traffic.create()


@click.command()
@click.option(
    "--hostname", envvar="PANOS_HOSTNAME", required=True,
    help="PAN-OS device to connect to (or PANOS_HOSTNAME envvar)."
)
@click.option(
    "--username", envvar="PANOS_USERNAME", required=True,
    help="Username for PAN-OS device (or PANOS_USERNAME envvar)."
)
@click.option(
    "--password", envvar="PANOS_PASSWORD", required=True,
    help="Password for PAN-OS device (or PANOS_PASSWORD envvar)."
)
def cli(hostname, username, password):
    """ PanDevice demo script. """
    try:
        device = PanDevice.create_from_device(hostname, api_username=username, api_password=password)

        configure_network(device)
        configure_policy(device)

        device.commit(sync=True)

    except PanDeviceError as e:
        click.echo('PanDeviceError: {}'.format(e))


if __name__ == '__main__':
    cli()
