Feature: Doing http requests

  Scenario: Send text body and headers
    Given I set header "X-My-Header" with value "Something"
    When I send a POST request to "/requests/echo" with body:
    """
    Something
    """
    Then the response code should be 200
    And the response should contain json:
    """
        {
            "method": "POST",
            "headers": {
                "X-My-Header": "Something"
            },
            "body": "Something"
        }
    """

  Scenario: Send form data
    Given I set header "X-My-Header" with value "Something"
    When I send a POST request to "/requests/echo" with values:
    """
    name=Wilson
    age=42
    """
    Then the response should contain json:
    """
        {
            "method": "POST",
            "body": "age=42&name=Wilson"
        }
    """

  Scenario: Send file
    Given I set header "X-My-Header" with value "Something"
    And I attach the file "$PWD/features/data/favicon.ico" as "upload"
    When I send a POST request to "/requests/echo"
    Then the response should contain json:
    """
        {
            "method": "POST",
            "files": [
                {
                    "key": "upload",
                    "name": "favicon.ico"
                }
            ]
        }
    """

  Scenario: Set variable
    Given I set variable "username" with value "Bob"
    When I send a POST request to "/requests/echo" with body:
    """
    Hello $username
    """
    Then the response should contain json:
    """
        {
            "body": "Hello Bob"
        }
    """
