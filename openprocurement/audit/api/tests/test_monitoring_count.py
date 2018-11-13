from openprocurement.audit.api.tests.base import BaseWebTest


class MonitoringCountResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitoringCountResourceTest, self).setUp()

    def test_get_nil(self):
        response = self.app.get('/monitorings/count')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 0)

    def test_get_nil_ignore_mode(self):
        self.create_monitoring(mode="test")
        response = self.app.get('/monitorings/count')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 0)


    def test_get_one(self):
        self.create_monitoring()
        response = self.app.get('/monitorings/count')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 1)


    def test_get_13(self):
        for _ in range(13):
            self.create_monitoring()
        response = self.app.get('/monitorings/count')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 13)

    def test_get_nil_ignore_real(self):
        self.create_monitoring()
        response = self.app.get('/monitorings/count?mode=test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 0)


    def test_get_one_test(self):
        self.create_monitoring()
        self.create_monitoring(mode="test")
        response = self.app.get('/monitorings/count?mode=test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 1)


    def test_get_13_test(self):
        self.create_monitoring()
        for _ in range(13):
            self.create_monitoring(mode="test")
        response = self.app.get('/monitorings/count?mode=test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"], 13)

