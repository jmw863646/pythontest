from __future__ import absolute_import
import os


def do_migrations(cursor):
    _ensure_migrations_table(cursor)
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    for migration in sorted(os.listdir(migrations_dir)):
        cursor.execute(
            'SELECT count(*) FROM migrations WHERE filename = ?', [migration]
        )
        if cursor.fetchone()[0] == 0:
            print "Running migration", migration
            with open(os.path.join(migrations_dir, migration)) as f:
                cursor.execute(f.read())
                cursor.execute(
                    'INSERT INTO migrations(filename) VALUES(?)', [migration]
                )


def _ensure_migrations_table(cursor):
    cursor.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='migrations'"
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute("""CREATE TABLE migrations(
            filename VARCHAR(255) PRIMARY KEY
        )""")

if __name__ == '__main__':
    import sqlite3
    from . import DATABASE_LOCATION
    with sqlite3.connect(DATABASE_LOCATION) as db:
        cursor = db.cursor()
        try:
            do_migrations(cursor)
        finally:
            cursor.close()
