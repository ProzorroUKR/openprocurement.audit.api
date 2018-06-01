# -*- coding: utf-8 -*-
import unittest
from freezegun import freeze_time
from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin


@freeze_time('2018-01-01T11:00:00+02:00')
class BaseAppealTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(BaseAppealTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()

        self.tender_owner_token = "1234qwerty"
        monitoring = self.db.get(self.monitoring_id)
        monitoring.update(tender_owner="broker", tender_owner_token=self.tender_owner_token)
        self.db.save(monitoring)

    def post_conclusion(self, publish=True):
        authorization = self.app.authorization
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                }
            }}
        )
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "declined" if publish else None,
                "conclusion": {
                    "description": "text",
                    "violationOccurred": False,
                }
            }}
        )
        self.app.authorization = authorization


class MonitoringAppealResourceTest(BaseAppealTest):

    def test_fail_appeal_before_conclusion(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
            status=422
        )
        self.assertEqual(
            response.json["errors"],
            [{'description': "Can't post before conclusion is published", 'location': 'body', 'name': 'appeal'}]
        )

    def test_fail_appeal_before_conclusion_posted(self):
        self.post_conclusion(publish=False)

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
            status=422
        )
        self.assertEqual(
            response.json["errors"],
            [{'description': "Can't post before conclusion is published", 'location': 'body', 'name': 'appeal'}]
        )

    def test_fail_appeal_none(self):
        self.post_conclusion()

        self.app.authorization = None
        self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
            status=403
        )

    def test_fail_appeal_sas(self):
        self.post_conclusion()

        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
            status=403
        )

    def test_success_appeal_minimum(self):
        self.post_conclusion()

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
        )
        self.assertEqual(
            response.json["data"],
            {'dateCreated': '2018-01-01T11:00:00+02:00', 'description': 'Lorem ipsum dolor sit amet',
             'datePublished': '2018-01-01T11:00:00+02:00'}
        )

    def test_success_appeal_with_document(self):
        self.post_conclusion()

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet',
                'documents': [
                    {
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.assertEqual(len(response.json["data"]["documents"]), 1)
        document = response.json["data"]["documents"][0]
        self.assertEqual(
            set(document.keys()),
            {
                'hash', 'author', 'format', 'url',
                'title', 'datePublished', 'dateModified', 'id',
            }
        )


class MonitoringAppealPostedResourceTest(BaseAppealTest):

    def setUp(self):
        super(MonitoringAppealPostedResourceTest, self).setUp()
        self.post_conclusion()
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet',
                'documents': [
                    {
                        'title': 'first.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.document_id = response.json["data"]["documents"][0]["id"]

    def test_fail_update_appeal(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Another description',
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [
                {
                    "location": "body",
                    "name": "data",
                    "description": "Can't post another appeal"
                }
            ]
        )

    def test_success_post_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/appeal/documents?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'title': 'lorem.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )

    def test_success_put_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            'title': 'another.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/json',
        }
        response = self.app.put_json(
            '/monitorings/{}/appeal/documents/{}?acc_token={}'.format(
                self.monitoring_id, self.document_id, self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )
        data = response.json["data"]
        self.assertEqual(data["id"], self.document_id)
        self.assertEqual(data["format"], request_data["format"])
        self.assertEqual(data["title"], request_data["title"])

    def test_success_patch_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            'title': 'another.doc',
            'url': self.generate_docservice_url(),
            'format': 'application/json',
        }
        response = self.app.patch_json(
            '/monitorings/{}/appeal/documents/{}?acc_token={}'.format(
                self.monitoring_id, self.document_id, self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )
        data = response.json["data"]
        self.assertEqual(data["id"], self.document_id)
        self.assertEqual(data["format"], request_data["format"])
        self.assertEqual(data["title"], request_data["title"])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringAppealResourceTest))
    suite.addTest(unittest.makeSuite(MonitoringAppealPostedResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
