from openprocurement.audit.request.tests.base import BaseWebTest


class TenderRequestsResourceTest(BaseWebTest):

    def test_get_empty_list(self):
        response = self.app.get('/tenders/f9f9f9/requests')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get(self):
        tender_id = "f" * 32

        ids = []
        for i in range(10):
            self.create_request(tenderId=tender_id)
            ids.append(self.request_id)

        for i in range(5):  # these are not on the list
            self.create_request(tenderId="a" * 32)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/tenders/{}/requests'.format(tender_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(
            set(response.json['data'][0].keys()),
            {"id", "dateCreated", "requestId", "dateModified"}
        )

    def test_get_custom_fields(self):
        tender_id = "a" * 32

        ids = []
        for i in range(10):
            self.create_request(tenderId=tender_id)
            ids.append(self.request_id)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(
            '/tenders/{}/requests?opt_fields=dateModified%2CrequestId'.format(
                tender_id
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(
            set(response.json['data'][0].keys()),
            {"id", "dateCreated", "dateModified", "requestId"}
        )

    def test_get_test_empty(self):
        tender_id = "a" * 32
        for i in range(10):
            self.create_request(tenderId=tender_id, mode="test")

        response = self.app.get(
            '/tenders/{}/requests'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])
