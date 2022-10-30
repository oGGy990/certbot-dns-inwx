import os
import sys

from setuptools import setup
from setuptools import find_packages

version = '2.2.0'
cb_required = '0.15'

install_requires = [
    'setuptools>=39.0.1',
]

extras_require = {
    'CNAME': ['dnspython'],
}

if not os.environ.get('SNAP_BUILD'):
    install_requires.extend([
        'acme>=0.31.0',
        f'certbot>={cb_required}',
    ])
# Snap Core20 Python Plugin is using 'pip install -U .' to build the package.
# PEP 517 builds do not fall back to 'setup.py install' - which is deprecated -
# as pip does for non-PEP 517 builds.
# The following error which was taken from the original certbot dns plugins thus
# always leads to a failed snap build. It is merely a sanity check to ensure
# SNAP_BUILD is not set if actually building a Python wheel for e.g. PyPi and
# not really required. It is kept for completeness and as a reminder to check
# for what kind of replacement the certbot community comes up with.
# 
# elif 'bdist_wheel' in sys.argv[1:]:
#    raise RuntimeError('Unset SNAP_BUILD when building wheels '
#                        'to include certbot dependencies.')
if os.environ.get('SNAP_BUILD'):
    install_requires.append('packaging')

if sys.platform.startswith('freebsd'):
    data_files = [
    	('/usr/local/etc/letsencrypt', ['inwx.cfg'])
    ]
else:
    data_files = [
    	('/etc/letsencrypt', ['inwx.cfg'])
    ]


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

