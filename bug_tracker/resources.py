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
        with self._repo.open() as repo:
            new_issue = req.media
            new_id = repo.issues.create_issue(
                new_issue['title'],
                new_issue['description']
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
        with self._repo.open() as repo:
            update = req.media
            repo.issues.update_issue(issue_id, **update)
            resp.status = falcon.HTTP_204
