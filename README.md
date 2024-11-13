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
 * Via pip:
   ```
   pip install certbot-dns-inwx
   ```

2. Configure it with your INWX API Login Details:
   ```
   vim /etc/letsencrypt/inwx.cfg
   ```
   with the following content (also see *inwx.cfg* of the repository):
   ```
   dns_inwx_url           = https://api.domrobot.com
   dns_inwx_username      = your_username
   dns_inwx_password      = """your_password"""
   dns_inwx_shared_secret = your_shared_secret optional
   ```
   It is recommended to create a subaccount in the INWX interface and restrict this account to the 'DNS management' role.
   This prevents the possible loss of your domains in case your account credentials are stolen.

   The shared secret is your INWX 2FA OTP key. It is shown to you when setting up the 2FA. It is **not** the 6 digit code you need to enter when siging in. If you are not using 2FA, simply keep the value the way it is.
   For general syntax requirements of this file, see [here](https://configobj.readthedocs.io/en/latest/configobj.html#the-config-file-format).

3. Make sure the file is only readable by root! Otherwise, all your domains might be in danger:
   ```
   chmod 0600 /etc/letsencrypt/inwx.cfg
   ```

## Usage
Request new certificates via a certbot invocation like this:

    certbot certonly -a dns-inwx -d sub.domain.tld -d *.wildcard.tld

Renewals will automatically be performed using the same authenticator and credentials by certbot.

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
                        Shall the plugin follow CNAME redirects on validation
                        records? (default: True)
                        This command line option is only exposed if 
                        dnspython is installed.

```

See also `certbot --help dns-inwx` for further information.

## CNAME Redirects
This plugin supports redirections on the DNS-01 validation records using CNAME records.

For example, you can have a domain `a.tld` which is not necessarily managed by INWX and possibly may not be automated via certbot. Additionally, you have a domain `b.tld` which is managed by INWX.

An easy solution to automate certificate retrieval for `a.tld` is to add a CNAME record for the name `_acme-challenge.a.tld` to `a.tld` which is pointing to i.e. `_a_validation.b.tld` in your providers web interface.

A command like `certbot -a dns-inwx -d a.tld` will then make certbot place its validation token at `_a_validation.b.tld` via INWX and your validation for `a.tld` succeeds.

**NOTE:** This is an optional feature and requires dnspython to be installed.
To install it use your distribution repository or i.e. `pip install dnspython`.
The snap package already ships with it.
