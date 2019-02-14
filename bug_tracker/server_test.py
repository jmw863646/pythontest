from __future__ import absolute_import
import datetime
import os
import pytz
import tempfile

from dateutil.parser import parse as parse_date
from falcon import testing

from unittest import TestCase, main
from .server import make_api


class APITest(TestCase):
    def setUp(self):
        self.db_file = tempfile.mktemp()
        self.api = make_api(self.db_file)
        self.client = testing.TestClient(self.api)

    def tearDown(self):
        os.remove(self.db_file)

    def test_issue_workflow(self):
        create_resp = self.client.simulate_post(
            '/issues',
            json={'title': "Test Issue", 'description': "Test Description"}
        )
        self.assertEqual(create_resp.status_code, 303)
        new_location = create_resp.headers['Location']

        fetch_resp = self.client.simulate_get(new_location)
        issue_json = fetch_resp.json
        self.assertEqual(issue_json['title'], "Test Issue")
        self.assertEqual(issue_json['description'], "Test Description")
        self.assertAlmostEqual(
            parse_date(issue_json['opened']),
            datetime.datetime.utcnow(),
            delta=datetime.timedelta(seconds=5)
        )

        list_resp = self.client.simulate_get('/issues')
        issues = list_resp.json['issues']
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['title'], "Test Issue")
        self.assertEqual(issues[0]['description'], "Test Description")

        update_resp = self.client.simulate_put(
            new_location,
            json={
                'description': "An updated issue"
            }
        )
        self.assertEqual(update_resp.status_code, 204)

        fetch_resp_2 = self.client.simulate_get(new_location)
        issue_json_2 = fetch_resp_2.json
        self.assertEqual(issue_json_2['description'], "An updated issue")

if __name__ == '__main__':
    main()
