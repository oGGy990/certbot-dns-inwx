from setuptools import setup
from setuptools import find_packages
import sys

install_requires = [
    'acme',
    'certbot',
    'zope.interface',
]

#if sys.version_info.major == 3:
#    install_requires.extend([
#        'xmlrpc',
#    ])
#else:
#    install_requires.extend([
#        'xmlrpclib',
#    ])

setup(
    name='certbot-dns-inwx',
    description="INWX DNS authenticator plugin for certbot",
    url='http://www.dryder.de',
    author="Oliver Ney",
    author_email='oliver@dryder.de',
    license='Apache License 2.0',
    install_requires=install_requires,
    packages=find_packages(),
    entry_points={
        'certbot.plugins': [
            'dnsinwx = certbot_inwx.inwxauth:InwxDnsAuth',
        ],
    },
)

