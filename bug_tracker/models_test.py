from __future__ import absolute_import
import datetime
import os
import tempfile

from unittest import TestCase, main
from .models import Repository
from .migrate_database import do_migrations


class IssueRepositoryTest(TestCase):
    def setUp(self):
        self.db_file = tempfile.mktemp()
        repo = Repository(self.db_file)
        repo.migrate_database()
        self.repo_conn = repo.open()
        self.instance = self.repo_conn.issues

    def tearDown(self):
        self.repo_conn.close()
        os.remove(self.db_file)

    def test_create_and_fetch(self):
        issue_id = self.instance.create_issue(
            'Test Issue', 'Test Issue Description')
        issue = self.instance.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.description, 'Test Issue Description')
        self.assertTrue(isinstance(issue.opened, datetime.datetime))
        self.assertEqual(issue.closed, None)

    def test_create_and_list(self):
        issue_id_1 = self.instance.create_issue(
            'Test Issue', 'Test Issue Description')
        issue_id_2 = self.instance.create_issue(
            'Test Issue 2', 'Test Issue Description 2')
        issues = self.instance.list_issues()
        self.assertEqual(issues[0].id, issue_id_1)
        self.assertEqual(issues[0].title, 'Test Issue')
        self.assertEqual(issues[0].description, 'Test Issue Description')
        self.assertEqual(issues[1].id, issue_id_2)
        self.assertEqual(issues[1].title, 'Test Issue 2')
        self.assertEqual(issues[1].description, 'Test Issue Description 2')

    def test_update(self):
        issue_id = self.instance.create_issue(
            'Test Issue', 'Test Issue Description')
        self.instance.update_issue(
            issue_id,
            title='New Title',
            description='New Description',
            closed=datetime.datetime(2020, 1, 1)
        )
        issue = self.instance.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'New Title')
        self.assertEqual(issue.description, 'New Description')
        self.assertEqual(issue.closed, datetime.datetime(2020, 1, 1))

if __name__ == '__main__':
    main()
