# -*- coding: utf-8 -*-

from openprocurement.audit.api.tests.base import BaseWebTest


class HealthTest(BaseWebTest):

    def test_health_view(self):
        response = self.app.get('/health', status=200)
        self.assertEqual(response.status, '200 OK')

