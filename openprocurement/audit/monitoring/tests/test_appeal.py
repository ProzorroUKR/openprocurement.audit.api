from openprocurement.audit.api.context import get_now
from freezegun import freeze_time
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin


@freeze_time('2018-01-01T11:00:00+02:00')
class BaseAppealTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(BaseAppealTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()

        self.tender_owner_token = "1234qwerty"
        monitoring = self.app.app.registry.mongodb.monitoring.get(self.monitoring_id)
        monitoring.update(
            tender_owner="broker",
            tender_owner_token=self.tender_owner_token
        )
        self.app.app.registry.mongodb.save_data(
            self.app.app.registry.mongodb.monitoring.collection,
            monitoring,
        )

    def post_conclusion(self, publish=True):
        authorization = self.app.authorization
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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

    def test_fail_patch_appeal_before_added(self):
        self.post_conclusion(publish=False)

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "proceeding": {
                    "dateProceedings": get_now().isoformat(),
                    "proceedingNumber": "somenumber",
                }
            }},
            status=404
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json["errors"],
            [{'location': 'body', 'name': 'data', 'description': 'Appeal not found'}]
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

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
            status=403
        )

    def test_success_appeal_minimum(self):
        self.post_conclusion()

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.put_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Lorem ipsum dolor sit amet'
            }},
        )
        self.assertEqual(
            response.json["data"],
            {
                'dateCreated': '2018-01-01T11:00:00+02:00',
                'description': 'Lorem ipsum dolor sit amet',
                'datePublished': '2018-01-01T11:00:00+02:00',
                'legislation': {
                    'article': ['8.10'],
                    'identifier': {
                        'id': '922-VIII',
                        'legalName': 'Закон України "Про публічні закупівлі"',
                        'uri': 'https://zakon.rada.gov.ua/laws/show/922-19'
                    },
                    'type': 'NATIONAL_LEGISLATION',
                    'version': '2020-04-19',
                }
             }
        )

    def test_success_appeal_with_document(self):
        self.post_conclusion()

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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

    def test_get_appeal(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["description"], 'Lorem ipsum dolor sit amet')

    def test_success_update_appeal(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'proceeding': {
                    'dateProceedings': get_now().isoformat(),
                    'proceedingNumber': 'somenumber',
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("proceeding", response.json["data"])
        proceeding = response.json["data"]["proceeding"]
        self.assertEqual(proceeding["proceedingNumber"], "somenumber")

        response = self.app.patch_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "proceeding": {
                    "dateProceedings": get_now().isoformat(),
                    "proceedingNumber": "somenumber",
                }
            }},
            status=403
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json["errors"],
            [{"location": "body", "name": "data", "description": "Can't post another proceeding."}]
        )

    def test_fail_patch_appeal(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/appeal?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "proceeding": {
                    "proceedingNumber": "somenumber",
                }
            }},
            status=422
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json["errors"][0]["description"],
            {'dateProceedings': ['This field is required.']},
        )

    def test_fail_update_appeal(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
                    "description": "Can't post another appeal."
                }
            ]
        )

    def test_success_post_document(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
        self.assertNotEqual(data["url"], request_data["url"])

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        self.tender_owner_token = "1234qwerty"
        monitoring = self.app.app.registry.mongodb.monitoring.get(self.monitoring_id)
        monitoring.update(
            tender_owner="broker",
            tender_owner_token=self.tender_owner_token
        )
        self.app.app.registry.mongodb.save_data(
            self.app.app.registry.mongodb.monitoring.collection,
            monitoring,
        )
        self.post_conclusion()
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.put_json(
            f'/monitorings/{self.monitoring_id}/appeal?acc_token={self.tender_owner_token}',
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
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["appeal"]["description"], "Lorem ipsum dolor sit amet")
        self.assertEqual(response.json['data']["appeal"]["documents"][0]["title"], "first.doc")
        self.assertIn("http://localhost", response.json['data']["appeal"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["appeal"]["description"], "Lorem ipsum dolor sit amet")
        self.assertEqual(response.json['data']["appeal"]["documents"][0]["title"], "first.doc")
        self.assertIn("http://localhost", response.json['data']["appeal"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["appeal"]["description"], "Приховано")
        self.assertEqual(response.json['data']["appeal"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["appeal"]["documents"][0]["url"], "Приховано")
