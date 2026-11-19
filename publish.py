import os
import sys
import time
import json
import urllib.parse
import urllib.request
from pathlib import Path

IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
VIDEO_URL = os.environ.get("VIDEO_PUBLIC_URL", "")
CAPTION_FILE = Path(__file__).parent / "build" / "caption.txt"


def api_post(endpoint: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{endpoint}", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get(endpoint: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{endpoint}?{qs}", timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    if not (IG_USER_ID and IG_ACCESS_TOKEN and VIDEO_URL):
        print("IG_USER_ID, IG_ACCESS_TOKEN ou VIDEO_PUBLIC_URL ausentes. Pulando publicação automática.")
        sys.exit(0)

    caption = CAPTION_FILE.read_text(encoding="utf-8")
    container = api_post(f"{IG_USER_ID}/media", {
        "media_type": "REELS",
        "video_url": VIDEO_URL,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    })
    creation_id = container["id"]
    print("Container criado:", creation_id)

    for _ in range(24):
        status = api_get(creation_id, {"fields": "status_code", "access_token": IG_ACCESS_TOKEN})
        code = status.get("status_code")
        print("Status:", code)
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Erro no processamento da Meta: {status}")
        time.sleep(5)

    pub = api_post(f"{IG_USER_ID}/media_publish", {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    })
    print("Publicado no Instagram! Media ID:", pub["id"])


if __name__ == "__main__":
    main()
