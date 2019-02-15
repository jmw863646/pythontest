Feature: Issues

  Background:
    Given a browser

  Scenario: Raising an issue
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

