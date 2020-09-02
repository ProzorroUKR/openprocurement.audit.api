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
        self.assertEqual(response.json['total'], 10)
        self.assertEqual(response.json['count'], 10)
        self.assertEqual(response.json['limit'], 500)
        self.assertEqual(response.json['page'], 1)

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
        self.assertEqual(response.json['total'], 10)
        self.assertEqual(response.json['count'], 10)
        self.assertEqual(response.json['limit'], 500)
        self.assertEqual(response.json['page'], 1)

    def test_get_test_empty(self):
        tender_id = "a" * 32
        for i in range(5):
            self.create_request(tenderId=tender_id, mode="test")

        response = self.app.get(
            '/tenders/{}/requests'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])
        self.assertEqual(response.json['total'], 0)
        self.assertEqual(response.json['count'], 0)
        self.assertEqual(response.json['limit'], 500)
        self.assertEqual(response.json['page'], 1)

    def test_get_with_pagination(self):
        tender_id = "a" * 32
        for i in range(5):
            self.create_request(tenderId=tender_id, description="description %s" % str(i + 1))

        response = self.app.get(
            '/tenders/{}/requests?opt_fields=description&limit=2&page=2'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 2)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 2)
        self.assertEqual(len(response.json['data']), 2)
        self.assertEqual(response.json['data'][0]["description"], "description 3")
        self.assertEqual(response.json['data'][1]["description"], "description 4")

    def test_get_with_pagination_not_full_page(self):
        tender_id = "a" * 32
        for i in range(5):
            self.create_request(tenderId=tender_id, description="description %s" % str(i + 1))

        response = self.app.get(
            '/tenders/{}/requests?opt_fields=description&limit=2&page=3'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 1)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 3)
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]["description"], "description 5")

    def test_get_with_pagination_out_of_bounds_page(self):
        tender_id = "a" * 32
        for i in range(5):
            self.create_request(tenderId=tender_id, description="description %s" % str(i + 1))

        response = self.app.get(
            '/tenders/{}/requests?opt_fields=description&limit=2&page=4'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 0)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 4)
        self.assertEqual(len(response.json['data']), 0)
