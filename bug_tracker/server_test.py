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
        register_resp = self.client.simulate_post(
            '/register',
            json={'email': 'justin@justinware.me.uk', 'password': 'garfield'}
        )
        self.assertEqual(register_resp.status_code, 204, 'Successfully registered a user')

        login_resp = self.client.simulate_post(
            '/login',
            json={'email': 'justin@justinware.me.uk', 'password': 'garfield'}
        )
        self.assertEqual(login_resp.status_code, 200)
        userId = login_resp.json['userId']
        sessionId = login_resp.json['sessionId']

        create_resp = self.client.simulate_post(
            '/issues',
            json={
                'title': 'Test Issue', 
                'description': 'Test Description', 
                'userId': userId, 
                'sessionId': sessionId
            }
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
        self.assertEqual(issue_json['createdBy'], 'justin@justinware.me.uk')

        list_resp = self.client.simulate_get('/issues')
        issues = list_resp.json['issues']
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['title'], "Test Issue")
        self.assertEqual(issues[0]['description'], "Test Description")
        self.assertEqual(issues[0]['createdBy'], "justin@justinware.me.uk")

        update_resp = self.client.simulate_put(
            new_location,
            json={
                'description': 'An updated issue', 
                'userId': userId, 
                'sessionId': sessionId
            }
        )
        self.assertEqual(update_resp.status_code, 204)

        fetch_resp_2 = self.client.simulate_get(new_location)
        issue_json_2 = fetch_resp_2.json
        self.assertEqual(issue_json_2['description'], "An updated issue")

        # Want another user
        register_resp = self.client.simulate_post(
            '/register',
            json={'email': 'fred@bloggs.com', 'password': 'garfield'}
        )
        self.assertEqual(register_resp.status_code, 204, 'Successfully registered a user')

        login_resp = self.client.simulate_post(
            '/login',
            json={'email': 'fred@bloggs.com', 'password': 'garfield'}
        )
        self.assertEqual(login_resp.status_code, 200)
        userId = login_resp.json['userId']
        sessionId = login_resp.json['sessionId']

        # Assign issue to the other user
        update_resp = self.client.simulate_put(
            new_location,
            json={
                'assigneeId': userId, 
                'userId': userId, 
                'sessionId': sessionId
            }
        )
        fetch_resp_2 = self.client.simulate_get(new_location)
        issue_json_2 = fetch_resp_2.json
        self.assertEqual(issue_json_2['createdBy'], 'justin@justinware.me.uk')
        self.assertEqual(issue_json_2['assignedTo'], 'fred@bloggs.com')

        # Query issue with a different timezone
        fetch_resp_3 = self.client.simulate_get(new_location, params = {'tz': 'US/Eastern'})
        issue_json_3 = fetch_resp_3.json
        self.assertLess(
            parse_date(issue_json_3['opened']),
            parse_date(issue_json_2['opened']) - datetime.timedelta(hours = 3),
            'Timestamp should be earlier as in the USA not Greenwich'
        )
    
    def test_nonexistent_issues(self):
        fetch_resp = self.client.simulate_get('/issues/1')
        self.assertEqual(fetch_resp.status_code, 200, 'Succeeds but returns error in JSON')
        self.assertIn('error', fetch_resp.json)

    def test_user_register(self):
        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'justin@justinware.me.uk', 'password': 'garfield'}
        )
        self.assertEqual(create_resp.status_code, 204, 'Succeeds and returns no more output')

        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'justin@justinware.me.uk', 'password': 'pookie'}
        )
        self.assertEqual(create_resp.status_code, 200, 'Output returned')
        self.assertIn('error', create_resp.json)

        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'clearly not an e-mail address', 'password': 'wibble'}
        )
        self.assertEqual(create_resp.status_code, 200, 'Output returned')
        self.assertIn('error', create_resp.json)

    def test_user_login(self):
        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'justin@justinware.me.uk', 'password': 'garfield'}
        )
        self.assertEqual(create_resp.status_code, 204, 'Succeeds and returns no more output')

        login_resp = self.client.simulate_post(
            '/login',
            json={'email': 'fred@flintstones.org', 'password': 'yabba-dabba-doo'}
        )
        self.assertEqual(login_resp.status_code, 401, 'Not authorised')

        login_resp = self.client.simulate_post(
            '/login',
            json={'email': 'justin@justinware.me.uk', 'password': 'yabba-dabba-doo'}
        )
        self.assertEqual(login_resp.status_code, 401, 'Not authorised')

        login_resp = self.client.simulate_post(
            '/login',
            json={'email': 'justin@justinware.me.uk', 'password': 'garfield'}
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json['userId'], 1)
        self.assertEqual(len(login_resp.json['sessionId']), 32)

        logout_resp = self.client.simulate_post(
            '/logout',
            json={'userId': 1}
        )
        self.assertEqual(logout_resp.status_code, 204)
    
    def test_user_list(self):
        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'a@b.c', 'password': 'wibble'}
        )
        self.assertEqual(create_resp.status_code, 204)
        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'z@d.e', 'password': 'wibble'}
        )
        self.assertEqual(create_resp.status_code, 204)
        create_resp = self.client.simulate_post(
            '/register',
            json={'email': 'm@f.g', 'password': 'wibble'}
        )
        self.assertEqual(create_resp.status_code, 204)

        user_list_resp = self.client.simulate_get(
            '/users'
        )
        self.assertEqual(user_list_resp.status_code, 200)
        users = user_list_resp.json['users']
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0]['id'], 1)
        self.assertEqual(users[0]['email'], 'a@b.c')
        self.assertEqual(users[1]['id'], 3)
        self.assertEqual(users[1]['email'], 'm@f.g')
        self.assertEqual(users[2]['id'], 2)
        self.assertEqual(users[2]['email'], 'z@d.e')

if __name__ == '__main__':
    main()
