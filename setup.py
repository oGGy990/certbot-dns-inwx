import os

from setuptools import find_packages
from setuptools import setup

version = '3.0.0'
cb_required = '3.0.0'

install_requires = [
    'setuptools>=41.6.0',
    'inwx-domrobot>=3.2.0',
]

if os.environ.get('SNAP_BUILD'):
    install_requires.extend([
        'packaging',
        'dnspython',
    ])
else:
    install_requires.extend([
        f'acme>={cb_required}',
        f'certbot>={cb_required}',
    ])

test_extras = [
    'pytest',
]

extras_require = {
    'CNAME': ['dnspython'],
    'test': test_extras,
}

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='certbot-dns-inwx',
    version=version,
    description="INWX DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/oGGy990/certbot-dns-inwx',
    author="Oliver Ney",
    author_email='oliver@dryder.de',
    license='Apache License 2.0',
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires='>=3.8',
    packages=find_packages(),
    entry_points={
        'certbot.plugins': [
            'dns-inwx = certbot_dns_inwx._internal.dns_inwx:Authenticator',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: System Administrators",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Operating System :: OS Independent",
    ]
)
