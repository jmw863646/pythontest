from __future__ import absolute_import
from datetime import datetime, date
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
        # Register a user to use as creator
        self.users.register('justin@justinware.me.uk', 'garfield')

        issue_id = self.repo.create_issue(
            'Test Issue', 'Test Issue Description', 1)
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.description, 'Test Issue Description')
        self.assertTrue(isinstance(issue.opened, datetime))
        self.assertEqual(issue.closed, None)

        # Additional tests with apostrophes
        issue_id_2 = self.repo.create_issue(
            "It's a wonderful life", "Especially when I've used the appropriate function", 1)
        issue = self.repo.fetch_issue(issue_id_2)
        self.assertEqual(issue.id, issue_id_2)
        self.assertEqual(issue.title, "It's a wonderful life")
        self.assertEqual(issue.description, "Especially when I've used the appropriate function")
        self.assertTrue(isinstance(issue.opened, datetime))
        self.assertEqual(issue.closed, None)

    def test_create_and_list(self):
        # Register some users
        self.users.register('justin@justinware.me.uk', 'garfield')
        self.users.register('fred@bloggs.com', 'garfield')

        issue_id_1 = self.repo.create_issue(
            'Test Issue', 'Test Issue Description', 1)
        issue_id_2 = self.repo.create_issue(
            'Test Issue 2', 'Test Issue Description 2', 2)
        issues = self.repo.list_issues()
        self.assertEqual(issues[0].id, issue_id_1)
        self.assertEqual(issues[0].title, 'Test Issue')
        self.assertEqual(issues[0].description, 'Test Issue Description')
        self.assertEqual(issues[0].createdBy, 'justin@justinware.me.uk')
        self.assertEqual(issues[1].id, issue_id_2)
        self.assertEqual(issues[1].title, 'Test Issue 2')
        self.assertEqual(issues[1].description, 'Test Issue Description 2')
        self.assertEqual(issues[1].createdBy, 'fred@bloggs.com')

    def test_update(self):
        # Register some users
        self.users.register('justin@justinware.me.uk', 'garfield')
        self.users.register('fred@bloggs.com', 'garfield')

        issue_id = self.repo.create_issue(
            'Test Issue', 'Test Issue Description', 1)
        issue = self.repo.fetch_issue(issue_id)
        self.assertIsNone(issue.closed)
        self.repo.update_issue(
            issue_id,
            title='New Title',
            description='New Description',
            closedFlag=True,
            assigneeId=2
        )
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'New Title')
        self.assertEqual(issue.description, 'New Description')
        self.assertIsNotNone(issue.closed)
        self.assertEqual(issue.createdBy, 'justin@justinware.me.uk')
        self.assertEqual(issue.assignedTo, 'fred@bloggs.com')
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
            closedFlag=False, # No longer closed
            assigneeId=-1 # No longer assigned
        )
        issue = self.repo.fetch_issue(issue_id)
        self.assertEqual(issue.id, issue_id)
        self.assertEqual(issue.title, 'Old Title\'s Revenge')
        self.assertEqual(issue.description, 'This time it\'s personal!')
        self.assertIsNone(issue.closed)
        self.assertIsNone(issue.assignedTo, 'No longer assigned to anyone')

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

        self.users.register('zebedee.fisherman@galilee.holy.land', 'Boing!')
        self.users.register('adam_and_eve@eden.garden', 'Arrgghh, snake!')

        userList = self.users.listUsers()
        self.assertEqual(userList[0].id, 4)
        self.assertEqual(userList[0].email, 'adam_and_eve@eden.garden')
        self.assertEqual(userList[1].id, 1)
        self.assertEqual(userList[1].email, 'justin@justinware.me.uk'),
        self.assertEqual(userList[2].id, 2)
        self.assertEqual(userList[2].email, 'wibble@wobble'),
        self.assertEqual(userList[3].id, 3)
        self.assertEqual(userList[3].email, 'zebedee.fisherman@galilee.holy.land'),
    
    def test_statistics(self):
        # Directly populate the data as we want fine control over the datetimes
        with self.repo_conn._conn as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users(id, email, password) 
                VALUES (1, 'justin@justinware.me.uk', 'garfield')""")
            
            issues = [
                ( 'an issue 1', 'blah blah blah', datetime(2019,  1, 15, 12,  0,  0), datetime(2019,  1, 25, 10,  0,  0) ),
                ( 'an issue 2', 'blah blah blah', datetime(2019,  1,  5, 12,  0,  0), datetime(2019,  2,  5, 10,  0,  0) ),
                ( 'an issue 3', 'blah blah blah', datetime(2019,  1, 10, 12,  0,  0),                               None ),
                ( 'an issue 4', 'blah blah blah', datetime(2019,  1, 27, 13,  0,  0), datetime(2019,  1, 28, 17,  0,  0) ),
                ( 'an issue 5', 'blah blah blah', datetime(2019,  1, 20, 12,  0,  0), datetime(2019,  1, 28, 10, 30,  0) ),
                ( 'an issue 6', 'blah blah blah', datetime(2019,  1, 27,  9, 45,  0),                               None ),
                ( 'an issue 7', 'blah blah blah', datetime(2019,  1, 27, 14,  5,  0), datetime(2019,  1, 28, 13, 15,  0) ),
                ( 'an issue 8', 'blah blah blah', datetime(2019,  2,  1, 11, 30,  0),                               None )
            ]

            # Above test data considers today to be '2019-02-07' (arbitrary choice) but to do closed in last week we'd like it to
            # be actual today.
            offset = date.today() - date(2019, 2, 7)
            for i in range(len(issues)):
                issues[i] = (
                    issues[i][0], 
                    issues[i][1],
                    issues[i][2] + offset, 
                    (issues[i][3] + offset) if issues[i][3] is not None else None
                )

            cursor.executemany("""
                INSERT INTO issues(title, description, opened_datetime, closed_datetime, creatorId)
                VALUES (?,?,?,?,1)""", issues)
            conn.commit()

            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 6, 'currentOpen': 3, 'closedInLastWeek': 1 }, 'Calculated fresh')
            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 6, 'currentOpen': 3, 'closedInLastWeek': 1 }, 'maxOpen is cached')

            # Make an issue close recently
            conn.execute("""
                UPDATE issues SET closed_datetime = ? WHERE title = 'an issue 8'""",
                (datetime(2019, 2, 2, 8, 0, 0) + offset,))
            conn.commit()
            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 6, 'currentOpen': 2, 'closedInLastWeek': 2 }, 'Another issue closed last week')

            # Have an issue close much earlier so that max open at one time changes
            conn.execute("""
                UPDATE issues SET closed_datetime = ? WHERE title = 'an issue 2'""",
                (datetime(2019, 1, 12, 8, 0, 0) + offset,))
            conn.commit()
            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 5, 'currentOpen': 2, 'closedInLastWeek': 1 }, 'Less issues open at same time')
            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 5, 'currentOpen': 2, 'closedInLastWeek': 1 }, 'Repeat using cached')

            # Insert more issues which will clear cached values and force a recalculation
            issues = [
                ( 'an issue 9',  'blah blah blah', datetime(2019,  2,  1, 12, 30,  0), datetime(2019, 2, 2, 18, 0, 0) ),
                ( 'an issue 10', 'blah blah blah', datetime(2019,  2,  1, 13, 30,  0), datetime(2019, 2, 2, 15, 0, 0) ),
                ( 'an issue 11', 'blah blah blah', datetime(2019,  2,  1, 14, 30,  0), datetime(2019, 2, 2, 14, 0, 0) ),
                ( 'an issue 12', 'blah blah blah', datetime(2019,  2,  1, 15, 30,  0), datetime(2019, 2, 2, 13, 0, 0) ),
                ( 'an issue 13', 'blah blah blah', datetime(2019,  2,  1, 16, 30,  0), datetime(2019, 2, 2, 12, 0, 0) ),
                ( 'an issue 14', 'blah blah blah', datetime(2019,  2,  1, 17, 30,  0), datetime(2019, 2, 2, 11, 0, 0) ),
                ( 'an issue 15', 'blah blah blah', datetime(2019,  2,  1, 18, 30,  0), datetime(2019, 2, 2, 10, 0, 0) )
            ]

            # Adjust for current date
            for i in range(len(issues)):
                issues[i] = (
                    issues[i][0], 
                    issues[i][1],
                    issues[i][2] + offset, 
                    (issues[i][3] + offset) if issues[i][3] is not None else None
                )

            cursor.executemany("""
                INSERT INTO issues(title, description, opened_datetime, closed_datetime, creatorId)
                VALUES (?,?,?,?,1)""", issues)
            conn.commit()

            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 10, 'currentOpen': 2, 'closedInLastWeek': 8 }, 'More issues open at same time')
            statistics = self.repo.statistics()
            self.assertEquals(statistics, { 'maxOpen': 10, 'currentOpen': 2, 'closedInLastWeek': 8 }, 'Repeat using cached')

if __name__ == '__main__':
    main()
