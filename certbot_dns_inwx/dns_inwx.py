"""DNS Authenticator using INWX XML-RPC DNS API."""
import logging

import zope.interface

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common

from .inwx import domrobot, getOTP, prettyprint

logger = logging.getLogger(__name__)

@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for INWX DNS API
    
    This Authenticator uses the INWX XML-RPC DNS API to fulfill a dns-01 challenge.
    """

    description = ('Obtain certificates using a DNS TXT record (if you are '
                   'using INWX for your domains).')
    ttl = 300
    
    clientCache = {}

    def __init__(self, *args, **kwargs):
        """Initialize an INWX Authenticator"""
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None
        
    @classmethod
    def add_parser_arguments(cls, add):
        super(Authenticator, cls).add_parser_arguments(add, default_propagation_seconds=60)
        add('credentials', help=('Path to INWX account credentials INI file'),
            default='/etc/letsencrypt/inwx.cfg')
    
    def more_info(self):
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the INWX XML-RPC DNS API.'
    
    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'path to INWX XML-RPC account credentials INI file',
            {
                'url': 'URL of the INWX XML-RPC API to use.',
                'username': 'Username of the INWX API account.',
                'password': 'Password of the INWX API account.',
            }
        )
    
    def _perform(self, domain, validation_name, validation):
        self._get_inwx_client().add_txt_record(domain, validation_name, validation, self.ttl)
        
    def _cleanup(self, domain, validation_name, validation):
        self._get_inwx_client().del_txt_record(domain, validation_name, validation)

    def _get_inwx_client(self):
        key = self.conf('credentials')
        if key in Authenticator.clientCache:
            return Authenticator.clientCache[key]
        else:
            client = _INWXClient(self.credentials.conf('url'),
                                 self.credentials.conf('username'),
                                 self.credentials.conf('password'),
                                 self.credentials.conf('shared_secret'))
            # Login was successful if this point is reached
            Authenticator.clientCache[key] = client
            return client

class _INWXClient(object):
    """
    Encapsulates all communication with the INWX XML-RPC API.
    """
    def __init__(self, url, username, password, secret):
        self.inwx = domrobot(url)
        try:
            login = self.inwx.account.login({
                'lang': 'en',
                'user': username,
                'pass': password
            })

            if 'tfa' in login['resData'] and login['resData']['tfa'] == 'GOOGLE-AUTH':
                login = self.inwx.account.unlock({'tan': getOTP(secret)})
        except NameError as err:
            raise errors.PluginError("INWX login failed: {0}".format(err))
    
    def add_txt_record(self, domain_name, record_name, record_content, record_ttl):
        """
        Add a TXT record using the supplied information.
        
        :param str domain_name: The domain to use to find the closest base domain name.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """
        
        domain = self._find_domain(domain_name)
        
        try:
            res = self.inwx.nameserver.createRecord({'domain': domain, 'name': record_name, 'type': 'TXT', 'content': record_content, 'ttl': record_ttl})['resData']
        except:
            raise errors.PluginError('Failed to add TXT DNS record {0} to {1}'.format(record_name, domain))
        
    def del_txt_record(self, domain_name, record_name, record_content):
        """
        Delete a TXT record using the supplied information.
        
        :param str domain_name: The domain to use to find the closest base domain name.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """
        
        domain = self._find_domain(domain_name)
        
        try:
            info = self.inwx.nameserver.info({'domain': domain, 'name': record_name, 'content': record_content})['resData']
            if (not 'record' in info) or 0 == info['count']: raise NameError('Unknown record')
        except NameError as err:
            raise errors.PluginError('No record {0} existing ({1})'.format(record_name, err))
            
        try:
            self.inwx.nameserver.deleteRecord({'id': info['record'][0]['id']})
        except:
            raise errors.PluginError('Failed to delete TXT DNS record {0} of {1}'.format(record_name, domain))
    
    def _find_domain(self, domain_name):
        """
        Find the base domain name for a given domain name.
        
        :param str domain_name: The domain name for which to find the corresponding base domain.
        :returns: The base domain name, if found.
        :rtype: str
        :raises certbot.errors.PluginError: if no matching domain is found.
        """
        
        domain_name_guesses = dns_common.base_domain_name_guesses(domain_name)
        
        for guess in domain_name_guesses:
            logging.debug('Testing {0} for domain {1}...'.format(guess, domain_name))
            try:
                info = self.inwx.domain.info({'domain': guess})['resData']
            except:
                continue
            if not 'status' in info:
                raise errors.PluginError('No status for INWX domain {0}'.format(guess))
            if 'OK' != info['status']:
                raise errors.PluginError('Not OK status for INWX domain {0}'.format(guess))
            return guess
        
        raise errors.PluginError('Unable to determine base domain for {0} using names: {1}.'.format(domain_name, domain_name_guesses))
