from openprocurement.audit.api.tests.base import BaseWebTest
import unittest


class TenderMonitoringsResourceTest(BaseWebTest):

    def test_get_empty_list(self):
        response = self.app.get('/tenders/f9f9f9/monitorings')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get(self):
        tender_id = "f" * 32

        ids = []
        for i in range(10):
            self.create_monitoring(tender_id=tender_id)
            ids.append(self.monitoring_id)

        for i in range(5):  # these are not on the list
            self.create_monitoring(tender_id="a" * 32)

        response = self.app.get('/tenders/{}/monitorings'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "status"})

    def test_get_custom_fields(self):
        tender_id = "a" * 32

        ids = []
        for i in range(10):
            self.create_monitoring(tender_id=tender_id)
            ids.append(self.monitoring_id)

        response = self.app.get(
            '/tenders/{}/monitorings?opt_fields=dateModified%2Creasons'.format(
                tender_id
            )
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "dateModified", "status", "reasons"})

    def test_get_test_empty(self):
        tender_id = "a" * 32
        for i in range(10):
            self.create_monitoring(tender_id=tender_id, mode="test")

        response = self.app.get(
            '/tenders/{}/monitorings'.format(tender_id)
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get_test(self):
        tender_id = "a" * 32

        ids = []
        for i in range(10):
            self.create_monitoring(tender_id=tender_id, mode="test")
            ids.append(self.monitoring_id)

        response = self.app.get(
            '/tenders/{}/monitorings?mode=test'.format(tender_id)
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual([e["id"] for e in response.json['data']], ids)


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TenderMonitoringsResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
