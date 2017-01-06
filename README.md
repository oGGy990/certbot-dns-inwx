# certbot-dns-inwx
INWX DNS authenticator plugin for certbot

An authenticator plugin for [certbot](https://certbot.eff.org/) to support [Let's Encrypt](https://letsencrypt.org/) DNS challenges for domains managed by the nameservers of InterNetworX ([INWX](https://www.inwx.com)).

## Requirements
* certbot (>=0.9)

For older Ubuntu distributions check out this PPA: [ppa:certbot/certbot](https://launchpad.net/~certbot/+archive/ubuntu/certbot)

## Installation
First install the plugin:

    python setup.py

Configure it with your INWX API Login Details:

    vim /etc/letsencrypt/inwx.cfg

Make sure the file is only readable by root! Otherwise all your domains might be in danger.

## Usage
Request new certificates via a certbot invocation like this:

    certbot certonly -a certbot-dns-inwx:dnsinwx -d sub.domain.tld -d otherdomain.tld

Renewals will automatically be performed using the same authenticator by certbot.

Please note that you might need multiple tries in order for a new request to succeed. certbot doesn't have a delay between calling the authenticator and telling Let's Encrypt to authenticate.
The DNS changes may not have propagated until this point. Renewals are automatically repeated if they don't succeed, so there's no issue there.
