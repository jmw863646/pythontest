from __future__ import absolute_import
import dateutil.parser
import sqlite3
import hashlib
import binascii
import re
from collections import namedtuple
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

Issue = namedtuple('Issue', ['id', 'title', 'description', 'opened', 'closed'])


def make_issue(row):
    id_, title, description, opened, closed = row
    if opened is not None:
        opened = dateutil.parser.parse(opened)
    if closed is not None:
        closed = dateutil.parser.parse(closed)
    return Issue(id_, title, description, opened, closed)


class IssueRepository(object):
    def __init__(self, conn):
        self._conn = conn

    def list_issues(self):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """SELECT
                    id,
                    title,
                    description,
                    opened_datetime,
                    closed_datetime
                    FROM issues
                    ORDER BY id""")
            return [make_issue(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def fetch_issue(self, issue_id):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """SELECT
                    id,
                    title,
                    description,
                    opened_datetime,
                    closed_datetime
                    FROM issues
                    WHERE id = {}""".format(issue_id))
            row = cursor.fetchone()
            return make_issue(row) if row != None else None
        finally:
            cursor.close()

    def create_issue(self, title, description):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO issues(
                    title,
                    description
                ) VALUES(?, ?)""", 
                (title, description)
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
        finally:
            cursor.close()

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

    def hashPassword(self, plain):
        """Hash a password so the database doesn't contain plaintext."""
        hashed = hashlib.pbkdf2_hmac('sha256', plain, self.salt, 100000)
        return binascii.hexlify(hashed)
