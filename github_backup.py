import requests
import os
import base64

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Yasar468/katilim-momentum-system"

def upload_file(path):

    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    filename = os.path.basename(path)

    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    data = {
        "message": f"auto update {filename}",
        "content": content
    }

    requests.put(url, json=data, headers=headers)