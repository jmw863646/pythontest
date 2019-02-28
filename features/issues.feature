Feature: Issues

  Background:
    Given a browser

  Scenario: Raising an issue
    Given screenshots folder exists
    When I open the website
    Then I should be able to login
    Given I'd like to register a user and login
    When I register a new user and login
    Then should be logged in as new user
    When the page is refreshed
    Then should still be logged in
    Given I'd like to raise a bug with a name that hasn't been used before
    When I raise the bug
    Then my bug should appear in the list
    When I view the description of the bug
    Then the description should match
    When I edit the existing bug
    Then the title should match
    When I change the description, close the bug and save
    Then my bug should appear in the list closed
    When I view the description of the bug again
    Then the description should be updated
    When I logout
    Then I should be able to login
    Given I'd like to raise a bug with a name that hasn't been used before
    When I raise a bug while not logged in
    Then should ask me to login
    Given edit an existing bug
    When I change the description, close the bug and save while not logged in
    Then should ask me to login

