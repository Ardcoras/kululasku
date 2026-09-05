import tempfile

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from expenseapp.models import AccountDimension, ExpenseLine, Organisation, ExpenseType

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class APITestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='testapi', password='password123')
        self.org = Organisation.objects.create(
            name='TestOrg',
            business_id='1234567-8',
            active=True,
            send_active=True,
        )
        self.et = ExpenseType.objects.create(
            name='Type1',
            type='O',
            active=True,
            persontype=self.user.person.type,
            multiplier=1.0,
            account='123',
            unit='EUR',
            organisation=self.org,
        )

    def _auth(self):
        res = self.client.post('/api/v1/login/', {'username': 'testapi', 'password': 'password123'}, format='json')
        self.assertEqual(res.status_code, 200)
        token = res.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def test_login_and_fetch_organisations(self):
        self._auth()
        res_orgs = self.client.get('/api/v1/organisations/')
        self.assertEqual(res_orgs.status_code, 200)
        self.assertEqual(len(res_orgs.data), 1)

    def test_api_root_without_trailing_slash_redirects(self):
        response = self.client.get('/api/v1')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/api/v1/')

    def test_login_endpoint_is_throttled(self):
        for _ in range(5):
            res = self.client.post('/api/v1/login/', {'username': 'testapi', 'password': 'wrong'}, format='json')
            self.assertEqual(res.status_code, 400)

        res = self.client.post('/api/v1/login/', {'username': 'testapi', 'password': 'wrong'}, format='json')
        self.assertEqual(res.status_code, 429)

    def test_pool_creation(self):
        self._auth()
        
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

    def test_organisation_filter_includes_matching_and_null_persontype(self):
        self._auth()

        org_null = Organisation.objects.create(
            name='NullTypeOrg',
            business_id='1234566-6',
            active=True,
            send_active=True,
        )
        ExpenseType.objects.create(
            name='NullTypeExpense',
            type='O',
            active=True,
            persontype=None,
            multiplier=1.0,
            account='123',
            unit='EUR',
            organisation=org_null,
        )

        org_other = Organisation.objects.create(
            name='OtherTypeOrg',
            business_id='1234565-4',
            active=True,
            send_active=True,
        )
        ExpenseType.objects.create(
            name='OtherTypeExpense',
            type='O',
            active=True,
            persontype=2,
            multiplier=1.0,
            account='123',
            unit='EUR',
            organisation=org_other,
        )

        res_orgs = self.client.get('/api/v1/organisations/')
        self.assertEqual(res_orgs.status_code, 200)
        ids = {x['id'] for x in res_orgs.data}
        self.assertIn(self.org.id, ids)
        self.assertIn(org_null.id, ids)
        self.assertNotIn(org_other.id, ids)

    def test_pool_line_update_description_and_org(self):
        """Updating a pool line's description and organisation is allowed when the new org is accessible."""
        self._auth()

        line_data = {
            'description': 'Original',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }
        res = self.client.post('/api/v1/pool/', line_data, format='json')
        self.assertEqual(res.status_code, 201)
        line_id = res.data['id']

        # Create a second accessible org (persontype=None → accessible to all)
        org2 = Organisation.objects.create(
            name='Org2', business_id='9999999-9', active=True, send_active=True,
        )
        et2 = ExpenseType.objects.create(
            name='Type2', type='O', active=True, persontype=None,
            multiplier=1.0, account='456', unit='EUR', organisation=org2,
        )

        patch_data = {
            'description': 'Updated',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': et2.id,
            'basis': '20.00',
            'organisation': org2.id,
        }
        res_patch = self.client.patch(f'/api/v1/pool/{line_id}/', patch_data, format='json')
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['description'], 'Updated')
        self.assertEqual(res_patch.data['organisation'], org2.id)

    def test_pool_line_delete(self):
        """A pool line can be deleted via the API; it is removed from the database."""
        self._auth()

        line_data = {
            'description': 'To be deleted',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '5.00',
            'organisation': self.org.id,
        }
        res = self.client.post('/api/v1/pool/', line_data, format='json')
        self.assertEqual(res.status_code, 201)
        line_id = res.data['id']

        res_del = self.client.delete(f'/api/v1/pool/{line_id}/')
        self.assertEqual(res_del.status_code, 204)

        from expenseapp.models import ExpenseLine
        self.assertFalse(ExpenseLine.objects.filter(id=line_id).exists())

    def test_pool_create_rejected_for_inaccessible_org(self):
        """Creating a pool line for an org the user has no access to returns 403."""
        self._auth()

        # Org with expense types only for persontype=2; our user has persontype=1
        org_blocked = Organisation.objects.create(
            name='BlockedOrg', business_id='8888888-8', active=True, send_active=True,
        )
        et_blocked = ExpenseType.objects.create(
            name='BlockedType', type='O', active=True, persontype=2,
            multiplier=1.0, account='789', unit='EUR', organisation=org_blocked,
        )

        line_data = {
            'description': 'Should fail',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': et_blocked.id,
            'basis': '50.00',
            'organisation': org_blocked.id,
        }
        res = self.client.post('/api/v1/pool/', line_data, format='json')
        self.assertEqual(res.status_code, 403)

    def test_pool_update_rejected_for_inaccessible_org(self):
        """Moving a pool line to an inaccessible org is rejected with 403."""
        self._auth()

        # Create a valid line first
        line_data = {
            'description': 'Valid',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }
        res = self.client.post('/api/v1/pool/', line_data, format='json')
        self.assertEqual(res.status_code, 201)
        line_id = res.data['id']

        # Org accessible only for persontype=2
        org_blocked = Organisation.objects.create(
            name='BlockedOrg2', business_id='7777777-7', active=True, send_active=True,
        )
        et_blocked = ExpenseType.objects.create(
            name='BlockedType2', type='O', active=True, persontype=2,
            multiplier=1.0, account='789', unit='EUR', organisation=org_blocked,
        )

        patch_data = {
            'description': 'Attempt to reassign',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': et_blocked.id,
            'basis': '10.00',
            'organisation': org_blocked.id,
        }
        res_patch = self.client.patch(f'/api/v1/pool/{line_id}/', patch_data, format='json')
        self.assertEqual(res_patch.status_code, 403)

    def test_pool_create_rejected_for_cross_organisation_expensetype(self):
        self._auth()

        org2 = Organisation.objects.create(
            name='Org2',
            business_id='6666666-6',
            active=True,
            send_active=True,
        )
        et2 = ExpenseType.objects.create(
            name='Type2',
            type='O',
            active=True,
            persontype=self.user.person.type,
            multiplier=1.0,
            account='456',
            unit='EUR',
            organisation=org2,
        )

        res = self.client.post('/api/v1/pool/', {
            'description': 'Cross org',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': et2.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }, format='json')

        self.assertEqual(res.status_code, 400)
        self.assertIn('expensetype', res.data)

    def test_pool_update_rejected_when_only_expensetype_becomes_inaccessible(self):
        self._auth()

        res = self.client.post('/api/v1/pool/', {
            'description': 'Valid',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }, format='json')
        self.assertEqual(res.status_code, 201)

        blocked = ExpenseType.objects.create(
            name='BlockedType',
            type='O',
            active=True,
            persontype=2,
            multiplier=1.0,
            account='789',
            unit='EUR',
            organisation=self.org,
        )

        res_patch = self.client.patch(
            f"/api/v1/pool/{res.data['id']}/",
            {'expensetype': blocked.id},
            format='json',
        )

        self.assertEqual(res_patch.status_code, 403)

    def test_pool_create_rejected_for_cross_organisation_accountdimension(self):
        self._auth()

        org2 = Organisation.objects.create(
            name='Org3',
            business_id='5555555-5',
            active=True,
            send_active=True,
        )
        accountdimension = AccountDimension.objects.create(
            name='Wrong org cost centre',
            code='100',
            organisation=org2,
        )

        res = self.client.post('/api/v1/pool/', {
            'description': 'Wrong dimension',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'accountdimension': accountdimension.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }, format='json')

        self.assertEqual(res.status_code, 400)
        self.assertIn('accountdimension', res.data)

    def test_pool_create_rejected_when_receipt_required(self):
        self._auth()
        self.et.requires_receipt = True
        self.et.save()

        res = self.client.post('/api/v1/pool/', {
            'description': 'Missing receipt',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': self.et.id,
            'basis': '10.00',
            'organisation': self.org.id,
        }, format='json')

        self.assertEqual(res.status_code, 400)
        self.assertIn('receipt', res.data)

    def test_pool_update_cannot_clear_required_receipt(self):
        self._auth()
        self.et.requires_receipt = True
        self.et.save()

        line = ExpenseLine.objects.create(
            description='Has receipt',
            begin_at='2026-03-28T12:00:00Z',
            expensetype=self.et,
            basis='10.00',
            organisation=self.org,
            user=self.user,
            receipt=SimpleUploadedFile('receipt.pdf', b'%PDF-1.4', content_type='application/pdf'),
        )

        res_patch = self.client.patch(
            f'/api/v1/pool/{line.id}/',
            {'receipt': None},
            format='json',
        )

        self.assertEqual(res_patch.status_code, 400)
        self.assertIn('receipt', res_patch.data)
        line.refresh_from_db()
        self.assertTrue(line.receipt)

    def test_pool_create_rejected_for_inactive_organisation(self):
        self._auth()
        inactive_org = Organisation.objects.create(
            name='InactiveOrg',
            business_id='4444444-4',
            active=False,
            send_active=True,
        )
        inactive_type = ExpenseType.objects.create(
            name='InactiveOrgType',
            type='O',
            active=True,
            persontype=self.user.person.type,
            multiplier=1.0,
            account='321',
            unit='EUR',
            organisation=inactive_org,
        )

        res = self.client.post('/api/v1/pool/', {
            'description': 'Inactive org',
            'begin_at': '2026-03-28T12:00:00Z',
            'expensetype': inactive_type.id,
            'basis': '10.00',
            'organisation': inactive_org.id,
        }, format='json')

        self.assertEqual(res.status_code, 400)
        self.assertIn('organisation', res.data)
