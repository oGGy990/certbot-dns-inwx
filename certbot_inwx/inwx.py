import sys

if sys.version_info.major == 3:
    import xmlrpc.client
    from xmlrpc.client import _Method
    import urllib.request, urllib.error, urllib.parse
else:
    import xmlrpclib
    from xmlrpclib import _Method
    import urllib2

import base64
import struct
import time
import hmac
import hashlib

def getOTP(shared_secret):
    key = base64.b32decode(shared_secret, True)
    msg = struct.pack(">Q", int(time.time())//30)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    if sys.version_info.major == 3:
        o = h[19] & 15
    else:
        o = ord(h[19]) & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

class domrobot ():
    def __init__ (self, address, debug = False):
        self.url = address
        self.debug = debug
        self.cookie = None
        self.version = "1.0"

    def __getattr__(self, name):
        return _Method(self.__request, name)

    def __request (self, methodname, params):
        tuple_params = tuple([params[0]])
        if sys.version_info.major == 3:
            requestContent = xmlrpc.client.dumps(tuple_params, methodname)
        else:
            requestContent = xmlrpclib.dumps(tuple_params, methodname)
        if(self.debug == True):
            print(("Anfrage: "+str(requestContent).replace("\n", "")))
        headers = { 'User-Agent' : 'DomRobot/'+self.version+' Python-v2.7', 'Content-Type': 'text/xml','content-length': str(len(requestContent))}
        if(self.cookie!=None):
            headers['Cookie'] = self.cookie

        if sys.version_info.major == 3:
            req = urllib.request.Request(self.url, bytearray(requestContent, 'ascii'), headers)
            response = urllib.request.urlopen(req)
        else:
            req = urllib2.Request(self.url, bytearray(requestContent, 'ascii'), headers)
            response = urllib2.urlopen(req)

        responseContent = response.read()

        if sys.version_info.major == 3:
            cookies = response.getheader('Set-Cookie')
        else:
            cookies = response.info().getheader('Set-Cookie')

        if(self.debug == True):
            print(("Antwort: "+str(responseContent).replace("\n", "")))
        if sys.version_info.major == 3:
            apiReturn = xmlrpc.client.loads(responseContent)
        else:
            apiReturn = xmlrpclib.loads(responseContent)
        apiReturn = apiReturn[0][0]
        if(apiReturn["code"]!=1000):
            raise NameError('There was a problem: %s (Error code %s)' % (apiReturn['msg'], apiReturn['code']), apiReturn)
            return False

        if(cookies!=None):
                if sys.version_info.major == 3:
                    cookies = response.getheader('Set-Cookie')
                else:
                    cookies = response.info().getheader('Set-Cookie')
                self.cookie = cookies
                if(self.debug == True):
                    print(("Cookie:" + self.cookie))
        return apiReturn

class prettyprint (object):
    """
    This object is just a collection of prettyprint helper functions for the output of the XML-API.
    """

    @staticmethod
    def contacts(contacts):
        """
        iterable contacts:  The list of contacts to be printed.
        """
        if("resData" in contacts):
            contacts = contacts['resData']

        output = "\nCurrently you have %i contacts set up for your account at InterNetworX:\n\n" % len(contacts['contact'])
        for contact in contacts['contact']:
            output += "ID: %s\nType: %s\n%s\n%s\n%s %s\n%s\n%s\nTel: %s\n------\n" % (contact['id'], contact['type'], contact['name'], contact['street'], contact['pc'], contact['city'], contact['cc'], contact['email'], contact['voice'])
        return output

    @staticmethod
    def domains(domains):
        """
        list domains:  The list of domains to be pretty printed.
        """
        if("resData" in domains):
            domains = domains['resData']

        output = "\n%i domains:\n" % len(domains['domain'])
        for domain in domains['domain']:
            output += "Domain: %s (Status: %s)\n" % (domain['domain'], domain['status'])
        return output

    @staticmethod
    def nameserversets(nameserversets):
        """
        list namerserversets:  The list of nameserversets to be pretty printed.
        """
        if("resData" in nameserversets):
            nameserversets = nameserversets['resData']

        count, total = 0, len(nameserversets['nsset'])
        output = "\n%i nameserversets:\n" % total
        for nameserverset in nameserversets['nsset']:
            count += 1
            output += "%i of %i - ID: %i consisting of [%s]\n" % (count, total, nameserverset['id'], ", ".join(nameserverset['ns']))
        return output

    @staticmethod
    def domain_log(logs):
        """
        list logs:  The list of nameserversets to be pretty printed.
        """
        if("resData" in logs):
            logs = logs['resData']

        count, total = 0, len(logs['domain'])
        output = "\n%i log entries:\n" % total
        for log in logs['domain']:
            count += 1
            output += "%i of %i - %s status: '%s' price: %.2f invoice: %s date: %s remote address: %s\n" % (count, total, log['domain'], log['status'], log['price'], log['invoice'], log['date'], log['remoteAddr'])
            output += "           user text: '%s'\n" % log['userText'].replace("\n",'\n           ')
        return output

    @staticmethod
    def domain_check(checks):
        """
        list checks:  The list of domain checks to be pretty printed.
        """
        if("resData" in checks):
                checks = checks['resData']

        count, total = 0, len(checks)
        output = "\n%i domain check(s):\n" % total
        for check in checks['domain']:
            count += 1
            output += "%s = %s" % (check['domain'], check['status'])
        return output
