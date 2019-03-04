from __future__ import absolute_import
import dateutil.parser
import sqlite3
import hashlib
import binascii
import re
from collections import namedtuple
from bisect import bisect_left, bisect_right
from uuid import uuid4

from .migrate_database import do_migrations


class Repository(object):
    def __init__(self, database_location):
        self._database_location = database_location

    def open(self):
        return RepositoryConnection(sqlite3.connect(self._database_location))

    def migrate_database(self):
        with sqlite3.connect(self._database_location) as conn:
            cursor = conn.cursor()
            try:
                do_migrations(cursor)
            finally:
                cursor.close()

class RepositoryConnection(object):
    def __init__(self, conn):
        self._conn = conn
        self.issues = IssueRepository(self._conn)
        self.users = UserRepository(self._conn)

    def __enter__(self):
        return self

    def __exit__(self, exc, type_, tb):
        try:
            self._conn.__exit__(exc, type_, tb)
        finally:
            self._conn.close()

    def close(self):
        self._conn.close()

Issue = namedtuple('Issue', ['id', 'title', 'description', 'opened', 'closed', 'createdBy', 'assignedTo' ])

def _parseDatetime(datetimeStr):
    if datetimeStr is None:
        return None
    return dateutil.parser.parse(datetimeStr)

def make_issue(row):
    id_, title, description, opened, closed, createdBy, assignedTo = row
    opened = _parseDatetime(opened)
    closed = _parseDatetime(closed)
    return Issue(id_, title, description, opened, closed, createdBy, assignedTo)

