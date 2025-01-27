# tests/test_app.py

import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    def test_home_page_not_found(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_endpoint(self):
        response = self.app.get('/invalid-endpoint')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
