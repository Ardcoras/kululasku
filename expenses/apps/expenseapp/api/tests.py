from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from expenseapp.models import Organisation, ExpenseType

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testapi', password='password123')
        self.org = Organisation.objects.create(name='TestOrg', active=True)
        self.et = ExpenseType.objects.create(name='Type1', type='K', active=True, organisation=self.org)

    def test_login_and_fetch_organisations(self):
        res = self.client.post('/api/v1/login/', {'username': 'testapi', 'password': 'password123'}, format='json')
        self.assertEqual(res.status_code, 200)
        token = res.data['token']
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        res_orgs = self.client.get('/api/v1/organisations/')
        self.assertEqual(res_orgs.status_code, 200)
        self.assertEqual(len(res_orgs.data), 1)

    def test_pool_creation(self):
        res = self.client.post('/api/v1/login/', {'username': 'testapi', 'password': 'password123'}, format='json')
        token = res.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        
        line_data = {
            'description': 'Taxi',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '25.50',
            'organisation': self.org.id
        }
        res_pool = self.client.post('/api/v1/pool/', line_data, format='json')
        self.assertEqual(res_pool.status_code, 201)
        self.assertEqual(res_pool.data['user'], self.user.id)
