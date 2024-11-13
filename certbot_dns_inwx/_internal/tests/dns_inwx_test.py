"""Tests for certbot_dns_inwx._internal.dns_inwx."""
import sys
import unittest
from unittest import mock

import dns.name
import pytest
from certbot import errors
from certbot.compat import os
from certbot.plugins import dns_test_common
from certbot.plugins.dns_test_common import DOMAIN
from certbot.tests import util as test_util
from dns.name import Name
from dns.rdatatype import RdataType

from certbot_dns_inwx._internal.dns_inwx import Authenticator, _INWXClient

KEY = 'config'
URL = 'https://test-api.example.com'
USERNAME = 'test-user'
PASSWORD = 'test-password'
SHARED_SECRET = 'test-secret'


class AuthenticatorTest(test_util.TempDirTestCase, dns_test_common.BaseAuthenticatorTest):
    def setUp(self) -> None:
        super().setUp()

        path = os.path.join(self.tempdir, 'inwx.cfg')
        dns_test_common.write({
            'dns_inwx_url': URL,
            'dns_inwx_username': USERNAME,
            'dns_inwx_password': PASSWORD,
            'dns_inwx_shared_secret': SHARED_SECRET,
        }, path)

        self.config = mock.MagicMock(dns_inwx_credentials=path, dns_inwx_propagation_seconds=0,
                                     dns_inwx_follow_cnames=False)
        self.auth = Authenticator(self.config, "dns-inwx")
        Authenticator.nameCache = {}
        Authenticator.clientCache = {}

        self.mock_client = mock.MagicMock()

    @test_util.patch_display_util()
    def test_perform(self, unused_mock_get_utility):
        self.auth._get_inwx_client = mock.MagicMock(return_value=self.mock_client)
        self.auth.perform([self.achall])

        expected = [mock.call.add_txt_record(DOMAIN, '_acme-challenge.' + DOMAIN, mock.ANY, mock.ANY)]
        assert self.mock_client.mock_calls == expected

    @test_util.patch_display_util()
    def test_perform_cnames(self, unused_mock_get_utility):
        self.auth._get_inwx_client = mock.MagicMock(return_value=self.mock_client)
        self.auth._follow_cnames = mock.MagicMock(return_value='_final.' + DOMAIN)
        self.auth.perform([self.achall])

        expected = [mock.call.add_txt_record(DOMAIN, '_final.' + DOMAIN, mock.ANY, mock.ANY)]
        assert self.mock_client.mock_calls == expected

    def test_cleanup(self):
        Authenticator.nameCache['_acme-challenge.' + DOMAIN] = '_final.' + DOMAIN
        self.auth._get_inwx_client = mock.MagicMock(return_value=self.mock_client)
        self.auth._attempt_cleanup = True
        self.auth.cleanup([self.achall])

        expected = [mock.call.del_txt_record(DOMAIN, '_final.' + DOMAIN, mock.ANY)]
        assert self.mock_client.mock_calls == expected

    @mock.patch('dns.resolver.Resolver')
    def test_follow_cnames_off(self, resolver_mock):
        result = self.auth._follow_cnames(DOMAIN, '_acme-challenge.' + DOMAIN)
        assert result == '_acme-challenge.' + DOMAIN
        assert not resolver_mock.called

    @mock.patch('dns.resolver.Resolver')
    def test_follow_cnames(self, resolver_mock):
        test_resolver = mock.MagicMock()

        def resolve(qname: Name | str, rdtype: RdataType | str) -> []:
            assert rdtype == dns.rdatatype.CNAME
            rrset = mock.MagicMock()
            answer = [rrset]
            if qname == dns.name.from_text('_acme-challenge.' + DOMAIN):
                rrset.target = dns.name.from_text('_intermediate.' + DOMAIN)
            elif qname == dns.name.from_text('_intermediate.' + DOMAIN):
                rrset.target = dns.name.from_text('_final.' + DOMAIN)
            elif qname == dns.name.from_text('_final.' + DOMAIN):
                return []
            else:
                assert False
            return answer

        test_resolver.resolve = resolve
        resolver_mock.return_value = test_resolver
        self.config.dns_inwx_follow_cnames = True
        result = self.auth._follow_cnames(DOMAIN, '_acme-challenge.' + DOMAIN)
        assert result == '_final.' + DOMAIN

    @mock.patch('dns.resolver.Resolver')
    def test_follow_cnames_finite_loop(self, resolver_mock):
        test_resolver = mock.MagicMock()

        def resolve(qname: Name | str, rdtype: RdataType | str) -> []:
            assert rdtype == dns.rdatatype.CNAME
            rrset = mock.MagicMock()
            answer = [rrset]
            if qname == dns.name.from_text('_acme-challenge.' + DOMAIN):
                rrset.target = dns.name.from_text('_intermediate.' + DOMAIN)
            elif qname == dns.name.from_text('_intermediate.' + DOMAIN):
                rrset.target = dns.name.from_text('_intermediate.' + DOMAIN)
            else:
                assert False
            return answer

        test_resolver.resolve = resolve
        resolver_mock.return_value = test_resolver
        self.config.dns_inwx_follow_cnames = True
        result = self.auth._follow_cnames(DOMAIN, '_acme-challenge.' + DOMAIN)
        assert result == '_intermediate.' + DOMAIN

    @mock.patch('dns.resolver.Resolver')
    def test_follow_cnames_no_cname(self, resolver_mock):
        test_resolver = mock.MagicMock()
        test_resolver.resolve = mock.MagicMock(return_value=[])
        resolver_mock.return_value = test_resolver
        self.config.dns_inwx_follow_cnames = True
        result = self.auth._follow_cnames(DOMAIN, '_acme-challenge.' + DOMAIN)
        assert result == '_acme-challenge.' + DOMAIN

    @mock.patch('certbot_dns_inwx._internal.dns_inwx._INWXClient')
    def test_get_inwx_client(self, client_mock):
        test_client = mock.MagicMock()
        client_mock.return_value = test_client

        self.auth._setup_credentials()
        self.auth._get_inwx_client()
        assert client_mock.called
        assert Authenticator.clientCache[self.auth.conf('credentials')] is test_client

    def test_get_inwx_client_cached(self):
        test_client = mock.MagicMock()
        Authenticator.clientCache[self.auth.conf('credentials')] = test_client
        assert self.auth._get_inwx_client() is test_client


