GITHUB_BASE_URL = "https://api.github.com/graphql"
GITHUB_URL = "https://github.com/"

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

def getUser (username: str):
    return { 
        "query": GENERAL_QUERY,
        "variables": {
            "login": username
        }
    }
