import os 
import logging
import requests
import time
from dotenv import load_dotenv
from utils import connect_db, push_entry, add_metadata_to_entry

def get_pretools_repositories(pretools_collection):
    
    # aggregation pipeline 
    pipeline = [
        {"$unwind": "$data.repository"},  # Unwind the repository array
        {"$match": {"data.repository.kind": "github"}},  # Match only GitHub repositories
        {"$project": {"_id": 0, "url": "$data.repository.url"}}  # Project only the URL field
    ]
    results = pretools_collection.aggregate(pipeline)

    # return unique repositories
    repositories = set()
    for result in results:
        repositories.add(result['url'])

    return list(repositories)



# Get information for each repository using the API
def repo_owner(repo_url):
    
    # remove final .git if present 
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]

    # remove trailing slash if present
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]

    # Extract owner and repository name from the URL
    owner, repo = repo_url.split('/')[-2:]
    return owner, repo

def get_repository_info(repo_url, token):
    '''
    Make a request to the GitHub API to get metadata for a repository.
    This function handles rate limit and retries the request if needed.
    '''
    request_url = 'https://observatory.openebench.bsc.es/github-metadata-api/metadata/user'
    owner, repo = repo_owner(repo_url)
    data = {
        "owner" : owner,
        "repo" : repo,
        "userToken" : token,
        "prepare" : False
    }

    remaining, reset_time = get_rate_limit()
    
    if remaining == 0:
        # If remaining requests are 0, wait until the reset time
        wait_for_rate_limit_reset(reset_time)

    response = requests.post(request_url, json=data)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:  # Rate limit exceeded
        # Get reset time from the response headers
        reset_time = int(response.headers['X-RateLimit-Reset'])
        wait_for_rate_limit_reset(reset_time)
        # Retry the request after waiting
        return get_repository_info(request_url)
    else:
        # Handle other potential errors
        response.raise_for_status()
    
    return None


def get_rate_limit():
    """Check the current rate limit status."""
    rate_limit_url = 'https://api.github.com/rate_limit'
    token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
        'Accept': 'application/vnd.github+json'
    }
    response = requests.get(rate_limit_url, headers=headers)
    data = response.json()
    
    remaining = data['resources']['core']['remaining']
    reset_time = data['resources']['core']['reset']
    
    return remaining, reset_time

def wait_for_rate_limit_reset(reset_time):
    """Wait until the rate limit is reset."""
    current_time = time.time()
    wait_seconds = reset_time - current_time
    if wait_seconds > 0:
        print(f"Rate limit exceeded. Waiting for {wait_seconds} seconds.")
        time.sleep(wait_seconds + 5)  # Adding 5 seconds buffer


if __name__ == '__main__':
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)

    token = os.getenv('GITHUB_TOKEN')

    ALAMBIQUE = os.getenv('ALAMBIQUE', default='alambiqueDev')
    alambique_collection = connect_db(ALAMBIQUE)
    PRETOOLS = os.getenv('PRETOOLS', default='pretoolsDev')
    pretools_collection = connect_db(PRETOOLS)

    repositories_urls = get_pretools_repositories(pretools_collection)

    for repository_url in repositories_urls:
        logging.info(f'Retrieving info from {repository_url}')
        try:
            retrieved_info = get_repository_info(repository_url, token)
            retrieved_info = retrieved_info['data']
        except Exception as e:
            logging.error(f"Failed to get metadata for repository: {repository_url}")
            logging.error(f"Error: {e}")
            continue
        else:
            if retrieved_info:
                identifier = repository_url
                entry = {
                    'data': retrieved_info,
                    '@data_source': 'github'
                }
                document_w_metadata = add_metadata_to_entry(identifier, entry, alambique_collection)
                push_entry(document_w_metadata, alambique_collection)
                #print('New entry inserted to the database.')
                #print(document_w_metadata)
            else:
                logging.error(f"Failed to get metadata for repository: {repository_url}")
        