# certbot-dns-inwx
INWX DNS authenticator plugin for certbot

An authenticator plugin for [certbot](https://certbot.eff.org/) to support [Let's Encrypt](https://letsencrypt.org/) DNS challenges (dns-01) for domains managed by the nameservers of InterNetworX ([INWX](https://www.inwx.com)).

## Requirements
* certbot (>=0.15)
* setuptools (for manual installation; e.g. `python3-setuptools`)

For older Ubuntu distributions check out this PPA: [ppa:certbot/certbot](https://launchpad.net/~certbot/+archive/ubuntu/certbot)

## Installation
1. First install the plugin:
 * Without dependencies (if using certbot from your distribution repository):
   ```
   python3 setup.py develop --no-deps
   ```
 * With dependencies (not recommended if using certbot from your distribution repositories):
   ```
   python3 setup.py install
   ```
 * Via PIP:
   ```
   pip install certbot-dns-inwx
   ```
 * With certbot-auto (needs to be reinstalled after every certbot-auto update):
   ```
   /opt/eff.org/certbot/venv/bin/pip install .
   ```

2. Configure it with your INWX API Login Details:
   ```
   vim /etc/letsencrypt/inwx.cfg
   ```
   with the following content (also see *inwx.cfg* of the repository):
   ```
   certbot_dns_inwx:dns_inwx_url           = https://api.domrobot.com/xmlrpc/
   certbot_dns_inwx:dns_inwx_username      = your_username
   certbot_dns_inwx:dns_inwx_password      = your_password
   certbot_dns_inwx:dns_inwx_shared_secret = your_shared_secret optional
   ```
   The shared secret is your INWX 2FA OTP code. It is shown to you when setting up the 2FA. It is **not** the 6 digit code you need to enter when siging in. If you are not using 2FA, simply keep the value the way it is.
3. Make sure the file is only readable by root! Otherwise all your domains might be in danger:
   ```
   chmod 0600 /etc/letsencrypt/inwx.cfg
   ```

## Usage
Request new certificates via a certbot invocation like this:

    certbot certonly -a certbot-dns-inwx:dns-inwx -d sub.domain.tld -d *.wildcard.tld

Renewals will automatically be performed using the same authenticator and credentials by certbot.

## Command Line Options
```
 --certbot-dns-inwx:dns-inwx-propagation-seconds CERTBOT_DNS_INWX:DNS_INWX_PROPAGATION_SECONDS
                        The number of seconds to wait for DNS to propagate
                        before asking the ACME server to verify the DNS
                        record. (default: 60)
 --certbot-dns-inwx:dns-inwx-credentials CERTBOT_DNS_INWX:DNS_INWX_CREDENTIALS
                        Path to INWX account credentials INI file (default:
                        /etc/letsencrypt/inwx.cfg)

```

See also `certbot --help certbot-dns-inwx:dns-inwx` for further information.

## CNAME Redirects
This plugin supports redirections on the DNS-01 validation records using CNAME records.

For example, you can have a domain `a.tld` which is not necessarily managed by INWX and possibly may not be automated via certbot. Additionally, you have a domain `b.tld` which is managed by INWX.

An easy solution to automate certificate retrieval for `a.tld` is to add a CNAME record for the name `_acme_challenge.a.tld` to `a.tld` which is pointing to i.e. `_a_validation.b.tld` in your providers web interface.

A command like `certbot -a certbot-dns-inwx:dns-inwx -d a.tld` will then make certbot place its validation token at `_a_validation.b.tld` via INWX and your validation for `a.tld` succeeds.

**NOTE:** This is an optional feature and requires dnspython to be installed. To install it use your distribution repository or i.e. `pip install dnspython`.

## Note
While the plugin itself is licensed according to the Apache License v2.0 the contained INWX DomRobot Client by INWX is licensed according to the MIT License.
