import tempfile
import types
from io import BytesIO, StringIO
from datetime import timezone as datetime_timezone
from http import HTTPStatus
from unittest.mock import patch
import PyPDF2
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


from .models import Expense, ExpenseEvent, ExpenseLine, ExpenseType, Organisation, Person, Workflow, WorkflowStep
from .helpers import render_to_pdf


FINNISH_IBAN = 'FI2112345600000785'


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestNewExpenseFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jacob.tester', email='jacob@partio.fi', password='top_secret', first_name='Jacob', last_name='Tester')
        self.person = Person.objects.get(user=self.user)
        self.person.type = 1
        self.person.address = 'Testitie 123'
        self.person.personno = '010101-123N'
        self.person.iban = FINNISH_IBAN
        self.person.save()
        self.organisation = Organisation.objects.create(
            name="Turun Hiihtäjät ry", business_id="y-1234", active=True, send_active=True)
        self.workflow = Workflow.objects.create(name="Default Workflow", organisation=self.organisation)

    def test_fail_login(self):
        response = self.client.post(
            "/accounts/login/", data={"username": "jacob.tester",
                                      "password": "not_working_password",
                                      })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, "Sisäänkirjautuminen epäonnistui."
        )

    def test_success_login(self):
        self.client.login(username='jacob.tester', password='top_secret',
                          name='Jacob Tester', address='Kotitie 112')
        response = self.client.get(
            "/expense/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(
            response, "Valitse organisaatiosi"
        )

    def test_user_can_edit_person(self):
        self.client.login(username='jacob.tester', password='top_secret')
        response = self.client.get(
            f"/personinfo/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Käyttäjätiedot'
        )

        postResponse = self.client.post(f"/personinfo/", data={
            "firstname": "Jaakop",
            "lastname": "Tester",
            "email": "jacob@partio.fi",
            "personno": "",
            "address": "",
            "phone": "",
            "iban": "",
            "swift_bic": "",
            "type": 1,
            "language": "fi-FI"
        })

        self.assertEqual(postResponse.status_code, HTTPStatus.OK)
        self.assertContains(
            postResponse, 'Profiilitiedot päivitetty'
        )

    def test_user_edit_validation_works(self):
        self.client.login(username='jacob.tester', password='top_secret')
        response = self.client.get(
            f"/personinfo/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Käyttäjätiedot'
        )

        postResponse = self.client.post(f"/personinfo/", data={
            "firstname": "Jaakop",
            "lastname": "Tester",
            "email": "",
            "personno": "",
            "address": "",
            "phone": "",
            "iban": "",
            "swift_bic": "",
            "type": 1,
            "language": "fi-FI"
        })

        self.assertEqual(postResponse.status_code, HTTPStatus.OK)
        self.assertContains(
            postResponse, 'Tarkista että kaikki tiedot ovat oikein.'
        )

    def test_user_create_expense_no_files(self):
        expenseType = ExpenseType.objects.create(
            name="km-korvaus",
            active=True,
            type="T",
            requires_receipt=False,
            multiplier=0.22,
            requires_endtime=False,
            requires_start_time=False,
            persontype=1,
            account="HiihtoTili",
            unit="km",
            organisation=self.organisation)

        self.client.login(username='jacob.tester', password='top_secret',
                          person=self.person)
        response = self.client.get(
            f"/expense/new/{self.organisation.id}")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Turun Hiihtäjät ry'
        )
        response = self.client.post(f"/expense/new/{self.organisation.id}", data={
            "preview": '0',
            "expenseform-user": self.user.id,
            "expenseform-organisation": self.organisation.id,
            "expenseform-workflow": self.workflow.id,
            "expenseform-name": "Jacob Tester",
            "expenseform-email": "jacob.tester@test.com",
            "expenseform-phone": "044123456",
            "expenseform-address": "Esimerkkitie 123",
            "expenseform-iban": FINNISH_IBAN,
            "expenseform-personno": "010101-123N",
            "expenseform-description": "description",
            "expenseform-memo": "memoteksti",
            "expenseform_EXPENSELINES-TOTAL_FORMS": 1,
            "expenseform_EXPENSELINES-INITIAL_FORMS": 0,
            "expenseform_EXPENSELINES-MIN_NUM_FORMS": 1,
            "expenseform_EXPENSELINES-MAX_NUM_FORMS": 1000,
            "expenseform_EXPENSELINES-0-basis": 100,
            "expenseform_EXPENSELINES-0-description": "Drove from Turku to helsinki",
            "expenseform_EXPENSELINES-0-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-__prefix__-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-0-sum": expenseType.multiplier*100,
            "expenseform_EXPENSELINES-0-begin_at_date": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at_time": "12.45",
            "expenseform_EXPENSELINES-0-ended_at_date": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at_time": "16.45",
            "expenseform_EXPENSELINES-0-expensetype_data": [expenseType]
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.client.get(response.url)
        self.assertContains(
            response, 'Kulutiedot tallennettu.'
        )

    def _create_expensetype(self, organisation, persontype=1):
        return ExpenseType.objects.create(
            name="Muut",
            active=True,
            type="O",
            requires_receipt=False,
            multiplier=1.0,
            requires_endtime=False,
            requires_start_time=False,
            persontype=persontype,
            account="123",
            unit="EUR",
            organisation=organisation,
        )

    def _create_pool_line(self, expensetype, organisation):
        return ExpenseLine.objects.create(
            description="Pool line",
            begin_at=timezone.now(),
            basis=10,
            expensetype=expensetype,
            user=self.user,
            organisation=organisation,
        )

    def _create_expense(self, description, status, personno='010101-123N'):
        return Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=status,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno=personno,
            description=description,
        )

    def _grant_organisation_permission(self):
        permission = Permission.objects.get(
            codename=f'change_organisation_{self.organisation.id}',
        )
        self.user.user_permissions.add(permission)

    def _valid_draft_submit_data(self, **overrides):
        data = {
            'submit_draft': '1',
            'name': 'Jacob Tester',
            'email': 'jacob.tester@test.com',
            'phone': '044123456',
            'address': 'Testikatu 1',
            'iban': FINNISH_IBAN,
            'swift_bic': 'NDEAFIHH',
            'personno': '010101-123N',
            'description': 'Draft description',
            'workflow': self.workflow.id,
        }
        data.update(overrides)
        return data

    def _valid_pdf_bytes(self):
        output = BytesIO()
        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(output)
        return output.getvalue()

    def test_pool_bundle_rejects_mixed_organisations(self):
        self.client.login(username='jacob.tester', password='top_secret')

        other_org = Organisation.objects.create(
            name='Other org',
            business_id='7654321-1',
            active=True,
            send_active=True,
        )

        et1 = self._create_expensetype(self.organisation)
        et2 = self._create_expensetype(other_org)

        line1 = self._create_pool_line(et1, self.organisation)
        line2 = self._create_pool_line(et2, other_org)

        response = self.client.post('/expense/pool/bundle/', data={
            'target_draft': 'new',
            'lines': [str(line1.id), str(line2.id)],
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, '/expense/pool/')
        self.assertEqual(Expense.objects.filter(user=self.user, status=-1).count(), 0)
        self.assertIsNone(ExpenseLine.objects.get(id=line1.id).expense_id)
        self.assertIsNone(ExpenseLine.objects.get(id=line2.id).expense_id)

    def test_pool_bundle_creates_draft_and_attaches_lines(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line1 = self._create_pool_line(et, self.organisation)
        line2 = self._create_pool_line(et, self.organisation)

        response = self.client.post('/expense/pool/bundle/', data={
            'target_draft': 'new',
            'lines': [str(line1.id), str(line2.id)],
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft = Expense.objects.get(user=self.user, status=-1)
        self.assertEqual(draft.organisation_id, self.organisation.id)
        self.assertEqual(draft.workflow_id, self.workflow.id)
        self.assertEqual(draft.name, 'Jacob Tester')
        self.assertEqual(draft.num, '')
        self.assertFalse(ExpenseEvent.objects.filter(expense=draft).exists())
        self.assertEqual(ExpenseLine.objects.filter(expense=draft).count(), 2)
        self.assertIn(f'/expense/draft/{draft.id}/', response.url)

    def test_user_create_expense_autoselects_only_workflow_when_missing(self):
        expenseType = self._create_expensetype(self.organisation)

        self.client.login(username='jacob.tester', password='top_secret')
        response = self.client.post(f"/expense/new/{self.organisation.id}", data={
            "preview": '0',
            "expenseform-user": self.user.id,
            "expenseform-organisation": self.organisation.id,
            "expenseform-name": "Jacob Tester",
            "expenseform-email": "jacob.tester@test.com",
            "expenseform-phone": "044123456",
            "expenseform-address": "Esimerkkitie 123",
            "expenseform-iban": FINNISH_IBAN,
            "expenseform-personno": "010101-123N",
            "expenseform-description": "description",
            "expenseform-memo": "memoteksti",
            "expenseform_EXPENSELINES-TOTAL_FORMS": 1,
            "expenseform_EXPENSELINES-INITIAL_FORMS": 0,
            "expenseform_EXPENSELINES-MIN_NUM_FORMS": 1,
            "expenseform_EXPENSELINES-MAX_NUM_FORMS": 1000,
            "expenseform_EXPENSELINES-0-basis": 100,
            "expenseform_EXPENSELINES-0-description": "Drove from Turku to Helsinki",
            "expenseform_EXPENSELINES-0-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-__prefix__-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-0-sum": expenseType.multiplier * 100,
            "expenseform_EXPENSELINES-0-begin_at_date": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at_time": "12.45",
            "expenseform_EXPENSELINES-0-ended_at_date": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at_time": "16.45",
            "expenseform_EXPENSELINES-0-expensetype_data": [expenseType]
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        created = Expense.objects.get(description='description')
        self.assertEqual(created.workflow_id, self.workflow.id)

    def test_pool_bundle_does_not_reuse_already_claimed_lines(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)

        first_response = self.client.post('/expense/pool/bundle/', data={
            'target_draft': 'new',
            'lines': [str(line.id)],
        })
        second_response = self.client.post('/expense/pool/bundle/', data={
            'target_draft': 'new',
            'lines': [str(line.id)],
        })

        self.assertEqual(first_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(second_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(second_response.url, '/expense/pool/')
        self.assertEqual(Expense.objects.filter(user=self.user, status=-1).count(), 1)
        line.refresh_from_db()
        self.assertIsNotNone(line.expense_id)

    def test_pool_receipt_download_requires_line_owner(self):
        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)
        line.receipt = SimpleUploadedFile('receipt.pdf', b'%PDF-1.4', content_type='application/pdf')
        line.save()

        other = User.objects.create_user(username='other.user', password='top_secret')

        self.client.login(username='other.user', password='top_secret')
        denied = self.client.get(f'/receipt/{line.id}')
        self.assertEqual(denied.status_code, HTTPStatus.FOUND)

        self.client.login(username='jacob.tester', password='top_secret')
        allowed = self.client.get(f'/receipt/{line.id}')
        self.assertEqual(allowed.status_code, HTTPStatus.OK)
        self.assertEqual(allowed['X-Accel-Redirect'], line.receipt.url)

    def test_draft_page_uses_authorized_receipt_links_and_separate_modal_form(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)
        line.receipt = SimpleUploadedFile('receipt.pdf', b'%PDF-1.4', content_type='application/pdf')
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            description='Draft description',
        )
        line.expense = draft
        line.save()

        response = self.client.get(f'/expense/draft/{draft.id}/')
        content = response.content.decode()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(f'/receipt/{line.id}', content)
        self.assertNotIn(line.receipt.url, content)
        self.assertLess(content.index('</form>'), content.index('id="poolModal"'))

    def test_draft_edit_prefills_whitespace_name_from_user(self):
        self.client.login(username='jacob.tester', password='top_secret')

        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name=' ',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            description='Draft description',
            num='1001',
        )

        response = self.client.get(f'/expense/draft/{draft.id}/')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'value="Jacob Tester"')

    def test_draft_submit_blocked_without_lines(self):
        self.client.login(username='jacob.tester', password='top_secret')

        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
            num='1001',
        )

        response = self.client.post(f'/expense/draft/{draft.id}/', data={
            'submit_draft': '1',
            'name': 'Jacob Tester',
            'email': 'jacob.tester@test.com',
            'phone': '044123456',
            'address': 'Testikatu 1',
            'iban': FINNISH_IBAN,
            'swift_bic': 'NDEAFIHH',
            'personno': '010101-123N',
            'description': 'Draft description',
            'workflow': self.workflow.id,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/expense/draft/{draft.id}/')
        draft.refresh_from_db()
        self.assertEqual(draft.status, -1)

    def test_draft_submit_blocked_with_invalid_email(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
            num='1004',
        )
        line = self._create_pool_line(et, self.organisation)
        line.expense = draft
        line.save()

        response = self.client.post(f'/expense/draft/{draft.id}/', data={
            'submit_draft': '1',
            'name': 'Jacob Tester',
            'email': 'not-an-email',
            'phone': '044123456',
            'address': 'Testikatu 1',
            'iban': FINNISH_IBAN,
            'swift_bic': 'NDEAFIHH',
            'personno': '010101-123N',
            'description': 'Draft description',
            'workflow': self.workflow.id,
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'field-email required error')
        self.assertContains(response, 'not-an-email')
        draft.refresh_from_db()
        self.assertEqual(draft.status, -1)

    def test_draft_submit_moves_status_and_saves_all_fields(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)

        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Old address 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Old desc',
            num='1002',
        )
        line.expense = draft
        line.save()

        response = self.client.post(f'/expense/draft/{draft.id}/', data={
            'submit_draft': '1',
            'name': 'Jacob Updated',
            'email': 'jacob.updated@test.com',
            'phone': '05012341234',
            'address': 'New address 5',
            'iban': FINNISH_IBAN,
            'swift_bic': 'NDEAFIHH',
            'personno': '010101-123N',
            'description': 'Updated draft description',
            'workflow': self.workflow.id,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 0)
        self.assertEqual(draft.name, 'Jacob Updated')
        self.assertEqual(draft.email, 'jacob.updated@test.com')
        self.assertEqual(draft.phone, '05012341234')
        self.assertEqual(draft.address, 'New address 5')
        self.assertEqual(draft.iban, FINNISH_IBAN)
        self.assertEqual(draft.swift_bic, 'NDEAFIHH')
        self.assertEqual(draft.personno, '010101-123N')
        self.assertEqual(draft.description, 'Updated draft description')
        self.assertEqual(response.url, f'/expense/{draft.id}')

    def test_draft_submit_assigns_number_and_created_from_pool_event(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
        )
        line.expense = draft
        line.save()

        self.assertEqual(draft.num, '')
        self.assertFalse(ExpenseEvent.objects.filter(expense=draft).exists())

        response = self.client.post(
            f'/expense/draft/{draft.id}/',
            data=self._valid_draft_submit_data(),
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 0)
        self.assertEqual(draft.num, '1001')
        event = ExpenseEvent.objects.get(expense=draft, type='R')
        self.assertEqual(event.notes, 'Created from pre-submitted entries')
        self.assertFalse(ExpenseEvent.objects.filter(expense=draft, type='E').exists())

    def test_draft_submit_autoselects_only_workflow_when_missing(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
        )
        line.expense = draft
        line.save()

        data = self._valid_draft_submit_data()
        data.pop('workflow')
        response = self.client.post(f'/expense/draft/{draft.id}/', data=data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 0)
        self.assertEqual(draft.workflow_id, self.workflow.id)

    def test_draft_submit_allows_omitted_optional_nullable_fields(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)

        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Old address 1',
            iban=FINNISH_IBAN,
            swift_bic=None,
            personno=None,
            description='Old desc',
            num='1005',
        )
        line.expense = draft
        line.save()

        response = self.client.post(f'/expense/draft/{draft.id}/', data={
            'submit_draft': '1',
            'name': 'Jacob Updated',
            'email': 'jacob.updated@test.com',
            'phone': '05012341234',
            'address': 'New address 5',
            'iban': FINNISH_IBAN,
            'description': 'Updated draft description',
            'workflow': self.workflow.id,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 0)
        self.assertIsNone(draft.swift_bic)
        self.assertIsNone(draft.personno)

    def test_draft_delete_returns_lines_to_pool(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
            num='1003',
        )
        line = self._create_pool_line(et, self.organisation)
        line.expense = draft
        line.save()

        response = self.client.post(f'/expense/draft/{draft.id}/delete/')

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, '/expense/')
        line.refresh_from_db()
        self.assertIsNone(line.expense_id)
        self.assertFalse(Expense.objects.filter(id=draft.id).exists())

    def test_draft_submit_uses_selected_workflow(self):
        self.client.login(username='jacob.tester', password='top_secret')

        et = self._create_expensetype(self.organisation)
        line = self._create_pool_line(et, self.organisation)
        other_workflow = Workflow.objects.create(name="Alternate Workflow", organisation=self.organisation)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
        )
        line.expense = draft
        line.save()

        response = self.client.post(
            f'/expense/draft/{draft.id}/',
            data=self._valid_draft_submit_data(workflow=other_workflow.id),
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        draft.refresh_from_db()
        self.assertEqual(draft.workflow_id, other_workflow.id)

    def test_workflow_user_cannot_view_or_act_on_draft(self):
        approver = User.objects.create_user(username='approver', password='top_secret')
        WorkflowStep.objects.create(workflow=self.workflow, type='C', users=approver)
        draft = Expense.objects.create(
            user=self.user,
            organisation=self.organisation,
            workflow=self.workflow,
            status=-1,
            name='Jacob Tester',
            email='jacob.tester@test.com',
            phone='044123456',
            address='Testikatu 1',
            iban=FINNISH_IBAN,
            swift_bic='NDEAFIHH',
            personno='010101-123N',
            description='Draft description',
        )

        self.client.login(username='approver', password='top_secret')

        detail_response = self.client.get(f'/expense/{draft.id}')
        addstep_response = self.client.get(f'/expense/{draft.id}/addstep?action=C')
        actable_response = self.client.get('/expense/act/')
        list_response = self.client.get('/expense/all/')

        self.assertEqual(detail_response.status_code, HTTPStatus.FOUND)
        self.assertEqual(addstep_response.status_code, HTTPStatus.FOUND)
        self.assertNotContains(actable_response, 'Draft description')
        self.assertNotContains(list_response, 'Draft description')

    def test_send_katre_excludes_drafts(self):
        draft = self._create_expense(
            description='Draft waiting for submission',
            status=-1,
        )
        Expense.objects.filter(id=draft.id).update(
            created_at=timezone.datetime(2026, 1, 1, tzinfo=datetime_timezone.utc),
        )

        out = StringIO()
        call_command('send_katre', stdout=out)

        self.assertIn('No katres to send.', out.getvalue())

    def test_annualarchive_excludes_drafts(self):
        self._grant_organisation_permission()
        self.client.login(username='jacob.tester', password='top_secret')

        self._create_expense('Submitted annual archive expense', status=0)
        self._create_expense('Draft annual archive expense', status=-1)

        response = self.client.get(
            f'/organisation/{self.organisation.id}/annualarchive/2026',
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Submitted annual archive expense')
        self.assertNotContains(response, 'Draft annual archive expense')

    def test_annualreport_excludes_drafts_from_tax_output(self):
        self._grant_organisation_permission()
        self.client.login(username='jacob.tester', password='top_secret')

        expense_type = self._create_expensetype(self.organisation)
        submitted = self._create_expense(
            'Submitted annual report expense',
            status=0,
            personno='010101-123N',
        )
        draft = self._create_expense(
            'Draft annual report expense',
            status=-1,
            personno='020202A1234',
        )
        ExpenseLine.objects.create(
            description='Submitted line',
            begin_at=timezone.now(),
            basis=10,
            expensetype=expense_type,
            expense=submitted,
            user=self.user,
            organisation=self.organisation,
        )
        ExpenseLine.objects.create(
            description='Draft line',
            begin_at=timezone.now(),
            basis=20,
            expensetype=expense_type,
            expense=draft,
            user=self.user,
            organisation=self.organisation,
        )

        response = self.client.get(
            f'/organisation/{self.organisation.id}/annualreport/2026',
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.content.decode()
        self.assertIn('010101-123N', content)
        self.assertNotIn('020202A1234', content)

    def test_pdf_generation_skips_receipt_with_unexpected_pdf_content(self):
        et = self._create_expensetype(self.organisation)
        expense = self._create_expense('Submitted PDF expense', status=0)
        line = ExpenseLine.objects.create(
            description='Bad receipt line',
            begin_at=timezone.now(),
            basis=10,
            expensetype=et,
            expense=expense,
            user=self.user,
            organisation=self.organisation,
        )
        line.receipt = SimpleUploadedFile('receipt.pdf', b'not a real pdf', content_type='application/pdf')
        line.save()

        fake_weasyprint = types.SimpleNamespace(
            HTML=lambda string: types.SimpleNamespace(write_pdf=lambda: self._valid_pdf_bytes())
        )
        with patch.dict('sys.modules', {'weasyprint': fake_weasyprint}):
            response = render_to_pdf(
                'expense_view_pdf.html',
                {'expense': expense, 'expenselines': [line], 'expenseevents': []},
                [line.receipt],
            )

        pdf = PyPDF2.PdfReader(BytesIO(response.content), strict=False)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(len(pdf.pages), 1)

    def test_user_create_expense_with_a_file(self):
        expenseType = ExpenseType.objects.create(
            name="km-korvaus",
            active=True,
            type="O",
            requires_receipt=True,
            multiplier=1.0,
            requires_endtime=False,
            requires_start_time=False,
            persontype=1,
            account="HiihtoTili",
            unit="EUR",
            organisation=self.organisation)

        self.client.login(username='jacob.tester', password='top_secret',
                          person=self.person)
        response = self.client.get(
            f"/expense/new/{self.organisation.id}")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Turun Hiihtäjät ry'
        )
        receipt = SimpleUploadedFile(
            "file.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(f"/expense/new/{self.organisation.id}", data={
            "preview": '0',
            "expenseform-user": self.user.id,
            "expenseform-organisation": self.organisation.id,
            "expenseform-workflow": self.workflow.id,
            "expenseform-name": "Jacob Tester",
            "expenseform-email": "jacob.tester@test.com",
            "expenseform-phone": "044123456",
            "expenseform-address": "Esimerkkitie 123",
            "expenseform-iban": FINNISH_IBAN,
            "expenseform-personno": "010101-123N",
            "expenseform-description": "description",
            "expenseform-memo": "memoteksti",
            "expenseform_EXPENSELINES-TOTAL_FORMS": 1,
            "expenseform_EXPENSELINES-INITIAL_FORMS": 0,
            "expenseform_EXPENSELINES-MIN_NUM_FORMS": 1,
            "expenseform_EXPENSELINES-MAX_NUM_FORMS": 1000,
            "expenseform_EXPENSELINES-0-basis": 100,
            "expenseform_EXPENSELINES-0-receipt": receipt,
            "expenseform_EXPENSELINES-0-description": "Drove from Turku to helsinki",
            "expenseform_EXPENSELINES-0-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-__prefix__-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-0-sum": expenseType.multiplier*100,
            "expenseform_EXPENSELINES-0-begin_at_date": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at_time": "12.45",
            "expenseform_EXPENSELINES-0-ended_at_date": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at_time": "16.45",
            "expenseform_EXPENSELINES-0-expensetype_data": [expenseType]
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.client.get(response.url)
        self.assertContains(
            response, 'Kulutiedot tallennettu.'
        )
