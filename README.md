Python Tech Test
================

Goal
----

This repository contains an unfinished issue tracker web app. Your goal is to
make some of the following improvements to it:

- Fix the bug where it's not possible to add an issue titled "Can't log in"
- Fix the bug where it's not possible to close an issue
- Fix the bug where the edit screen doesn't change the description of the issue
- Make REST endpoints return a more reasonable response when requesting non-existent resources
- Add date formatting in the UI, to put timestamps in the user's local timezone
- Add a login and registration page, to enable username/password login
  - Read-only pages don't need users to be logged in, but new/edit/update pages do
  - Username must be a valid email address
  - Once this is done, add the ability to assign bugs to users, and for bugs to have creators
- Create a dashboard page with the following information:
  - How many bugs are currently open, and what percentage this is of the maximum number that were ever open at once
  - How many bugs were closed in the last week

We are more interested in looking at what you consider good practice, than in
measuring how quickly you work, so do not worry if you can't finish all the tasks.
You do not have to tackle the tasks in any particular order.

Some of the libraries and frameworks used may not be familiar to you. This is
deliberate, and you are not expected to already know them, and can refer to
online documentation.

Getting Started
---------------

### Prerequisites

- Ensure you have Python 2.7 and NodeJS 8 or higher
- Create a new virtualenv and `pip install -r requirements.txt`
- Obtain the necessary Node modules with `npm install`

### Running The App

Run unit and component integration tests with:
```
python -m unittest discover . '*_test.py'  # Run Python tests
npm test  # Run node tests
```

Build UI assets with:
```
npm run-script build
```

Or have them auto-rebuild with:
```
npm run-script watch
```

And run the app with:
```
python -m bug_tracker.server
```

Run end-to-end tests with:
```
npm run-script integration-test
```
