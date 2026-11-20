import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
VIDEO_URL = os.environ.get("VIDEO_PUBLIC_URL", "")
CAPTION_FILE = Path(__file__).parent / "build" / "caption.txt"
BASE_URL = (
    "https://graph.instagram.com/v21.0"
    if IG_ACCESS_TOKEN.startswith("IGA")
    else "https://graph.facebook.com/v21.0"
)


def api_post(endpoint: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/{endpoint}", data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Meta API POST error ({endpoint}): {exc.code} {body}")
        raise


def api_get(endpoint: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(f"{BASE_URL}/{endpoint}?{qs}", timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Meta API GET error ({endpoint}): {exc.code} {body}")
        raise


def main() -> None:
    if not (IG_ACCESS_TOKEN and VIDEO_URL) or (
        not IG_ACCESS_TOKEN.startswith("IGA") and not IG_USER_ID
    ):
        print("IG_USER_ID, IG_ACCESS_TOKEN ou VIDEO_PUBLIC_URL ausentes. Pulando publicação automática.")
        sys.exit(0)

    target_id = IG_USER_ID
    if not target_id and IG_ACCESS_TOKEN.startswith("IGA"):
        me = api_get("me", {"fields": "id,user_id,username", "access_token": IG_ACCESS_TOKEN})
        target_id = str(me.get("user_id") or me.get("id") or "me")

    caption = CAPTION_FILE.read_text(encoding="utf-8")
    container = api_post(f"{target_id}/media", {
        "media_type": "REELS",
        "video_url": VIDEO_URL,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    })
    creation_id = container["id"]
    print("Container criado:", creation_id)

    status: dict = {}
    code = None
    for _ in range(36):
        status = api_get(creation_id, {"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN})
        code = status.get("status_code")
        print("Status:", code)
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Erro no processamento da Meta: {status}")
        time.sleep(5)
    else:
        raise RuntimeError(f"Timeout aguardando processamento da Meta. Último status: {status}")

    pub = api_post(f"{target_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    })
    print("Publicado no Instagram! Media ID:", pub["id"])


if __name__ == "__main__":
    main()
