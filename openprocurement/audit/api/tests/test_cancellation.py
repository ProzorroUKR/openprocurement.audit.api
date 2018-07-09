# -*- coding: utf-8 -*-
import unittest
import mock
import json

from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.api.tests.utils import get_errors_field_names
from openprocurement.audit.api.constants import CANCELLED_STATUS


class MonitoringCancellationResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringCancellationResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))

    def test_cancellation_get(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description',
                    'relatedParty': 'some_related_party'
                }
            }})
        response = self.app.get('/monitorings/{}/cancellation'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEquals('some_description', response.json['data']['description'])
        self.assertEquals('some_related_party', response.json['data']['relatedParty'])

    def test_get_cancellation_from_active_monitoring(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        with self.assertRaisesRegexp(Exception, 'Bad response: 403 Forbidden'):
            response = self.app.get('/monitorings/{}/cancellation'.format(self.monitoring_id))
            self.assertEqual(response.status_code, 404)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringCancellationResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
