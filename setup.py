import sys

from setuptools import setup
from setuptools import find_packages

install_requires = [
    'acme',
    'certbot>=0.15',
    'setuptools>=1.0',
    'zope.interface',
]

extras_require = {
    'CNAME': ['dnspython'],
}

data_files = [
	('/etc/letsencrypt', ['inwx.cfg'])
]

setup(
    name='certbot-dns-inwx',
    version='2.1.0',
    description="INWX DNS Authenticator plugin for Certbot",
    url='https://github.com/oGGy990/certbot-dns-inwx',
    author="Oliver Ney",
    author_email='oliver@dryder.de',
    license='Apache License 2.0',
    install_requires=install_requires,
    extras_require=extras_require,
    packages=find_packages(),
    data_files=data_files,
    entry_points={
        'certbot.plugins': [
            'dns-inwx = certbot_dns_inwx.dns_inwx:Authenticator',
        ],
    },
)

