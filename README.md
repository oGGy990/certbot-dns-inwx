# certbot-dns-inwx
INWX DNS authenticator plugin for certbot

An authenticator plugin for [certbot](https://certbot.eff.org/) to support [Let's Encrypt](https://letsencrypt.org/) DNS challenges (dns-01) for domains managed by the nameservers of InterNetworX ([INWX](https://www.inwx.com)).

## Requirements
* certbot (>=0.15)

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
 * With certbot-auto (needs to be reinstalled after every certbot-auto update):
   ```
   /root/.local/share/letsencrypt/bin/pip install .
   ```

2. Configure it with your INWX API Login Details:
   ```
   vim /etc/letsencrypt/inwx.cfg
   ```

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
