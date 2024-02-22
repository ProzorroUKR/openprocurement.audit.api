import unittest
from hashlib import sha512

from unittest import mock
from datetime import datetime
from freezegun import freeze_time
from iso8601 import parse_date
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names
from openprocurement.audit.api.constants import RESOLUTION_WAIT_PERIOD
from openprocurement.audit.monitoring.utils import calculate_normalized_business_date


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringEliminationBaseTest(BaseWebTest, DSWebTestMixin):

    def get_elimination_resolution(self):
        data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "not_eliminated",
            },
            "description": "Do you have spare crutches?",
            "documents": [
                {
                    'title': 'sign.p7s',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/pkcs7-signature',
                }
            ]
        }
        return data

    def setUp(self):
        super(MonitoringEliminationBaseTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'

    def create_addressed_monitoring(self, restricted_config=False, **kwargs):
        self.create_active_monitoring(restricted_config=restricted_config, **kwargs)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                },
                "status": "addressed",
            }}
        )
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

    def create_monitoring_with_elimination(self, restricted_config=False, **kwargs):
        self.create_addressed_monitoring(restricted_config=restricted_config, **kwargs)
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "description": "It's a minimal required elimination report",
                "documents": [
                    {
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.elimination = response.json["data"]

    def create_monitoring_with_resolution(self, restricted_config=False, **kwargs):
        self.create_monitoring_with_elimination(restricted_config=restricted_config, **kwargs)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": {
                    "result": "partly",
                    "resultByType": {
                        "corruptionProcurementMethodType": "eliminated",
                        "corruptionAwarded": "not_eliminated",
                    },
                    "description": "Do you have spare crutches?",
                    "documents": [
                        {
                            'title': 'sign.p7s',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/pkcs7-signature',
                        }
                    ]
                },
            }},
        )


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringActiveEliminationResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(MonitoringActiveEliminationResourceTest, self).setUp()
        self.create_active_monitoring()

    def test_fail_post_elimination_report_when_not_in_addressed_state(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        request_data = {
            "description": "Five pint, six pint, seven pint, flour."
        }
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
            status=422
        )

        self.assertEqual(
            ('body', 'eliminationReport'),
            next(get_errors_field_names(response, 'Can\'t update in current active monitoring status.')))

    def test_fail_post_elimination_resolution_without_conclusion(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": self.get_elimination_resolution(),
            }},
            status=422
        )
        assert response.json == {"status": "error", "errors": [
            {"location": "body", "name": "eliminationResolution",
             "description": "This field cannot be updated in the active status."}]}


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringEliminationResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(MonitoringEliminationResourceTest, self).setUp()
        self.create_addressed_monitoring()

    def test_get_elimination(self):
        self.app.get(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            status=403
        )

    def test_patch_elimination(self):
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "One pint, two pint, three pint, four,"}},
            status=405
        )

    def test_patch_sas_elimination(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            {"data": {"description": "One pint, two pint, three pint, four,"}},
            status=405
        )

    def test_success_put(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        request_data = {
            "description": "Five pint, six pint, seven pint, flour.",
            "dateCreated": "1988-07-11T15:53:06.068598+03:00",
            "documents": [
                {
                    'title': 'lorem.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }
            ],
        }
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.status_code, 200)

        # get monitoring
        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(data["description"], request_data["description"])
        self.assertEqual(data["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertNotIn("resolution", data)
        self.assertEqual(len(data["documents"]), 1)
        document = data["documents"][0]
        self.assertNotEqual(document["url"], request_data["documents"][0]["url"])
        self.assertEqual(document["author"], "tender_owner")

    def test_fail_update_resolution(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": self.get_elimination_resolution(),
            }},
            status=403
        )

        assert response.json == {u'status': u'error', u'errors': [
            {u'description': u"Can't post eliminationResolution without eliminationReport "
                             u"earlier than 5 business days since conclusion.datePublished",
             u'location': u'body', u'name': u'data'}]}


    def test_success_post_resolution_without_report(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        conclusion_published = response.json["data"]["conclusion"]["datePublished"]
        allow_post_since = calculate_normalized_business_date(
            parse_date(conclusion_published),
            RESOLUTION_WAIT_PERIOD
        )
        request_data = self.get_elimination_resolution()
        with freeze_time(allow_post_since):
            response = self.app.patch_json(
                '/monitorings/{}'.format(self.monitoring_id),
                {"data": {
                    "eliminationResolution": request_data,
                }},
            )

        resolution = response.json["data"]["eliminationResolution"]
        self.assertEqual(resolution["result"], request_data["result"])
        self.assertEqual(resolution["resultByType"], request_data["resultByType"])
        self.assertEqual(resolution["description"], request_data["description"])
        self.assertEqual(resolution["dateCreated"], allow_post_since.isoformat())
        self.assertEqual(len(resolution["documents"]), len(request_data["documents"]))


class MonitoringEliminationResolutionResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(MonitoringEliminationResolutionResourceTest, self).setUp()
        self.create_monitoring_with_resolution()

    def test_elimination_resolution_get(self):
        response = self.app.get('/monitorings/{}/eliminationResolution'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEquals('partly', response.json['data']['result'])
        self.assertEquals('Do you have spare crutches?', response.json['data']['description'])

    def test_elimination_report_get(self):
        response = self.app.get('/monitorings/{}/eliminationReport'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEquals('It\'s a minimal required elimination report', response.json['data']['description'])

    def test_restricted_visibility(self):
        self.create_monitoring_with_resolution(parties=[self.initial_party], restricted_config=True)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data']["eliminationReport"]["description"],
            "It's a minimal required elimination report",
        )
        self.assertEqual(response.json['data']["eliminationReport"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["eliminationReport"]["documents"][0]["url"])
        self.assertEqual(response.json['data']["eliminationResolution"]["description"], "Do you have spare crutches?")
        self.assertEqual(response.json['data']["eliminationResolution"]["documents"][0]["title"], "sign.p7s")
        self.assertIn("http://localhost", response.json['data']["eliminationResolution"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data']["eliminationReport"]["description"],
            "It's a minimal required elimination report",
        )
        self.assertEqual(response.json['data']["eliminationReport"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["eliminationReport"]["documents"][0]["url"])
        self.assertEqual(response.json['data']["eliminationResolution"]["description"], "Do you have spare crutches?")
        self.assertEqual(response.json['data']["eliminationResolution"]["documents"][0]["title"], "sign.p7s")
        self.assertIn("http://localhost", response.json['data']["eliminationResolution"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["eliminationResolution"]["description"], "Приховано")
        self.assertEqual(response.json['data']["eliminationResolution"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["eliminationResolution"]["documents"][0]["url"], "Приховано")
        self.assertEqual(response.json['data']["eliminationReport"]["description"], "Приховано")
        self.assertEqual(response.json['data']["eliminationReport"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["eliminationReport"]["documents"][0]["url"], "Приховано")

        # check masking in feed
        response = self.app.get(f'/monitorings?opt_fields=eliminationResolution,eliminationReport')
        self.assertEqual(response.json['data'][-1]["eliminationResolution"]["description"], "Приховано")
        self.assertEqual(response.json['data'][-1]["eliminationResolution"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data'][-1]["eliminationResolution"]["documents"][0]["url"], "Приховано")
        self.assertEqual(response.json['data'][-1]["eliminationReport"]["description"], "Приховано")
        self.assertEqual(response.json['data'][-1]["eliminationReport"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data'][-1]["eliminationReport"]["documents"][0]["url"], "Приховано")


class UpdateEliminationResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(UpdateEliminationResourceTest, self).setUp()
        self.create_monitoring_with_elimination(parties=[self.initial_party])

    def test_forbidden_sas_patch(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [],
        }
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
            status=405
        )

    def test_forbidden_patch(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [],
        }
        self.app.patch_json(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            {"data": request_data},
            status=405
        )

    def test_forbidden_put(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "description": "Hi there",
                "documents": [
                    {
                        'title': 'texts.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ],
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [{u'description': u"Can't post another elimination report.", u'location': u'body', u'name': u'data'}],
        )

    def test_forbidden_sas_post_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        self.app.post_json(
            '/monitorings/{}/eliminationReport/documents?acc_token={}'.format(
                self.monitoring_id, self.tender_owner_token),
            {"data": document},
            status=403
        )

    def test_forbidden_without_token_post_document(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        self.app.post_json(
            '/monitorings/{}/eliminationReport/documents'.format(self.monitoring_id),
            {"data": document},
            status=403
        )

    def test_success_post_document(self):
        # dateModified
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["dateModified"], '2018-01-01T11:00:00+02:00')

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        post_time = '2018-01-13T13:35:00+02:00'
        with freeze_time(post_time):
            response = self.app.post_json(
                '/monitorings/{}/eliminationReport/documents?acc_token={}'.format(
                    self.monitoring_id, self.tender_owner_token),
                {"data": document},
            )
        self.assertEqual(response.status_code, 201)

        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        data = response.json["data"]
        self.assertEqual(len(data["eliminationReport"]["documents"]), 2)
        self.assertEqual(data["eliminationReport"]["documents"][1]["title"], document["title"])
        self.assertEqual(data["dateModified"], post_time)

    def test_patch_document_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_pass, self.sas_pass))
        document = {
            'title': 'another.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        doc_to_update = self.elimination["documents"][0]

        self.app.patch_json(
            '/monitorings/{}/eliminationReport/documents/{}'.format(
                self.monitoring_id, doc_to_update["id"]
            ),
            {"data": document},
            status=403
        )

    def test_patch_document(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        request_data = {
            'title': 'sign-2.p7s',
            'url': self.generate_docservice_url(),
            'format': 'application/pkcs7-signature',
            'hash': 'md5:' + '1' * 32,
        }
        doc_to_update = self.elimination["documents"][0]
        response = self.app.patch_json(
            '/monitorings/{}/eliminationReport/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"],  self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertNotEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertNotEqual(response.json["data"]["hash"], request_data["hash"])

    def test_put_document_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        document = {
            'title': 'my_new_file.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'text/css',
        }
        doc_to_update = self.elimination["documents"][0]

        self.app.put_json(
            '/monitorings/{}/eliminationReport/documents/{}'.format(
                self.monitoring_id, doc_to_update["id"]
            ),
            {"data": document},
            status=403
        )

    def test_put_document(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        request_data = {
            'title': 'sign-1.p7s',
            'url': self.generate_docservice_url(),
            'format': 'application/json',
            'hash': 'md5:' + '0' * 32,
        }
        doc_to_update = self.elimination["documents"][0]
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"],  self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertEqual(response.json["data"]["hash"], request_data["hash"])

    def test_fail_update_resolution_wo_result_by_type(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "result": "partly",
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )
        self.assertEqual(response.json["errors"][0]["description"],
                         {"resultByType": ["This field is required."]})

    def test_fail_update_resolution_wrong_result_by_type(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionChanges": "eliminated",
            }
        }
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )

    def test_fail_update_resolution_wrong_result_by_type_value(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "Nope",
            }
        }
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )

    def test_success_update_resolution(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "not_eliminated",
            },
            "description": "Do you have spare crutches?",
            "documents": [
                {
                    'title': 'sign.p7s',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/pkcs7-signature',
                }
            ]
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        resolution = response.json["data"]["eliminationResolution"]

        self.assertEqual(resolution["result"], request_data["result"])
        self.assertEqual(resolution["resultByType"], request_data["resultByType"])
        self.assertEqual(resolution["description"], request_data["description"])
        self.assertEqual(resolution["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(len(resolution["documents"]), len(request_data["documents"]))

    def test_success_update_party_resolution(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        party_id = response.json['data']['parties'][0]['id']

        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "not_eliminated",
            },
            "description": "Do you have spare crutches?",
            "relatedParty": party_id
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['eliminationResolution']['relatedParty'], party_id)

    def test_success_update_party_resolution_party_id_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "not_eliminated",
            },
            "description": "Do you have spare crutches?",
            "relatedParty": "Party with the devil"
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }}, status=422
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'eliminationResolution', 'relatedParty'),
            next(get_errors_field_names(response, 'relatedParty should be one of parties.')))

    def test_fail_change_status(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "completed",
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [{
                'description': "Can't change status to completed before elimination period ends.",
                'location': 'body',
                'name': 'data'
            }]
        )

    @freeze_time('2018-01-20T12:00:00.000000+03:00')
    def test_change_status_without_report(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "completed",
            }}, status=422
        )


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class ResolutionMonitoringResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(ResolutionMonitoringResourceTest, self).setUp()
        self.create_monitoring_with_resolution()

    def test_change_report_not_allowed(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
            status=405
        )

    @freeze_time('2018-01-20T12:00:00.000000+03:00')
    def test_success_change_status(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "completed",
            }},
        )
        self.assertEqual(response.json["data"]["status"], "completed")

        # can't update resolution
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": {
                    "result": "completely",
                },
            }},
            status=422
        )

        # can't update elimination report
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
            status=405
        )
