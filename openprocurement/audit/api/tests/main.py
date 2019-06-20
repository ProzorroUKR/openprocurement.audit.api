# -*- coding: utf-8 -*-

import unittest

from openprocurement.audit.api.tests import test_auth, test_migration, test_spore


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_auth.suite())
    suite.addTest(test_spore.suite())
    suite.addTest(test_migration.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
