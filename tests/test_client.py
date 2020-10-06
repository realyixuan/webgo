import requests
import unittest


class ClientTest(unittest.TestCase):
    def test_get(self):
        response = requests.get('http://localhost:8080')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = requests.post(
            'http://localhost:8080',
            data={'name': 'Guido'}
        )
        self.assertEqual(response.status_code, 200)
