# certbot-dns-inwx
INWX DNS authenticator plugin for certbot

An authenticator plugin for [certbot](https://certbot.eff.org/) to support [Let's Encrypt](https://letsencrypt.org/) DNS challenges (dns-01) for domains managed by the nameservers of InterNetworX ([INWX](https://www.inwx.com)).

## Requirements
* certbot (>=3.0.0)
* setuptools (for manual installation; e.g. `python3-setuptools`)

For older Ubuntu distributions check out this PPA: [ppa:certbot/certbot](https://launchpad.net/~certbot/+archive/ubuntu/certbot)

## Installation
1. First install the plugin:
 * Via Snap (requires certbot to be installed via snap):
   ```
   snap install certbot-dns-inwx
   snap set certbot trust-plugin-with-root=ok
   snap connect certbot:plugin certbot-dns-inwx
   snap connect certbot-dns-inwx:certbot-metadata certbot:certbot-metadata
   ```
 * Via PIP:
   ```
   pip install certbot-dns-inwx
   ```
 * Without dependencies (if using certbot from your distribution repository):
   ```
   python3 setup.py develop --no-deps
   ```
 * With dependencies (not recommended if using certbot from your distribution repositories):
   ```
   python3 setup.py install
   ```
 * With certbot-auto (deprecated for most platforms, needs to be reinstalled after every certbot-auto update):
   ```
   /opt/eff.org/certbot/venv/bin/pip install .
   ```

2. Configure it with your INWX API Login Details:
   ```
   vim /etc/letsencrypt/inwx.cfg
   ```
   with the following content (also see *inwx.cfg* of the repository):
   ```
   dns_inwx_url           = https://api.domrobot.com/xmlrpc/
   dns_inwx_username      = your_username
   dns_inwx_password      = """your_password"""
   dns_inwx_shared_secret = your_shared_secret optional
   ```
   The shared secret is your INWX 2FA OTP key. It is shown to you when setting up the 2FA. It is **not** the 6 digit code you need to enter when siging in. If you are not using 2FA, simply keep the value the way it is.
   For general syntax requirements of this file, see [here](https://configobj.readthedocs.io/en/latest/configobj.html#the-config-file-format).

   Also note [these remarks](#usage-on-certbot--v170) if you are using an older version of certbot.
3. Make sure the file is only readable by root! Otherwise all your domains might be in danger:
   ```
   chmod 0600 /etc/letsencrypt/inwx.cfg
   ```

## Usage
Request new certificates via a certbot invocation like this:

    certbot certonly -a dns-inwx -d sub.domain.tld -d *.wildcard.tld

Renewals will automatically be performed using the same authenticator and credentials by certbot.

## Usage on certbot < v1.7.0
Before certbot v1.7.0, third plugins needed to be accessed using their plugin name as prefix. If you are still using an older version of certbot, ensure to prefix all options in *inwx.cfg* and on the command-line with `certbot-dns-inwx:`, e.g.:

    certbot certonly -a certbot-dns-inwx:dns-inwx --certbot-dns-inwx:dns-inwx-credentials /root/inwx.cfg -d sub.domain.tld

## Command Line Options
```
 --dns-inwx-propagation-seconds DNS_INWX_PROPAGATION_SECONDS
                        The number of seconds to wait for DNS to propagate
                        before asking the ACME server to verify the DNS
                        record. (default: 60)
 --dns-inwx-credentials DNS_INWX_CREDENTIALS
                        Path to INWX account credentials INI file (default:
                        /etc/letsencrypt/inwx.cfg)
 --dns-inwx-follow-cnames DNS_INWX_FOLLOW_CNAMES
                        If 'true', the plugin will follow CNAME redirects 
                        on validation records (default: true)
                        This command line option is only exposed, if 
                        dnspython is installed.

```

See also `certbot --help dns-inwx` for further information.

## CNAME Redirects
This plugin supports redirections on the DNS-01 validation records using CNAME records.

For example, you can have a domain `a.tld` which is not necessarily managed by INWX and possibly may not be automated via certbot. Additionally, you have a domain `b.tld` which is managed by INWX.

An easy solution to automate certificate retrieval for `a.tld` is to add a CNAME record for the name `_acme-challenge.a.tld` to `a.tld` which is pointing to i.e. `_a_validation.b.tld` in your providers web interface.

A command like `certbot -a dns-inwx -d a.tld` will then make certbot place its validation token at `_a_validation.b.tld` via INWX and your validation for `a.tld` succeeds.

**NOTE:** This is an optional feature and requires dnspython to be installed. To install it use your distribution repository or i.e. `pip install dnspython`.

## Note
While the plugin itself is licensed according to the Apache License v2.0 the contained INWX DomRobot Client by INWX is licensed according to the MIT License.
