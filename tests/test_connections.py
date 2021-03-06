from __future__ import with_statement
from os import path, makedirs, environ
import re
import shutil
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from nose.plugins.skip import SkipTest

import _mssql

from .helpers import config
server = config.server
username = config.user
password = config.password
database = config.database
port = config.port
ipaddress = config.ipaddress
instance = config.instance

cdir = path.dirname(__file__)
tmpdir = path.join(cdir, 'tmp')
config_dump_path = path.join(tmpdir, 'freetds-config-dump.txt')
dump_path = path.join(tmpdir, 'freetds-dump.txt')

def setup_module():
    if not path.isdir(tmpdir):
        makedirs(tmpdir)

class TestCons(unittest.TestCase):
    def connect(self, **kwargs):
        environ['TDSDUMPCONFIG'] = config_dump_path
        environ['TDSDUMP'] = dump_path
        _mssql.connect(**kwargs)
        with open(config_dump_path, 'r') as fh:
            return fh.read()

    def test_connection_by_dns_name(self):
        cdump = self.connect(server=server, port=port, user=username, password=password)
        dump_server_name = re.search('server_name = (\S+)', cdump).groups()[0]
        self.assertIn(server, dump_server_name)
        dump_server_host_name = re.search('server_host_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_server_host_name, server)
        dump_user_name = re.search('user_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_user_name, username)
        dump_port = re.search('port = (\S+)', cdump).groups()[0]
        self.assertIn(port, dump_port)

    def test_connection_by_ip(self):
        cdump = self.connect(server=ipaddress, port=port, user=username, password=password)
        dump_server_name = re.search('server_name = (\S+)', cdump).groups()[0]
        self.assertIn(ipaddress, dump_server_name)
        dump_server_host_name = re.search('server_host_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_server_host_name, ipaddress)

    def test_port_override_ipaddress(self):
        server_join = '%s:%s' % (ipaddress, port)
        cdump = self.connect(server=server_join, user=username, password=password)
        dump_server_name = re.search('server_name = (\S+)', cdump).groups()[0]
        self.assertIn(server_join, dump_server_name)
        dump_server_host_name = re.search('server_host_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_server_host_name, ipaddress)
        dump_port = re.search('port = (\S+)', cdump).groups()[0]
        self.assertIn(port, dump_port)

    def test_port_override_name(self):
        server_join = '%s:%s' % (server, port)
        cdump = self.connect(server=server_join, user=username, password=password)
        dump_server_name = re.search('server_name = (\S+)', cdump).groups()[0]
        self.assertIn(server, dump_server_name)
        dump_server_host_name = re.search('server_host_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_server_host_name, server)
        dump_port = re.search('port = (\S+)', cdump).groups()[0]
        self.assertIn(port, dump_port)

    def test_instance(self):
        if not instance:
            raise SkipTest
        server_join = r'%s\%s' % (server, instance)
        cdump = self.connect(server=server_join, user=username, password=password)
        dump_server_name = re.search('server_name = (\S+)', cdump).groups()[0]
        self.assertIn(server, dump_server_name)
        dump_server_host_name = re.search('server_host_name = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_server_host_name, server)
        dump_port = re.search('port = (\S+)', cdump).groups()[0]
        self.assertEqual(dump_port, 0)

    def test_repeated_failed_connections(self):
        # This is a test for https://github.com/pymssql/pymssql/issues/145
        # (Repeated failed connections result in error string getting longer
        # and longer)

        last_exc_message = None

        for i in range(5):
            try:
                _mssql.connect(
                    server='www.google.com',
                    port=80,
                    user='joe',
                    password='secret',
                    database='tempdb')
            except Exception as exc:
                exc_message = exc.args[0][1]
                self.assertIn(
                    b'Adaptive Server connection failed',
                    exc_message)

                if last_exc_message:
                    self.assertEqual(exc_message, last_exc_message)

                last_exc_message = exc_message
