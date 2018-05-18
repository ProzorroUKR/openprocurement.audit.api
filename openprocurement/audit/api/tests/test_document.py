# -*- coding: utf-8 -*-
import unittest

from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.api.tests.utils import get_errors_field_names


class MonitoringDecisionDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringDecisionDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.test_monitoring_activation_data = {
            "status": "active",
            "decision": {
                "date": "2015-05-10T23:11:39.720908+03:00",
                "description": "text",
                "documents": [self.test_docservice_document_data]
            }
        }

    def test_monitoring_decision_document_get_single(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['decision']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/decision/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_monitoring_decision_document_get_list(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/decision/documents'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_monitoring_decision_document_download(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']['decision']['documents'][-1]
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/decision/documents/{}?download=some_id'.format(
            self.monitoring_id, document_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/decision/documents/{}?download={}'.format(
            self.monitoring_id, document_id, key))
        self.assertEqual(response.status, '302 Moved Temporarily')
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_monitoring_decision_document_upload_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/decision/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {('body', 'data')},
            get_errors_field_names(response, 'Can\'t add document in current active monitoring status'))


class MonitoringConclusionDocumentResourceTest(BaseWebTest, DSWebTestMixin):
    # TODO: Add tests on conclusion functionality ready
    pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringDecisionDocumentResourceTest))
    suite.addTest(unittest.makeSuite(MonitoringConclusionDocumentResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
