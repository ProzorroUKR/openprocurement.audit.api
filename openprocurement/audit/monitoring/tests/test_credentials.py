from hashlib import sha512
from unittest import mock
from openprocurement_client.exceptions import ResourceError
from openprocurement.audit.monitoring.tests.base import BaseWebTest
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


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

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_query_param_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_query_param_wrong_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'wrong_token'),
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_no_tender(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.side_effect = ResourceError(mock.Mock(status_code=404))

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token'),
            status=403
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, 'Tender {} not found'.format("f" * 32))))

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_tender_error(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.side_effect = ResourceError(mock.Mock(status_code=555))

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token'),
            status=555
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json,
            {'status': 'error', 'errors': [
                {'location': 'body', 'name': 'data', 'description': 'Unsuccessful tender request'}
            ]}
        )

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_header_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            headers={'X-access-token': 'tender_token'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_header_wrong_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            headers={'X-access-token': 'wrong_token'},
            status=403
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_body_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {
                'tender_token': sha512(b'tender_token').hexdigest()
            }
        }
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            {'access': {'token': 'tender_token'}}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('access', response.json)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_credentials_body_wrong_access_token(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials'.format(self.monitoring_id, 'tender_token'),
            {'access': {'token': 'wrong_token'}},
            status=403
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')
