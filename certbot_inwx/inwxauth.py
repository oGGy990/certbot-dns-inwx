"""INWX DNS Authentication"""
import logging

import zope.interface

import sys
import time

if sys.version_info.major == 3:
    import configparser
else:
    import ConfigParser as configparser

from acme import challenges

from certbot import errors
from certbot import interfaces

from certbot.plugins import common

from inwx import domrobot, getOTP, prettyprint

logger = logging.getLogger(__name__)

@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class InwxDnsAuth(common.Plugin):
    """INWX DNS Authenticator"""

    description = "Authentication via INWX's XML-RPC API"

    @classmethod
    def add_parser_arguments(cls, add):
        add("cfgfile", default="/etc/letsencrypt/inwx.cfg",
            help="INWX API Configuration")

    def __init__(self, *args, **kwargs):
        """Initialize an INWX Authenticator"""
        super(InwxDnsAuth, self).__init__(*args, **kwargs)
        
        self.nsIds = {}

    def prepare(self):
        """Prepare the authenticator"""
        config = configparser.SafeConfigParser()
        try:
            if config.read(self.conf("cfgfile")) == []:
                raise Exception("Config empty")
        except Exception as err:
            raise errors.MisconfigurationError("Invalid INWX API configuration: {0}".format(err))

        self.inwx = domrobot(config.get('inwx', 'url'))
        try:
            login = self.inwx.account.login({'lang':'en', 'user': config.get('inwx', 'username'), 'pass': config.get('inwx', 'password')})

            if 'tfa' in login['resData'] and login['resData']['tfa'] == 'GOOGLE-AUTH':
                login = self.inwx.account.unlock({'tan': getOTP(config.get('inwx', 'shared_secret'))})
        except NameError as err:
            raise errors.MisconfigurationError("INWX login failed: {0}".format(err))

    def get_chall_pref(self, domain):
        """Return list of challenge preferences.

        :param str domain: Domain for which challenge preferences are sought.
        
        :returns: List of challenge types (subclasses of
            :class:`acme.challenges.Challenge`) with the most
            preferred challenges first. If a type is not specified, it means the
            Authenticator cannot perform the challenge.
        :rtype: list
        
        """
        return [challenges.DNS01]

    def get_inwx_domain(self, domain):
        """Search the registered INWX domains for the parent domain"""
        parts = domain.split(".")
        result = False
        for i in range(2, len(parts) + 1):
            parent = ".".join(parts[len(parts)-i:len(parts)])
            logging.debug("Testing {0} for domain {1}...".format(parent, domain))
            try:
                info = self.inwx.domain.info({'domain': parent})['resData']
            except:
                continue
            if not 'status' in info:
                logging.warning("No status for INWX domain {0}".format(domain))
                return None
            if 'OK' != info['status']:
                logging.warning("Not OK status for INWX domain {0}".format(domain))
                return None
            return parent
        return None

    def create_or_update_record(self, parent, achall, validation):
        """Creates or updates the DNS challenge TXT record"""
        name = achall.validation_domain_name(achall.domain)
        try:
            info = self.inwx.nameserver.info({'domain': parent, 'name': name})['resData']
            if (not 'record' in info) or 0 == info['count']: raise NameError("Unknown record")
        except NameError as err:
            logging.debug("No record {0} existing ({1})".format(name, err))
        else:
            self.nsIds[name] = info['record'][0]['id']

        if name in self.nsIds:
            try:
                self.inwx.nameserver.updateRecord({'id': self.nsIds[name], 'type': 'TXT', 'content': validation, 'ttl': 300})
            except:
                return False
        else:
            try:
                res = self.inwx.nameserver.createRecord({'domain': parent, 'name': name, 'type': 'TXT', 'content': validation, 'ttl': 300})['resData']
                self.nsIds[name] = res['id']
            except:
                return False
        return True

    def delete_record(self, achall):
        """Deletes a previously created record"""
        name = achall.validation_domain_name(achall.domain)
        if not name in self.nsIds:
            return False
        try:
            self.inwx.nameserver.deleteRecord({'id': self.nsIds[name]})
        except:
            return False
        return True

    def perform(self, achalls):
        """Perform the given challenge.
        
        :param list achalls: Non-empty (guaranteed) list of
            :class:`~certbot.achallenges.AnnotatedChallenge`
            instances, such that it contains types found within
            :func:`get_chall_pref` only.
        
        :returns: List of ACME
            :class:`~acme.challenges.ChallengeResponse` instances
            or if the :class:`~acme.challenges.Challenge` cannot
            be fulfilled then:
                
                ``None``
                Authenticator can perform challenge, but not at this time.
                ``False``
                Authenticator will never be able to perform (error).
        
        :rtype: :class:`list` of
            :class:`acme.challenges.ChallengeResponse`
        
        :raises .PluginError: If challenges cannot be performed
        
        """
        results = []
        success = False
        for achall in achalls:
            response, validation = achall.response_and_validation()
            parent = self.get_inwx_domain(achall.domain)
            if(None == parent):
                results.append(False)
                continue
            if False == self.create_or_update_record(parent, achall, validation):
                logging.error("Failed to create TXT record for domain {0}".format(achall.domain))
                results.append(None)
                continue
            results.append(response)
            success = True
        
        #print(results)
        if success == True:
        	logging.info("Waiting 60s for DNS changes to propagate...")
        	time.sleep(60)
        return results

    def cleanup(self, achalls):
        """Revert changes and shutdown after challenges complete.
        
        :param list achalls: Non-empty (guaranteed) list of
            :class:`~certbot.achallenges.AnnotatedChallenge`
            instances, a subset of those previously passed to :func:`perform`.
        
        :raises PluginError: if original configuration cannot be restored
        
        """
        for achall in achalls:
            self.delete_record(achall)

    def more_info(self):
        """Human-readable string to help understand the module"""
        return (
            "Uses an external shell script to authenticate and deploy "
            "certificates.{0}"
            "External handler path: {handler}".format(
                os.linesep, handler=self.conf('inwxconfig'))
        )

