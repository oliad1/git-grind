"""
All constants / re-used functions
"""

GITHUB_BASE_URL = "https://api.github.com/graphql"
GITHUB_URL = "https://github.com/"

def get_auth_header (gh_token: str):
    """
    Returns HTTP header for authenticated github API requests
    """
    return { 'Authorization': 'bearer '+gh_token }

def get_user_vars (username: str):
    """
    Returns GQL login format
    """
    return { "variables": {"login": username } }

GENERAL_QUERY = """
query ($login: String!) {
  user (login: $login) {
    avatarUrl
    bio
    pronouns
    url
    name
    status {
      emoji
      message
    }
    login
    contributionsCollection {
      totalCommitContributions
      totalRepositoryContributions
      pullRequestContributions {
        totalCount
      }
      issueContributions {
        totalCount
      }
    }
  }
}
"""

def get_user (username: str):
    """
    Returns body for user query
    """
    return {
        "query": GENERAL_QUERY,
        "variables": {
            "login": username
        }
    }

emoji = ["first", "second", "third"]
