GITHUB_BASE_URL = "https://api.github.com/graphql"

def getAuthHeader (gh_token: str):
    return { 'Authorization': 'bearer '+gh_token }

def getUserVars (username: str):
    return { "variables": {"login": username } }

GENERAL_QUERY = """
query ($login: String!) {
  user (login: $login) {
    avatarUrl
    bio
    pronouns
    url
    status {
      emoji
      message
    }
    login
    contributionsCollection {
      totalCommitContributions
      totalRepositoryContributions
    }
  }
}
"""

def getUser (username: str):
    return { 
        "query": GENERAL_QUERY,
        "variables": {
            "login": username
        }
    }
