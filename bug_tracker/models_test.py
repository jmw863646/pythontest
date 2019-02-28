from __future__ import absolute_import
import datetime
import time
import os
import tempfile
from uuid import uuid4

from unittest import TestCase, main
from .models import Repository
from .migrate_database import do_migrations


class IssueRepositoryTest(TestCase):
    def setUp(self):
        self.db_file = tempfile.mktemp()
        repo = Repository(self.db_file)
        repo.migrate_database()
        self.repo_conn = repo.open()
        self.repo = self.repo_conn.issues
        self.users = self.repo_conn.users

    def tearDown(self):
        self.repo_conn.close()
        os.remove(self.db_file)

    def test_create_and_fetch(self):
        issue_id = self.repo.create_issue(
            'Test Issue', 'Test Issue Description')
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.description, 'Test Issue Description')
        self.assertTrue(isinstance(issue.opened, datetime.datetime))
        self.assertEqual(issue.closed, None)

        # Additional tests with apostrophes
        issue_id_2 = self.repo.create_issue(
            "It's a wonderful life", "Especially when I've used the appropriate function")
        issue = self.repo.fetch_issue(issue_id_2)
        self.assertEqual(issue.id, issue_id_2)
        self.assertEqual(issue.title, "It's a wonderful life")
        self.assertEqual(issue.description, "Especially when I've used the appropriate function")
        self.assertTrue(isinstance(issue.opened, datetime.datetime))
        self.assertEqual(issue.closed, None)

    def test_create_and_list(self):
        issue_id_1 = self.repo.create_issue(
            'Test Issue', 'Test Issue Description')
        issue_id_2 = self.repo.create_issue(
            'Test Issue 2', 'Test Issue Description 2')
        issues = self.repo.list_issues()
        self.assertEqual(issues[0].id, issue_id_1)
        self.assertEqual(issues[0].title, 'Test Issue')
        self.assertEqual(issues[0].description, 'Test Issue Description')
        self.assertEqual(issues[1].id, issue_id_2)
        self.assertEqual(issues[1].title, 'Test Issue 2')
        self.assertEqual(issues[1].description, 'Test Issue Description 2')

    def test_update(self):
        issue_id = self.repo.create_issue(
            'Test Issue', 'Test Issue Description')
        issue = self.repo.fetch_issue(issue_id)
        self.assertIsNone(issue.closed)
        self.repo.update_issue(
            issue_id,
            title='New Title',
            description='New Description',
            closedFlag=True
        )
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'New Title')
        self.assertEqual(issue.description, 'New Description')
        self.assertIsNotNone(issue.closed)
        previousClosed = issue.closed

        # Closing an already closed issue should not update the timestamp
        time.sleep(2)
        self.repo.update_issue(
            issue_id,
            closedFlag=True
        )
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.closed, previousClosed)

        # Repeat but with apostrophes
        self.repo.update_issue(
            issue_id,
            title='Old Title\'s Revenge',
            description='This time it\'s personal!',
            closedFlag=False
        )
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'Old Title\'s Revenge')
        self.assertEqual(issue.description, 'This time it\'s personal!')
        self.assertIsNone(issue.closed)

    def test_users(self):
        self.assertIsNone(self.users.register('justin@justinware.me.uk', 'garfield'))
        error = self.users.register('justin@justinware.me.uk', 'pookie')
        self.assertEqual(error, "User 'justin@justinware.me.uk' already exists")
        error = self.users.register('wibble', 'pookie')
        self.assertEqual(error, "Email address 'wibble' is invalid")
        error = self.users.register('@nowhere', 'pookie')
        self.assertEqual(error, "Email address '@nowhere' is invalid")
        error = self.users.register('someone@', 'pookie')
        self.assertEqual(error, "Email address 'someone@' is invalid")
        error = self.users.register('someone@nowhere.', 'pookie')
        self.assertEqual(error, "Email address 'someone@nowhere.' is invalid")
        error = self.users.register('someone@nowhere.me.', 'pookie')
        self.assertEqual(error, "Email address 'someone@nowhere.me.' is invalid")
        self.assertIsNone(self.users.register('wibble@wobble', 'pookie'))

        self.assertIsNone(self.users.createSessionId('fred@dibnah.com', 'ayup'))
        self.assertIsNone(self.users.createSessionId('justin@justinware.me.uk', 'pookie'))
        id, sessionId = self.users.createSessionId('justin@justinware.me.uk', 'garfield')
        self.assertEqual(id, 1, 'Should be unity as database is freshly created')
        self.assertEqual(len(sessionId), 32, 'Not the expected length')

        self.assertFalse(self.users.authenticateSessionId(id, None))
        self.assertFalse(self.users.authenticateSessionId(None, sessionId))
        self.assertTrue(self.users.authenticateSessionId(id, sessionId))
        wrongSessionId = uuid4().hex
        self.assertFalse(self.users.authenticateSessionId(id, wrongSessionId))

        with self.repo_conn._conn as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET expiresAt = DATETIME('now', '-1 day') WHERE id = ?", (id, ))
            finally:
                cursor.close()
        self.assertFalse(self.users.authenticateSessionId(id, sessionId), 'Session has expired on the server side')

        id, sessionId = self.users.createSessionId('justin@justinware.me.uk', 'garfield')
        self.assertTrue(self.users.authenticateSessionId(id, sessionId))
        self.users.revokeSessionId(id)
        self.assertFalse(self.users.authenticateSessionId(id, sessionId))

if __name__ == '__main__':
    main()
