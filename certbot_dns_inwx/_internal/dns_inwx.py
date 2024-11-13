"""DNS Authenticator using INWX XML-RPC DNS API."""
import logging
import os.path
import sys
from typing import Callable

from INWX.Domrobot import ApiClient
from certbot import errors
from certbot.compat import misc
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for INWX DNS API
    
    This Authenticator uses the INWX XML-RPC DNS API to fulfill a dns-01 challenge.
    """

    description = ('Obtain certificates using a DNS TXT record (if you are '
                   'using INWX for your domains).')
    ttl = 300

    clientCache = {}
    nameCache = {}

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None], default_propagation_seconds: int = 60) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        if sys.platform.startswith('freebsd'):
            cfg_default = os.path.join('/usr/local', misc.get_default_folder('config'), 'inwx.cfg')
        else:
            cfg_default = os.path.join(misc.get_default_folder('config'), 'inwx.cfg')
        add('credentials', help='Path to INWX account credentials INI file.',
            default=cfg_default)

        try:
            import dns.resolver
            add('follow-cnames',
                type=bool,
                help='Shall the plugin follow CNAME redirects on validation records?',
                default=True)
        except ImportError:
            pass

    def more_info(self) -> str:
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
            'the INWX XML-RPC DNS API.'

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            'credentials',
            'path to INWX XML-RPC account credentials INI file',
            {
                'url': 'URL of the INWX XML-RPC API to use.',
                'username': 'Username of the INWX API account.',
                'password': 'Password of the INWX API account.',
                'shared_secret': 'Optional shared secret code for the two-factor ' + \
                                 'authentication assigned to the INWX API account.'
            }
        )

    def _follow_cnames(self, domain: str, validation_name: str) -> str:
        """
        Performs recursive CNAME lookups in case there exists a CNAME for the given
        validation name.
        If the optional dependency dnspython is not installed, the given name is
        simply returned.
        """
        try:
            import dns.exception
            import dns.resolver
            import dns.name

            if not self.conf('follow-cnames'):
                return validation_name
        except ImportError:
            return validation_name

        resolver = dns.resolver.Resolver()
        name = dns.name.from_text(validation_name)
        for _ in range(10):
            try:
                answer = resolver.resolve(name, dns.rdatatype.CNAME)
                if 1 <= len(answer):
                    name = answer[0].target
                else:
                    break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                break
            except (dns.exception.Timeout, dns.resolver.YXDOMAIN, dns.resolver.NoNameservers):
                raise errors.PluginError(f'Failed to lookup CNAME\'s on your requested domain {domain}')
        return name.to_text(True)

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        if validation_name in Authenticator.nameCache:
            resolved = Authenticator.nameCache[validation_name]
        else:
            resolved = self._follow_cnames(domain, validation_name)
            Authenticator.nameCache[validation_name] = resolved

        if resolved != validation_name:
            logger.info('Validation record for %s redirected by CNAME(s) to %s', domain, resolved)
        self._get_inwx_client().add_txt_record(domain, resolved, validation, self.ttl)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        resolved = Authenticator.nameCache[validation_name]
        self._get_inwx_client().del_txt_record(domain, resolved, validation)

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


class _INWXClient:
    """
    Encapsulates all communication with the INWX XML-RPC API.
    """

    def __init__(self, url: str, username: str, password: str, secret: str) -> None:
        # Ensure compatibility with configurations for the old API interface
        if url.endswith('/'):
            url = url[:-1]
        if url.endswith('xmlrpc'):
            url = url[:-6]
        self.inwx = ApiClient(url)
        self.recordCache = {}
        try:
            login_result = self.inwx.login(username, password, secret)
        except Exception as err:
            raise errors.PluginError(f'INWX login failed: {err}')
        if login_result['code'] != 1000:
            raise errors.PluginError(f'INWX login failed: {login_result['msg']}')

    def add_txt_record(self, source: str, record_name: str, record_content: str, record_ttl: int):
        """
        Add a TXT record using the supplied information.
        
        :param str source: The original domain (before CNAME lookup) this request is done for.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """

        try:
            domain = self._find_domain(record_name)

            self._call_api('nameserver.createRecord',
                           {'domain': domain, 'name': record_name, 'type': 'TXT', 'content': record_content,
                            'ttl': record_ttl})
        except Exception as err:
            raise errors.PluginError(
                f'Failed to add TXT DNS record {record_name} for {source}: {err}')

    def del_txt_record(self, source: str, record_name: str, record_content: str):
        """
        Delete a TXT record using the supplied information.
        
        :param str source: The original domain (before CNAME lookup) this request is done for.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """

        try:
            domain = self._find_domain(record_name)

            info = self._call_api('nameserver.info',
                                  {'domain': domain, 'name': record_name, 'content': record_content})
            if (not 'record' in info) or 0 == info['count']:
                raise Exception(f'record has been removed/altered')

            self._call_api('nameserver.deleteRecord', {'id': info['record'][0]['id']})
        except Exception as err:
            raise errors.PluginError(
                f'Failed to delete TXT DNS record {record_name} for {source}: {err}')

    def _call_api(self, api_method: str, method_params: dict = None) -> dict:
        try:
            result = self.inwx.call_api(api_method, method_params)
            if result['code'] == 2201:
                raise Exception(
                    f'insufficient authorization. Have you added the \'DNS management\' role to your API account?')
            elif result['code'] != 1000:
                raise Exception(f'{result['msg']} ({result['code']})')
            elif 'resData' in result:
                return result['resData']
            else:
                return {}
        except Exception as err:
            raise Exception(f'INWX API request failed: {err}')

    def _find_domain(self, record_name: str):
        """
        Find the base domain name for a given domain name.
        
        :param str record_name: The domain record name for which to find the corresponding base domain.
        :returns: The base domain name, if found.
        :rtype: str
        :raises certbot.errors.PluginError: if no matching domain is found.
        """

        if record_name in self.recordCache:
            return self.recordCache[record_name]

        # Get list of domain name candidates (stripping the TLD as those cannot be registered with INWX)
        domain_name_guesses = dns_common.base_domain_name_guesses(record_name)[:-1]

        # Iterate in reverse order so we begin with the most probable match
        for guess in reversed(domain_name_guesses):
            logging.debug(f'Testing {guess} for domain {record_name}...')
            try:
                info = self._call_api('nameserver.list', {'domain': guess})
            except:
                continue
            if info['count'] > 0:
                for domain in info['domains']:
                    # Only consider an exact match and domains for which the INWX nameservers are the master
                    if domain['domain'] == guess and domain['type'] == 'MASTER':
                        self.recordCache[record_name] = guess
                        return guess

        raise errors.PluginError(
            f'Unable to determine base domain for {record_name} using names: {domain_name_guesses}')
