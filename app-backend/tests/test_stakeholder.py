from sqlalchemy.exc import OperationalError, ProgrammingError

from unittest import mock
from app import app_object

import app
import unittest


class MockDatabaseModelResult:

    def __init__(self):
        self.results = []

    def all(self):
        return self.results


def _db_session_add_side_effect(project):
    project.id = 1
    return project


def _raise_operational_error(*args, **kwargs):
    raise OperationalError('', {}, '')


def _raise_programming_error(*args, **kwargs):
    raise ProgrammingError('', {}, '')


def _raise_type_error(*args, **kwargs):
    raise TypeError()


class StakeholderCreationTestCase(unittest.TestCase):

    def setUp(self):
        self.tester = app_object.test_client(self)
        self.project_id = 5
        self.name = "Bernd"
        self.company = "Ulf GmbH"
        self.role = "rollig"
        self.attitude = "positive"

    @mock.patch("app.db.session.add")
    @mock.patch("app.db.session.commit")
    def test_create_stakeholder(self, mock_db_session_commit, mock_db_session_add):
        mock_db_session_add.side_effect = _db_session_add_side_effect
        stake_holder = app.stakeholder.create_stakeholder(self.project_id, self.name, self.company, self.role,
                                                          self.attitude)

        self.assertEqual(stake_holder.name, self.name)
        self.assertEqual(stake_holder.company, self.company)
        self.assertEqual(stake_holder.role, self.role)
        self.assertEqual(stake_holder.attitude, self.attitude)
        self.assertEqual(stake_holder.id, 1)

        assert mock_db_session_add.called
        assert mock_db_session_commit.called

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint(self, mock_create_stakeholder):
        mock_create_stakeholder.return_value = app.stakeholder.Stakeholder(project_id=1, name=self.name,
                                                                           company=self.company, role=self.role,
                                                                           attitude=self.attitude)
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={
            'name': self.name,
            'company': self.company,
            'role': self.role,
            'attitude': self.attitude,
        })

        self.assertEqual(response.status_code, 201)
        self.assertIn(member='Location', container=response.headers)

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_missing_name(self, mock_create_stakeholder):
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={
            'company': self.company
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data, b'Missing data: name')

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_missing_description(self, mock_create_stakeholder):
        mock_create_stakeholder.return_value = app.stakeholder.Stakeholder(id=1, name=self.name, project_id=1)
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={
            'name': self.name
        })

        self.assertEqual(response.status_code, 201)
        self.assertIn(member='Location', container=response.headers)

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_empty_json(self, mock_create_stakeholder):
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data, b'Missing data: name')

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_no_json(self, mock_create_stakeholder):
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', data=dict(
            name=self.name,
            company=self.company
        ))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, b'Format: application/json expected')

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_no_database(self, mock_create_stakeholder):
        mock_create_stakeholder.side_effect = _raise_operational_error
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={
            'name': self.name,
            'company': self.company,
            'role': self.role,
            'attitude': self.attitude,
        })

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.is_json, True)
        self.assertEqual(response.json, 'Could not find stakeholder')

    @mock.patch("app.stakeholder.create_stakeholder")
    def test_create_stakeholder_endpoint_no_table(self, mock_create_stakeholder):
        mock_create_stakeholder.side_effect = _raise_programming_error
        response = self.tester.post(f'/project/{self.project_id}/stakeholder', json={
            'name': self.name,
            'company': self.company,
            'role': self.role,
            'attitude': self.attitude,
        })

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.is_json, True)
        self.assertEqual(response.json, 'Could not find stakeholder')


class StakeHolderListRetrievalTestCase(unittest.TestCase):

    def setUp(self):
        self.tester = app_object.test_client(self)
        self.mock_stakeholder = app.stakeholder.Stakeholder(id=1, project_id=1, name="Stakeholder 1",
                                                            company="Wichtig GmbH",
                                                            role="Chief of Wichtigkeit",
                                                            attitude="alles muss man selber machen")

    @mock.patch("app.stakeholder.Stakeholder")
    def test_retrieve_stakeholder_list(self, mock_stakeholder_model):
        mock_stakeholder_result = MockDatabaseModelResult()
        mock_stakeholder_result.results = [self.mock_stakeholder]

        mock_stakeholder_model.query.filter_by.return_value = mock_stakeholder_result
        stakeholder_list = app.stakeholder.list_stakeholders(1)

        self.assertEqual(len(stakeholder_list), 1)
        self.assertEqual(stakeholder_list, [self.mock_stakeholder])

    @mock.patch("app.stakeholder.Stakeholder")
    def test_retrieve_stakeholder_list_empty(self, mock_stakeholder_model):
        mock_stakeholder_result = MockDatabaseModelResult()
        mock_stakeholder_result.results = []

        mock_stakeholder_model.query.filter_by.return_value = mock_stakeholder_result
        stakeholder_list = app.stakeholder.list_stakeholders(100000)

        self.assertEqual(stakeholder_list, [])

    @mock.patch("app.stakeholder.list_stakeholders")
    def test_retrieve_stakeholder_list_endpoint(self, mock_list_stakeholders):
        mock_list_stakeholders.return_value = [self.mock_stakeholder]
        response = self.tester.get('/project/1/stakeholder', content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.is_json, True)
        self.assertEqual(response.json, [self.mock_stakeholder.to_json()])

    @mock.patch("app.stakeholder.list_stakeholders")
    def test_retrieve_stakeholder_list_endpoint_no_database(self, mock_list_stakeholders):
        mock_list_stakeholders.side_effect = _raise_operational_error
        response = self.tester.get('/project/1/stakeholder', content_type='application/json')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.is_json, True)
        self.assertEqual(response.json, 'Could not find stakeholders')

    @mock.patch("app.stakeholder.list_stakeholders")
    def test_retrieve_stakeholder_list_endpoint_no_table(self, mock_list_stakeholders):
        mock_list_stakeholders.side_effect = _raise_programming_error
        response = self.tester.get('/project/1/stakeholder', content_type='application/json')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.is_json, True)
        self.assertEqual(response.json, 'Could not find stakeholders')


if __name__ == '__main__':
    unittest.main()
