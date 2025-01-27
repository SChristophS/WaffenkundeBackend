# tests/test_generate_pdf.py

import unittest
from app import app
from unittest.mock import patch
from bson.objectid import ObjectId

class TestGeneratePDF(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    @patch('resources.generate_pdf.db')
    @patch('resources.generate_pdf.HTML')
    @patch('resources.generate_pdf.os')
    @patch('resources.generate_pdf.Environment')
    def test_generate_pdf_success(self, mock_env, mock_os, mock_html, mock_db):
        personalized_story_id = str(ObjectId())
        mock_db.personalized_stories.find_one.return_value = {
            '_id': ObjectId(personalized_story_id),
            'story_id': str(ObjectId()),
            'personal_data': {'child_name': 'Max'},
            'user_images': [],
            'created_at': None
        }
        mock_db.stories.find_one.return_value = {
            '_id': ObjectId(),
            'title': 'Geschichte 1',
            'scenes': []
        }
        mock_template = mock_env.return_value.get_template.return_value
        mock_template.render.return_value = '<html></html>'
        mock_html.return_value.write_pdf.return_value = True
        mock_os.path.join.return_value = '/path/to/pdf.pdf'
        
        response = self.app.get(f'/api/generate-pdf/{personalized_story_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('pdf_path', response.get_json())
    
    def test_generate_pdf_invalid_id(self):
        response = self.app.get('/api/generate-pdf/invalid_id')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid personalized story ID', str(response.data))
    
    @patch('resources.generate_pdf.os')
    def test_download_pdf_success(self, mock_os):
        personalized_story_id = str(ObjectId())
        mock_os.path.exists.return_value = True
        response = self.app.get(f'/api/download-pdf/{personalized_story_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
    
    @patch('resources.generate_pdf.os')
    def test_download_pdf_not_found(self, mock_os):
        personalized_story_id = str(ObjectId())
        mock_os.path.exists.return_value = False
        response = self.app.get(f'/api/download-pdf/{personalized_story_id}')
        self.assertEqual(response.status_code, 404)
        self.assertIn('PDF not found', str(response.data))

if __name__ == '__main__':
    unittest.main()
