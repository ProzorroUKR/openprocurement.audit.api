import unittest

import mock
from datetime import datetime, timedelta

from openprocurement.audit.api.utils import calculate_business_date, get_access_token


class CalculateBusinessDateTests(unittest.TestCase):

    @mock.patch('openprocurement.audit.api.utils.calculate_business_date_base')
    def test_days_calculation(self, base_calculate_mock):
        date = datetime.now()
        result = calculate_business_date(date, timedelta(days=10), working_days=False)
        base_calculate_mock.assert_called_once_with(date, timedelta(days=10), working_days=False, context=None)
        self.assertEqual(result, base_calculate_mock.return_value)

    def test_accelerator(self):
        date = datetime.now()
        result = calculate_business_date(date, timedelta(days=10), context={'monitoringDetails': 'accelerator=2'})
        self.assertEqual(result, date + timedelta(days=10/2))


class GetAccessTokenTests(unittest.TestCase):

    def test_token_query_param(self):
        self.assertEqual(get_access_token(
            request=mock.Mock(params={'acc_token': 'test_token'})),
            'test_token'
        )

    def test_token_headers(self):
        self.assertEqual(get_access_token(
            request=mock.Mock(params={}, headers={'X-Access-Token': 'test_token'})),
            'test_token'
        )

    def test_token_body(self):
        request = mock.Mock(
            method='POST',
            content_type='application/json',
            params={},
            headers={},
            json_body={
                'access': {
                    'token': 'test_token'
                }
            }
        )
        self.assertEqual(get_access_token(request=request), 'test_token')

    def test_no_token(self):
        request = mock.Mock(
            method='POST',
            content_type='application/json',
            params={},
            headers={},
            json_body={}
        )
        self.assertRaises(ValueError, get_access_token, request=request)
