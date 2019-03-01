from __future__ import absolute_import
import falcon
from pytz import timezone
import pytz

def _to_local(dt, clientTZ):
    dtWithTZ = dt.replace(tzinfo = pytz.utc)
    dtLocalWithTZ = dtWithTZ.astimezone(clientTZ)
    dtLocal = dtLocalWithTZ.replace(tzinfo = None)
    return dtLocal.isoformat()

def _issue_to_json(issue, clientTZ):
    return {
        'id': issue.id,
        'title': issue.title,
        'description': issue.description,
        'opened': _to_local(issue.opened, clientTZ) if issue.opened else None,
        'closed': _to_local(issue.closed, clientTZ) if issue.closed else None,
        'createdBy': issue.createdBy,
        'assignedTo': issue.assignedTo
    }

def _interpret_tzname(name):
    if name is not None:
        return timezone(name)
    else:
        return pytz.utc

class IssuesResource(object):
    def __init__(self, repo):
        self._repo = repo

    def on_get(self, req, resp):
        # See if a timezone is specified
        clientTZName = req.get_param('tz')
        clientTZ = _interpret_tzname(clientTZName)
 
        with self._repo.open() as repo:
            issue_list = repo.issues.list_issues()
            resp.media = {
                'issues': [_issue_to_json(issue, clientTZ) for issue in issue_list]
            }
            resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        fields = req.media

        with self._repo.open() as repo:
            # Check this has valid user id and session id
            if not repo.users.authenticateSessionId(fields.get('userId'), fields.get('sessionId')):
                resp.status_code = falcon.HTTP_401
                return

            new_id = repo.issues.create_issue(
                fields['title'],
                fields['description'],
                fields['userId']
            )
        raise falcon.HTTPSeeOther('/issues/{}'.format(new_id))

class IssueResource(object):
    def __init__(self, repo):
        self._repo = repo

    def on_get(self, req, resp, issue_id):
        clientTZName = req.get_param('tz')
        clientTZ = _interpret_tzname(clientTZName)
 
        with self._repo.open() as repo:
            issue = repo.issues.fetch_issue(int(issue_id))
            if issue != None:
                resp.media = _issue_to_json(issue, clientTZ)
            else:
                resp.media = { 'error': 'Issue does not exist' }
            resp.status = falcon.HTTP_200

    def on_put(self, req, resp, issue_id):
        fields = req.media

        with self._repo.open() as repo:
            # Check this has valid user id and session id
            if not repo.users.authenticateSessionId(fields.get('userId'), fields.get('sessionId')):
                resp.status_code = falcon.HTTP_401
                return

            repo.issues.update_issue(issue_id, **fields)
            resp.status = falcon.HTTP_204

class RegisterResource(object):
    """A resource to register new users."""

    def __init__(self, repo):
        self._repo = repo
    
    def on_post(self, req, resp):
        """Register a new user. The response may contain an 'error' property."""
        with self._repo.open() as repo:
            new_user = req.media
            error = repo.users.register(
                new_user['email'], 
                new_user['password']
            )

            if error is None:
                resp.status = falcon.HTTP_204
            else:
                resp.media = { 'error': error }
                resp.status = falcon.HTTP_200

class LoginResource(object):
    """A resource to login an existing user."""

    def __init__(self, repo):
        self._repo = repo
    
    def on_post(self, req, resp):
        """Login an existing user. If successful the response contains user and session ids."""
        with self._repo.open() as repo:
            authenticate_user = req.media
            sessionDetails = repo.users.createSessionId(
                authenticate_user['email'], 
                authenticate_user['password']
            )

            if sessionDetails is None:
                resp.status = falcon.HTTP_401
            else:
                resp.media = { 'userId': sessionDetails[0], 'sessionId': sessionDetails[1] }
                resp.status = falcon.HTTP_200

class LogoutResource(object):
    """A resource to logout an existing user."""

    def __init__(self, repo):
        self._repo = repo

    def on_post(self, req, resp):
        """Logout an existing user. There is never a response."""
        id = req.media['userId']
        with self._repo.open() as repo:
            repo.users.revokeSessionId(id)
            resp.status = falcon.HTTP_204

def _userToJSON(user):
    return {
        'id': user.id,
        'email': user.email
    }

class UsersResource(object):
    """A resource to get a list of users."""

    def __init__(self, repo):
        self._repo = repo

    def on_get(self, req, resp):
        with self._repo.open() as repo:
            userList = repo.users.listUsers()
            resp.media = {
                'users': [_userToJSON(user) for user in userList]
            }
            resp.status = falcon.HTTP_200
