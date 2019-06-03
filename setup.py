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

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='certbot-dns-inwx',
    version='2.1.2',
    description="INWX DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: System Administrators",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security :: Cryptography",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Operating System :: OS Independent",
    ]
)

