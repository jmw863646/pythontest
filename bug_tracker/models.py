from __future__ import absolute_import
import dateutil.parser
import sqlite3
from collections import namedtuple

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
            return make_issue(cursor.fetchone())
        finally:
            cursor.close()

    def create_issue(self, title, description):
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO issues(
                    title,
                    description
                ) VALUES('{}', '{}')""".format(title, description))
            cursor.execute("select last_insert_rowid()")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def update_issue(self, issue_id, **kwargs):
        cursor = self._conn.cursor()
        try:
            if 'title' in kwargs:
                cursor.execute(
                    """UPDATE issues SET title = '{}' WHERE id = {}"""
                    .format(kwargs['title'], issue_id)
                )
            if 'description' in kwargs:
                cursor.execute(
                    """UPDATE issues SET description = '{}' WHERE id = {}"""
                    .format(kwargs['description'], issue_id)
                )
            if 'closed' in kwargs:
                cursor.execute(
                    """UPDATE issues SET closed_datetime = '{}' WHERE id = {}"""
                    .format(kwargs['closed'].isoformat(), issue_id)
                )
        finally:
            cursor.close()
