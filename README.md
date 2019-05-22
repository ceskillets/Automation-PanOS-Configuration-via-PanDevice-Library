# PanDevice Example Skillet

This skillet is a longer example of how to configure a firewall using the Palo Alto Networks
[PanDevice](https://pandevice.readthedocs.io/en/latest/) library.

It configures the following on a PAN-OS firewall:

- Interfaces
- Zones
- Default Router
- Address Objects
- Service Objects
- Security Rules
- NAT Rules

It assumes the initial configuration of the firewall is empty.

## Script Walkthrough

### Connecting to a Firewall

Connecting to a firewall can be done with the
[`create_from_device()`](https://pandevice.readthedocs.io/en/latest/module-policies.html#pandevice.policies.PostRulebase)
method.  It returns a [`pandevice.firewall.Firewall`](https://pandevice.readthedocs.io/en/latest/module-firewall.html#pandevice.firewall.Firewall)
or [`pandevice.panorama.Panorama`](https://pandevice.readthedocs.io/en/latest/module-panorama.html#pandevice.panorama.Panorama)
object as appropriate:

```
device = PanDevice.create_from_device(hostname, api_username=username, api_password=password)
```

### Creating Objects

Creating configuration elements with PanDevice follows the following pattern:

```
web_srv = AddressObject(name='web-srv', value='192.168.45.5')
device.add(web_srv)
web_srv.create()
```

1. Create the object with the desired attributes.
2. Add the object you're creating to its parent by calling its `add()` method.  This could be a
   [`pandevice.firewall.Firewall`](https://pandevice.readthedocs.io/en/latest/module-firewall.html#pandevice.firewall.Firewall)
   object in a lot of cases, but could be a
   [`pandevice.panorama.DeviceGroup`](https://pandevice.readthedocs.io/en/latest/module-panorama.html#pandevice.panorama.DeviceGroup)
   or a [`pandevice.panorama.Template`](https://pandevice.readthedocs.io/en/latest/module-panorama.html#pandevice.panorama.Template)
   object if you're working with Panorama.  This places the object you created in the appropriate spot in the XML configuration.
3. Create the object using its `create()` method.  This actually modifies the candidate configuration.

### Creating Rules

Creating rules is similar to creating objects, except the parent object is different:

```
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

rulebase.add(allow_ping)
allow_ping.create()
```

1. Create a [`pandevice.policies.Rulebase`](https://pandevice.readthedocs.io/en/latest/module-policies.html#pandevice.policies.Rulebase)
   object if you're working with a firewall, or a
   [`pandevice.policies.PreRulebase`](https://pandevice.readthedocs.io/en/latest/module-policies.html#pandevice.policies.PreRulebase)
   or [`pandevice.policies.PostRulebase`](https://pandevice.readthedocs.io/en/latest/module-policies.html#pandevice.policies.PostRulebase)
   if you're working with Panorama.
2. Add the rulebase to its parent object.
3. Create the rule with the desired attributes.
4. Add the rule to its parent object, the rulebase you're working with.
5. Create the rule using its `create()` method.

### Committing Configuration

Committing configuration to the firewall or Panorama is done with the 
[`commit()`](https://pandevice.readthedocs.io/en/latest/module-base.html#pandevice.base.PanDevice.commit) method.

```
device.commit()
```

Panorama can also use the [`commit_all()`](https://pandevice.readthedocs.io/en/latest/module-panorama.html#pandevice.panorama.Panorama.commit_all)
method to commit to Panorama and firewalls at the same time.

## Support Policy

The code and templates in the repo are released under an as-is, best effort,
support policy. These scripts should be seen as community supported and
Palo Alto Networks will contribute our expertise as and when possible.
We do not provide technical support or help in using or troubleshooting the
components of the project through our normal support options such as
Palo Alto Networks support teams, or ASC (Authorized Support Centers)
partners and backline support options. The underlying product used
(the VM-Series firewall) by the scripts or templates are still supported,
but the support is only for the product functionality and not for help in
deploying or using the template or script itself. Unless explicitly tagged,
all projects or work posted in our GitHub repository
(at https://github.com/PaloAltoNetworks) or sites other than our official
Downloads page on https://support.paloaltonetworks.com are provided under
the best effort policy.