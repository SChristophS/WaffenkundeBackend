# tests/test_personalize.py

import unittest
from app import app
from unittest.mock import patch
from bson.objectid import ObjectId

class TestPersonalize(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
    
    @patch('resources.personalize.db')
    def test_personalize_story_success(self, mock_db):
        story_id = str(ObjectId())
        mock_db.stories.find_one.return_value = {'_id': ObjectId(story_id)}
        mock_db.personalized_stories.insert_one.return_value = type('obj', (object,), {'inserted_id': ObjectId()})
        
        data = {
            'story_id': story_id,
            'personal_data': {'child_name': 'Max'},
            'user_images': ['path/to/image1.jpg', 'path/to/image2.jpg']
        }
        response = self.app.post('/api/personalize', json=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('personalized_story_id', response.get_json())
    
    @patch('resources.personalize.db')
    def test_personalize_story_missing_name(self, mock_db):
        story_id = str(ObjectId())
        data = {
            'story_id': story_id,
            'personal_data': {},
            'user_images': []
        }
        response = self.app.post('/api/personalize', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Child's name is required", str(response.data))
    
    @patch('resources.personalize.db')
    def test_personalize_story_invalid_story_id(self, mock_db):
        data = {
            'story_id': 'invalid_id',
            'personal_data': {'child_name': 'Max'},
            'user_images': []
        }
        response = self.app.post('/api/personalize', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid story ID', str(response.data))
    
    @patch('resources.personalize.db')
    def test_get_personalized_story_success(self, mock_db):
        personalized_story_id = str(ObjectId())
        mock_db.personalized_stories.find_one.return_value = {
            '_id': ObjectId(personalized_story_id),
            'story_id': str(ObjectId()),
            'personal_data': {'child_name': 'Max'},
            'user_images': [],
            'created_at': None
        }
        response = self.app.get(f'/api/personalized-story/{personalized_story_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Max', str(response.data))
    
    def test_get_personalized_story_invalid_id(self):
        response = self.app.get('/api/personalized-story/invalid_id')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid personalized story ID', str(response.data))

if __name__ == '__main__':
    unittest.main()
