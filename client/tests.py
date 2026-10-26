from unittest.mock import patch
from django.test import SimpleTestCase

class ViewsTest(SimpleTestCase):
    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roll it!")

    @patch("client.views.roll", side_effect=[2, 5])
    def test_two_routes_and_comparison(self, roll):
        response = self.client.post("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["a"], 2)
        self.assertEqual(response.context["b"], 5)
        self.assertEqual(response.context["sign"], "<")
        self.assertEqual([call.args[0] for call in roll.call_args_list], ["direct", "nginx"])

    @patch("client.views.logger")
    @patch("client.views.roll", side_effect=OSError("missing cert"))
    def test_missing_certificate_returns_error(self, roll, logger):
        self.assertEqual(self.client.post("/").status_code, 502)

    @patch("client.views.roll", return_value=6)
    def test_individual_endpoints(self, roll):
        for path, route in [("/grpc", "direct"), ("/nginx", "nginx")]:
            response = self.client.get(path)
            self.assertEqual(response.json()["route"], route)
            self.assertEqual(response.json()["value"], 6)
