import requests
import os
import base64

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Yasar468/katilim-momentum-system"

def upload_file(path):

    filename = os.path.basename(path)

    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    # önce dosyanın sha bilgisini al
    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    data = {
        "message": f"auto update {filename}",
        "content": content
    }

    if sha:
        data["sha"] = sha

    requests.put(url, json=data, headers=headers)