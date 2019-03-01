Feature: Issues

  Background:
    Given a browser

  Scenario: Raising an issue
    Given screenshots folder exists
    When I open the website
    Then I should be able to login
    Given I'd like to create some users
    When I register a new user and login
    Then should be logged in as user1
    When the page is refreshed
    Then should still be logged in
    Given I'd like to raise bug with names that haven't been used before
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
    When I raise a bug while not logged in
    Then should ask me to login
    Given edit an existing bug
    When I change the description, close the bug and save while not logged in
    Then should ask me to login
    Given I've registered some new users
    When I login as user1
    Then should be logged in as user1
    When I view the description of the bug
    Then the bug should not be assigned
    When I edit the existing bug
    Then the title should match
    When the bug is assigned and saved
    Then the bug should be assigned
    When I edit the existing bug
    Then the title should match
    When the bug is unassigned and saved
    Then the bug should not be assigned



