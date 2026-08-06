import json
import os
import re
import hashlib
import datetime
import requests

# Referencing your specific file exactly
JSON_FILE = 'P.json' 

def calculate_sha256(url):
    """Fallback: Downloads the file to calculate its SHA-256 checksum."""
    print(f"  -> Digest missing from API. Downloading file to calculate hash...")
    sha256_hash = hashlib.sha256()
    try:
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()
        for byte_block in response.iter_content(chunk_size=8192):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def get_latest_release_info(domain, owner, repo, token, target_filename):
    """Fetches the latest release and attempts to pull GitHub's auto-generated digest."""
    if "github.com" in domain:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    else:
        api_url = f"https://{domain}/api/v1/repos/{owner}/{repo}/releases/latest"
        headers = {"Accept": "application/json"}
        
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        tag_name = data.get("tag_name")
        asset_digest = None
        
        # Scan the API's asset list to find the specific file and extract its native digest
        for asset in data.get("assets", []):
            if asset.get("name") == target_filename:
                digest = asset.get("digest")
                if digest and digest.startswith("sha256:"):
                    # Strip the "sha256:" prefix to get the raw hash string
                    asset_digest = digest.replace("sha256:", "")
                break
                
        return tag_name, asset_digest
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch release for {owner}/{repo}: {e}")
        return None, None

def main():
    github_token = os.environ.get("GITHUB_TOKEN", "")
    
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)

    updated = False

    for app in data:
        url = app.get('url')
        match = re.match(r"https://([^/]+)/([^/]+)/([^/]+)/releases/download/[^/]+/(.+)", url)
        
        if not match:
            print(f"Could not parse URL for {app.get('name')}")
            continue
            
        domain, owner, repo, filename = match.groups()
        current_version = app.get('version')
        
        latest_tag, precalculated_hash = get_latest_release_info(domain, owner, repo, github_token, filename)
        
        if latest_tag and latest_tag != current_version:
            print(f"Update found for {app['name']}: {current_version} -> {latest_tag}")
            
            new_url = f"https://{domain}/{owner}/{repo}/releases/download/{latest_tag}/{filename}"
            
            # 1. Use the hash GitHub already calculated for us
            if precalculated_hash:
                print(f"  -> Extracted GitHub API native SHA-256 digest: {precalculated_hash}")
                new_checksum = precalculated_hash
            # 2. Fall back to downloading for non-GitHub servers
            else:
                new_checksum = calculate_sha256(new_url)
            
            if new_checksum:
                app['version'] = latest_tag
                app['url'] = new_url
                app['checksum'] = new_checksum
                app['last_update'] = datetime.datetime.now().strftime("%Y-%m-%d")
                updated = True

    if updated:
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {JSON_FILE}.")
    else:
        print("All repositories are up to date.")

if __name__ == "__main__":
    main()
