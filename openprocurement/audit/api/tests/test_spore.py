# -*- coding: utf-8 -*-
import unittest

from openprocurement.audit.api.constants import VERSION
from openprocurement.audit.api.tests.base import BaseWebTest


class SporeTest(BaseWebTest):

    def test_spore(self):
        response = self.app.get('/spore')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["version"], VERSION)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SporeTest))
    return suite
