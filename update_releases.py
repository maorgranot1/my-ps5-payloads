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

def get_latest_release_info(domain, owner, repo, token, old_filename, current_version, app_name):
    """Fetches the latest release with special handling rules per application."""
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
        assets = data.get("assets", [])
        
        if not tag_name:
            return None, None, old_filename
            
        actual_filename = old_filename
        asset_digest = None
        
        # Build the expected filename ONLY if it's etaHEN
        ext = os.path.splitext(old_filename)[1]
        expected_filename = old_filename
        if app_name == "etaHEN":
            expected_filename = f"etaHEN-{tag_name}{ext}"
        
        for asset in assets:
            name = asset.get("name")
            if not name:
                continue
            
            # Specific rule: if it's etaHEN, match any asset starting with "etaHEN-" and ending with the correct extension
            is_etahen_match = (app_name == "etaHEN" and name.startswith("etaHEN-") and name.endswith(ext))
            
            if name == old_filename or name == expected_filename or is_etahen_match:
                actual_filename = name
                digest = asset.get("digest")
                if digest and digest.startswith("sha256:"):
                    asset_digest = digest.replace("sha256:", "")
                break
                
        return tag_name, asset_digest, actual_filename
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch release for {owner}/{repo}: {e}")
        return None, None, old_filename

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
            
        domain, owner, repo, old_filename = match.groups()
        current_version = app.get('version')
        app_name = app.get('name')
        
        latest_tag, precalculated_hash, actual_filename = get_latest_release_info(
            domain, owner, repo, github_token, old_filename, current_version, app_name
        )
        
        if latest_tag and latest_tag != current_version:
            print(f"Update found for {app_name}: {current_version} -> {latest_tag}")
            
            new_url = f"https://{domain}/{owner}/{repo}/releases/download/{latest_tag}/{actual_filename}"
            
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
                app['filename'] = actual_filename
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
