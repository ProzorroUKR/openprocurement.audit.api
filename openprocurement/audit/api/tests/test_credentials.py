import json

import mock
from hashlib import sha512
from openprocurement.audit.api.tests.base import BaseWebTest
import unittest

from openprocurement.audit.api.tests.utils import get_errors_field_names


class MonitoringCredentialsResourceTest(BaseWebTest):
    def setUp(self):
        super(MonitoringCredentialsResourceTest, self).setUp()
        self.create_monitoring()

    def test_credentials_no_access_token(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id),
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(('body', 'data'), next(get_errors_field_names(response, 'No access token was provided.')))

    @mock.patch('restkit.Resource.request')
    def test_credentials_query_param_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('restkit.Resource.request')
    def test_credentials_query_param_wrong_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'wrong_token'),
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('restkit.Client.request')
    def test_credentials_no_tender(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=404
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token'),
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, 'Tender {} not found'.format("f" * 32))))

    @mock.patch('restkit.Resource.request')
    def test_credentials_header_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            headers={'X-access-token': 'tender_token'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('restkit.Resource.request')
    def test_credentials_header_wrong_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            headers={'X-access-token': 'wrong_token'},
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('restkit.Resource.request')
    def test_credentials_body_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            {'access': {'token': 'tender_token'}}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('restkit.Resource.request')
    def test_credentials_body_wrong_access_token(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            {'access': {'token': 'wrong_token'}},
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringCredentialsResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
