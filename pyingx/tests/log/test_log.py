__author__ = 'Yingxin'

import testtools

from pyingx import log


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
