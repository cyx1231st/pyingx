__author__ = 'Yingxin'

import fixtures
import testtools

from pyingx import log
from pyingx.experimental import test_obj
from pyingx.experimental import monkey_patch


def test1(*args, **kwargs):
    print args
    print kwargs
    print "in test1"

def dec(func):
    def func_wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return func_wrapper


class TestLog(testtools.TestCase):
    def test_global_level(self):
        g_level = log.get_global_level()
        self.assertEqual(g_level,
                         log.Level.INFO,
                         "Default log level should be INFO, not %r." % g_level)

        g_level = log.Level.ERROR
        log.set_global_level(g_level)
        self.assertEqual(log.get_global_level(),
                         g_level,
                         "Global level cannot be set.")

    def test_default_object(self):
        self.assertIsInstance(log.LOG, log.Logger, "LOG should be a instance of Logger.")

    def test_test(self):
        fixture = fixtures.MonkeyPatch('pyingx.experimental.test_obj.A.action', test1)
        fixture.setUp()
        ttt = test_obj.A()
        fixture.cleanUp()

        test_obj.A.action = dec(test_obj.A.action)

        a = monkey_patch.test1()

        ttt = test_obj.A()
        ttt.action()
