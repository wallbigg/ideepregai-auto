import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "").strip()
TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip()

BUILD_DIR = Path(__file__).parent / "build"
VIDEO_FILE = BUILD_DIR / "reel_final.mp4"
TT_CAPTION_FILE = BUILD_DIR / "caption_tiktok.txt"
IG_CAPTION_FILE = BUILD_DIR / "caption.txt"
PUBLISHED_MARKER = BUILD_DIR / ".published"
TIKTOK_MARKER = BUILD_DIR / ".published_tiktok"


def _load_caption() -> str:
    if TT_CAPTION_FILE.exists():
        return TT_CAPTION_FILE.read_text(encoding="utf-8").strip()[:2150]
    if IG_CAPTION_FILE.exists():
        return IG_CAPTION_FILE.read_text(encoding="utf-8").strip()[:2150]
    return (
        "Você responderia ou manteria o silêncio? 👇 Acesse o protocolo completo no link da bio ou comenta ZERO. "
        "#relacionamento #termino #contatozero #superacao #codigozero #paravoce #fyp"
    )


def _refresh_tiktok_token() -> str:
    """Renova TIKTOK_ACCESS_TOKEN via OAuth2 refresh_token oficial quando configurado."""
    if not (TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET and TIKTOK_REFRESH_TOKEN):
        return TIKTOK_ACCESS_TOKEN
    data = urllib.parse.urlencode({
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": TIKTOK_REFRESH_TOKEN,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            tok = payload.get("access_token", "")
            if tok:
                print("Token OAuth2 do TikTok renovado com sucesso.")
                return tok
    except Exception as exc:
        print(f"Aviso ao renovar TIKTOK_REFRESH_TOKEN: {exc}")
    return TIKTOK_ACCESS_TOKEN


def _query_creator_info(token: str) -> dict:
    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        data=b"{}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8")).get("data") or {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Aviso creator_info TikTok ({exc.code}): {body[:240]}")
        return {}


def publish_via_official_api(token: str, caption: str) -> bool:
    """Publica vídeo 9:16 no TikTok via Content Posting API v2 oficial."""
    if not VIDEO_FILE.exists():
        print("Arquivo build/reel_final.mp4 não encontrado para upload no TikTok.")
        return False

    creator = _query_creator_info(token)
    privacy_opts = creator.get("privacy_level_options") or ["PUBLIC_TO_EVERYONE", "SELF_ONLY"]
    privacy = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in privacy_opts else privacy_opts[0]

    video_bytes = VIDEO_FILE.read_bytes()
    video_size = len(video_bytes)

    init_payload = {
        "post_info": {
            "title": caption[:2150],
            "privacy_level": privacy,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1,
        },
    }

    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        data=json.dumps(init_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            init_resp = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"TikTok API init error ({exc.code}): {body[:320]}")
        return False

    data = init_resp.get("data") or {}
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not (publish_id and upload_url):
        print(f"Resposta inesperada do TikTok init: {init_resp}")
        return False

    put_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(video_size),
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(put_req, timeout=120) as put_resp:
            print(f"Upload binário concluído no TikTok (HTTP {put_resp.status}) | publish_id={publish_id}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"TikTok PUT upload error ({exc.code}): {body[:320]}")
        return False

    status_req_body = json.dumps({"publish_id": publish_id}).encode("utf-8")
    for _ in range(18):
        time.sleep(4)
        sreq = urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
            data=status_req_body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(sreq, timeout=25) as sresp:
                sdata = (json.loads(sresp.read().decode("utf-8")).get("data") or {})
                st = sdata.get("status")
                print(f"TikTok status: {st}")
                if st in {"PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"}:
                    TIKTOK_MARKER.write_text(str(publish_id), encoding="utf-8")
                    if not PUBLISHED_MARKER.exists():
                        PUBLISHED_MARKER.write_text(f"tiktok:{publish_id}", encoding="utf-8")
                    print(f"Publicado no TikTok com sucesso! publish_id={publish_id}")
                    return True
                if st == "FAILED":
                    print(f"Falha reportada pelo TikTok: {sdata}")
                    return False
        except Exception as exc:
            print(f"Aviso ao consultar status TikTok: {exc}")

    return True


def main() -> None:
    if TIKTOK_MARKER.exists():
        TIKTOK_MARKER.unlink()

    token = _refresh_tiktok_token()
    if not token:
        print(
            "TIKTOK_ACCESS_TOKEN ausente nos GitHub Secrets. "
            "Vídeo pronto em build/reel_final.mp4 + build/caption_tiktok.txt no GitHub Release."
        )
        sys.exit(0)

    caption = _load_caption()
    publish_via_official_api(token, caption)
    sys.exit(0)


if __name__ == "__main__":
    main()
