import unittest
import os
from src import create_app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Set test environment variables
        os.environ["ADMIN_USERNAME"] = "admin"
        os.environ["ADMIN_PASSWORD"] = "password123"
        os.environ["USE_DATABASE_AUTH"] = "false"
        os.environ["JWT_SECRET_KEY"] = "test_secret_key"
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
            
    def test_login_user(self):
        # Try to login with correct credentials
        response = self.client.post('/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)
        self.assertIn('refresh_token', response.json)
        
    def test_login_invalid_credentials(self):
        # Try to login with incorrect credentials
        response = self.client.post('/login', json={
            'username': 'admin',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)
        
    def test_health_check(self):
        # First login to get a token
        login_response = self.client.post('/login', json={
            'username': 'admin',
            'password': 'password123'
        })
        token = login_response.json['access_token']
        
        # Use the token to access the health check endpoint
        response = self.client.get('/health', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json)
        self.assertEqual(response.json['status'], 'healthy')

if __name__ == '__main__':
    unittest.main()