class IssueRepository(object):
    def __init__(self, conn):
        self._conn = conn

    def list_issues(self):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """SELECT
                        i.id,
                        i.title,
                        i.description,
                        i.opened_datetime,
                        i.closed_datetime,
                        u1.email,
                        u2.email
                    FROM 
                        issues i
                        JOIN users u1 ON i.creatorId = u1.id
                        LEFT JOIN users u2 on i.assigneeId = u2.id 
                    ORDER BY i.id""")
            return [make_issue(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def fetch_issue(self, issue_id):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """SELECT
                        i.id,
                        i.title,
                        i.description,
                        i.opened_datetime,
                        i.closed_datetime,
                        u1.email,
                        u2.email
                    FROM 
                        issues i
                        JOIN users u1 ON i.creatorId = u1.id
                        LEFT JOIN users u2 on i.assigneeId = u2.id 
                    WHERE 
                        i.id = ?
                    ORDER BY i.id""",
                    (issue_id, ))
            row = cursor.fetchone()
            return make_issue(row) if row != None else None
        finally:
            cursor.close()

    def create_issue(self, title, description, creatorId):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO issues(
                    title,
                    description,
                    creatorId
                ) VALUES(?, ?, ?)""", 
                (title, description, creatorId)
            )
            cursor.execute("select last_insert_rowid()")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def update_issue(self, issue_id, **kwargs):
        cursor = self._conn.cursor()
        try:
            if 'title' in kwargs:
                cursor.execute(
                    """UPDATE issues SET title = ? WHERE id = ?""",
                    (kwargs['title'], issue_id)
                )
            if 'description' in kwargs:
                cursor.execute(
                    """UPDATE issues SET description = ? WHERE id = ?""",
                    (kwargs['description'], issue_id)
                )

            # The field 'closedFlag' is a Boolean indicating whether the issue is closed. If it is now closed then let the database timestamp
            # the closure as it did the creation.
            if 'closedFlag' in kwargs:
                if kwargs['closedFlag']:
                    cursor.execute(
                        """UPDATE issues 
                            SET closed_datetime = DATETIME('now') 
                            WHERE id = {} AND closed_datetime IS NULL""".format(issue_id))
                else:
                    cursor.execute("UPDATE issues SET closed_datetime = NULL WHERE id = {}".format(issue_id))

            if 'assigneeId' in kwargs:
                # Negative assignee id implies issue is not assigned to a user
                assigneeId = int(kwargs['assigneeId'])
                if assigneeId < 0:
                    cursor.execute(
                        """UPDATE issues SET assigneeId = NULL WHERE id = ?""",
                        (issue_id, ))
                else:
                    cursor.execute(
                        """UPDATE issues SET assigneeId = ? WHERE id = ?""",
                        (kwargs['assigneeId'], issue_id))

        finally:
            cursor.close()

    def statistics(self):
        """Gather statistics for the dashboard."""
        cursor = self._conn.cursor()
        try:
            # Never cache the open number of issues as it's relatively cheap to calculate (providing the table isn't too big)
            cursor.execute('SELECT COUNT(*) FROM issues WHERE closed_datetime IS NULL')
            currentOpenNow = cursor.fetchone()[0]

            # Never cache the number of issues closed in the last week as it's relatively cheap to calculate (providing the 
            # table isn't too big)
            cursor.execute(
                """SELECT COUNT(*) 
                    FROM issues
                    WHERE closed_datetime > DATE('now', '-7 days')""")
            closedInLastWeek = cursor.fetchone()[0]

            # The maximum number of open issues there's every been at one time is more complex so we'll cache it and use 
            # (database) triggers on insert / update to wipe the cached value
            cursor.execute("SELECT value FROM cached WHERE name = 'max_open'")
            row = cursor.fetchone()
            if row is not None:
                maxOpen = row[0]
            else:
                maxOpen = 0

                # There is no cached value so we'll recalculate it
                cursor.execute(
                    """SELECT 
                        opened_datetime,
                        closed_datetime
                        FROM 
                            issues
                        ORDER BY
                            opened_datetime,
                            closed_datetime
                    """)

                # Issues that are currently open and have a closing date; only closing dates are stored and in increasing
                # order.
                willCloseIssues = []

                # The count of issues that are opened but never closed
                neverCloseIssueCount = 0

                # Iterate throw the issues
                row = cursor.fetchone()
                while row is not None:
                    currentOpened = _parseDatetime(row[0])
                    currentClosed = _parseDatetime(row[1])
                    row = cursor.fetchone()
 
                    # Have any open issues closed since this one opened? Look for the first closed date strictly after
                    # this opened date. Retain those elements
                    afterIndex = bisect_right(willCloseIssues, currentOpened)
                    willCloseIssues = willCloseIssues[afterIndex:]

                    # Is the current issue going to close at some point?
                    if currentClosed is None:
                        neverCloseIssueCount += 1
                    else:
                        # Insert the new closed date in order
                        insertAt = bisect_left(willCloseIssues, currentClosed)
                        willCloseIssues.insert(insertAt, currentClosed)

                    # Is this the maximum number of open issues?
                    currentOpen = len(willCloseIssues) + neverCloseIssueCount
                    maxOpen = max(currentOpen, maxOpen)

                try:
                    cursor.execute("INSERT INTO cached VALUES('max_open', ?)", (maxOpen, ))
                except sqlite3.DatabaseError:
                    # Ignore any attempt to insert duplicate key
                    pass

            return {
                'maxOpen': maxOpen, 
                'currentOpen': currentOpenNow, 
                'closedInLastWeek': closedInLastWeek
            }

        finally:
            cursor.close()

User = namedtuple('User', ['id', 'email' ])

def _makeUser(row):
    """Make a 'User' tuple from a returned row."""
    id_, email = row
    return User(id_, email)

class UserRepository:
    """Support for registering, logging in, logging out and authentication."""

    def __init__(self, conn):
        self._conn = conn
        self.sessionTimeout = '+1 hour'
        # This would be better coming from a configuration file
        self.salt = '\xc1\x9c\x0ei\xb0P\xe5ma\xe0\xa4\xdd0\xa5X\xce'
    
    def register(self, email, password):
        """Register a new user"""

        # Check the email address looks valid
        if not re.search('^[^@]+@([^@.]+\\.)*[^@.]+$', email):
            return "Email address '{}' is invalid".format(email)

        hashedPassword = self.hashPassword(password)
        cursor = self._conn.cursor()
        try: 
            cursor.execute(
                """INSERT INTO users(
                    email,
                    password
                ) VALUES(?, ?)""", 
                (email, hashedPassword)
            )
        except sqlite3.IntegrityError:
            return "User '{}' already exists".format(email)
        finally:
            cursor.close()
        return None

    def createSessionId(self, email, password):
        """Given a user's detail return a user and session id, or None if failed to authenticate."""
        hashedPassword = self.hashPassword(password)
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                'SELECT id FROM users WHERE email = ? AND password = ?',
                (email, hashedPassword))
            row = cursor.fetchone()
            if row is None:
                return None
            id = row[0]

            sessionId = uuid4().hex
            cursor.execute(
                "UPDATE users SET uuid = ?, expiresAt = DATETIME('now', '{}') WHERE id = ?".format(self.sessionTimeout),
                (sessionId, id))
            return (id, sessionId)

        finally:
            cursor.close()

    def revokeSessionId(self, id):
        """Drop the session id for a particular user (effetively logging them out)."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                'UPDATE users SET uuid = NULL, expiresAt = NULL WHERE id = ?', 
                (id, ))
        finally:
            cursor.close()

    def authenticateSessionId(self, id, sessionId):
        """Authenticate a user by checking the accompanying session id."""
        if id is None or sessionId is None:
            return False

        cursor = self._conn.cursor()
        try:
            # Does the session id match the one we have for this user? and is it still valid?
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE id = ? AND uuid = ? AND expiresAt > DATETIME('now')",
                (id, sessionId))
            count = cursor.fetchone()[0]
            if count == 0:
                return False

            # Extend the expiry of the session id
            cursor.execute(
                "UPDATE users SET expiresAt = DATETIME('now', '{}') WHERE id = ?".format(self.sessionTimeout),
                (id, ))
            return True

        finally:
            cursor.close()

    def listUsers(self):
        """Generate a list of all users and their ids."""

        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """SELECT
                        id,
                        email
                    FROM 
                        users
                    ORDER BY 
                        email""")
            return [_makeUser(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def hashPassword(self, plain):
        """Hash a password so the database doesn't contain plaintext."""
        hashed = hashlib.pbkdf2_hmac('sha256', plain, self.salt, 100000)
        return binascii.hexlify(hashed)