class INWXClientTest(unittest.TestCase):
    @mock.patch('INWX.Domrobot.ApiClient.__new__')
    def _setUpClient(self, client_mock) -> _INWXClient:
        test_client = mock.MagicMock()
        test_client.login = mock.MagicMock(return_value={'code': 1000})
        client_mock.return_value = test_client
        return _INWXClient(URL, USERNAME, PASSWORD, SHARED_SECRET)

    @mock.patch('INWX.Domrobot.ApiClient.__new__')
    def test_login(self, client_mock):
        test_client = mock.MagicMock()
        test_client.login = mock.MagicMock(return_value={'code': 1000})
        client_mock.return_value = test_client
        _INWXClient(URL, USERNAME, PASSWORD, SHARED_SECRET)
        client_mock.assert_called_with(mock.ANY, URL)
        test_client.login.assert_called_once_with(USERNAME, PASSWORD, SHARED_SECRET)

    @mock.patch('INWX.Domrobot.ApiClient.__new__')
    def test_login_failure(self, client_mock):
        test_client = mock.MagicMock()
        test_client.login = mock.MagicMock(return_value={'code': 2200, 'msg': 'error'})
        client_mock.return_value = test_client
        with pytest.raises(errors.PluginError):
            _INWXClient(URL, USERNAME, PASSWORD, SHARED_SECRET)
        client_mock.assert_called_with(mock.ANY, URL)
        test_client.login.assert_called_once_with(USERNAME, PASSWORD, SHARED_SECRET)

    def test_call_api_data(self):
        test_client = self._setUpClient()
        expected = {'test': True}
        test_client.inwx.call_api = mock.MagicMock(return_value={'code': 1000, 'resData': expected})
        params = {'test': 'test'}
        result = test_client._call_api('test', params)
        assert result == expected
        test_client.inwx.call_api.assert_called_once_with('test', params)

    def test_call_api_no_data(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(return_value={'code': 1000})
        params = {'test': 'test'}
        result = test_client._call_api('test', params)
        assert result == {}
        test_client.inwx.call_api.assert_called_once_with('test', params)

    def test_call_api_failure(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(return_value={'code': 2200, 'msg': 'error'})
        params = {'test': 'test'}
        with pytest.raises(Exception):
            test_client._call_api('test', params)
        test_client.inwx.call_api.assert_called_once_with('test', params)

    def test_find_domain(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(
            return_value={'code': 1000, 'resData': {'count': 1, 'domains': [{'domain': 'b.a', 'type': 'MASTER'}]}})
        result = test_client._find_domain('d.c.b.a')
        assert result == 'b.a'

    def test_find_domain_failure(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(return_value={'code': 1000, 'resData': {'count': 0, 'domains': []}})
        with pytest.raises(errors.PluginError):
            test_client._find_domain('d.c.b.a')
        expected = [
            mock.call('nameserver.list', {'domain': 'b.a'}),
            mock.call('nameserver.list', {'domain': 'c.b.a'}),
            mock.call('nameserver.list', {'domain': 'd.c.b.a'}),
        ]
        assert test_client.inwx.call_api.mock_calls == expected

    def test_find_domain_nonmatching(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(
            return_value={'code': 1000, 'resData': {'count': 1, 'domains': [{'domain': 'b', 'type': 'MASTER'}]}})
        with pytest.raises(errors.PluginError):
            test_client._find_domain('d.c.b.a')

    def test_find_domain_nonmaster(self):
        test_client = self._setUpClient()
        test_client.inwx.call_api = mock.MagicMock(
            return_value={'code': 1000, 'resData': {'count': 1, 'domains': [{'domain': 'b.a', 'type': 'SLAVE'}]}})
        with pytest.raises(errors.PluginError):
            test_client._find_domain('d.c.b.a')

    def test_add_txt_record(self):
        test_client = self._setUpClient()
        test_client._call_api = mock.MagicMock(return_value={})
        test_client._find_domain = mock.MagicMock(return_value='test')
        test_client.add_txt_record('source', DOMAIN, 'content', 999)
        test_client._find_domain.assert_called_once_with(DOMAIN)
        test_client._call_api.assert_called_once_with('nameserver.createRecord',
                                                      {'domain': 'test', 'name': DOMAIN, 'type': 'TXT',
                                                       'content': 'content', 'ttl': 999})

    def test_del_txt_record(self):
        test_client = self._setUpClient()
        test_client._call_api = mock.MagicMock(return_value={'count': 1, 'record': [{'id': 999}]})
        test_client._find_domain = mock.MagicMock(return_value='test')
        test_client.del_txt_record('source', DOMAIN, 'content')
        test_client._find_domain.assert_called_once_with(DOMAIN)
        expected = [
            mock.call('nameserver.info',
                      {'domain': 'test', 'name': DOMAIN, 'content': 'content'}),
            mock.call('nameserver.deleteRecord', {'id': 999})]
        assert test_client._call_api.mock_calls == expected

    def test_del_txt_record_noexist(self):
        test_client = self._setUpClient()
        test_client._call_api = mock.MagicMock(return_value={'count': 0, 'record': []})
        test_client._find_domain = mock.MagicMock(return_value='test')
        with pytest.raises(errors.PluginError):
            test_client.del_txt_record('source', DOMAIN, 'content')
        test_client._find_domain.assert_called_once_with(DOMAIN)
        test_client._call_api.assert_called_once_with('nameserver.info',
                                                      {'domain': 'test', 'name': DOMAIN, 'content': 'content'})


if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:] + [__file__]))
