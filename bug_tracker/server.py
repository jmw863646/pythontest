from __future__ import absolute_import
import argparse
import falcon
import os

from .resources import IssueResource, IssuesResource
from .models import Repository


def _index_middleware(app):
    def handler(environ, start_response):
        if environ['PATH_INFO'] == '/':
            environ['PATH_INFO'] = '/index.html'
        return app(environ, start_response)
    return handler


def make_api(database_location, migrate_database=True):
    api = falcon.API()
    repo = Repository(database_location)
    if migrate_database:
        repo.migrate_database()
    api.add_route('/issues', IssuesResource(repo))
    api.add_route('/issues/{issue_id}', IssueResource(repo))
    static_dir = os.path.abspath(os.path.join(__file__, '..', '..', 'dist'))
    api.add_static_route('/', static_dir)
    return _index_middleware(api)


if __name__ == '__main__':
    from werkzeug.serving import make_server

    parser = argparse.ArgumentParser(description="Run a bug tracker server")
    parser.add_argument('--interface', default='0.0.0.0',
                        help="Interface to bind to")
    parser.add_argument('--port', default=8640,
                        help="Port to listen on")
    parser.add_argument('--database-location',
                        default=os.path.join(
                            os.path.dirname(__file__), '..', 'database.db'
                        ), help="Where to store the database")
    parser.add_argument('--no-database-migrations', action='store_true',
                        help="Do not perform database migrations")
    parser.add_argument('--clean', action='store_true',
                        help="Delete the database and start from clean")
    args = parser.parse_args()
    if args.clean:
        os.remove(args.database_location)

    api = make_api(args.database_location, not args.no_database_migrations)
    httpd = make_server(args.interface, args.port, api)
    print "Serving on {args.interface}:{args.port}".format(args=args)
    httpd.serve_forever()
