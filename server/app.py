"""
Seal Music Player — YouTube backend (runs on the laptop server).

Implements exactly the HTTP contract the PWA front-end expects:

  GET  /                      -> {"ok": true}          (health / wake-up, no auth)
  GET  /search?q=<text>       -> [ {id,title,channel,duration,thumbnail}, ... ]
  GET  /download?id=<videoId> -> raw audio bytes (audio/mp4 etc.)

Both /search and /download require the header:  X-Api-Key: <password>
A wrong/missing key returns HTTP 401 with JSON {"detail": "..."}.

Run it on the Ubuntu laptop and expose it with a Cloudflare tunnel; the
public https URL + the password get typed into the app's YouTube settings.

See README.md in this folder for full setup instructions.
"""
import os
import glob
import tempfile

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from yt_dlp import YoutubeDL

# ---- config (from environment) --------------------------------------------
API_KEY = os.environ.get("API_KEY", "")          # the in-app password
SEARCH_LIMIT = int(os.environ.get("SEARCH_LIMIT", "20"))

app = FastAPI(title="Seal Music YouTube backend")

# The front-end sends the password in a header, so any origin is safe to allow;
# this lets the GitHub Pages / Cloudflare Pages builds call the tunnel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

CONTENT_TYPES = {
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".webm": "audio/webm",
    ".opus": "audio/ogg",
    ".ogg": "audio/ogg",
    ".mp3": "audio/mpeg",
}

# Common yt-dlp options. A cookies file (exported from a browser logged in to
# YouTube) greatly reduces "Sign in to confirm you're not a bot" errors.
COOKIES = os.environ.get("YT_COOKIES", "")  # path to a cookies.txt, optional


def _check(key: str):
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=401, detail="Wrong password")


def _ydl_base() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "retries": 3,
        "socket_timeout": 30,
    }
    if COOKIES and os.path.exists(COOKIES):
        opts["cookiefile"] = COOKIES
    return opts


@app.get("/")
def health():
    return {"ok": True}


@app.get("/search")
def search(q: str = Query(..., min_length=1), x_api_key: str = Header("")):
    _check(x_api_key)
    opts = _ydl_base()
    opts.update({"extract_flat": "in_playlist", "skip_download": True})
    out = []
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{SEARCH_LIMIT}:{q}", download=False)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Search failed: {e}")
    for e in (info or {}).get("entries", []) or []:
        if not e:
            continue
        vid = e.get("id")
        if not vid:
            continue
        out.append({
            "id": vid,
            "title": e.get("title") or "Untitled",
            "channel": e.get("channel") or e.get("uploader") or "",
            "duration": e.get("duration") or 0,
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
        })
    return out


@app.get("/download")
def download(id: str = Query(..., min_length=1), x_api_key: str = Header("")):
    _check(x_api_key)
    # basic sanity check on the video id
    if len(id) > 32 or any(c in id for c in "/\\?&= "):
        raise HTTPException(status_code=400, detail="Bad id")

    with tempfile.TemporaryDirectory() as tmp:
        opts = _ydl_base()
        opts.update({
            # prefer a progressive m4a (plays natively on iOS, no ffmpeg needed)
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
        })
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={id}"])
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Download failed: {e}")

        files = glob.glob(os.path.join(tmp, "*"))
        if not files:
            raise HTTPException(status_code=502, detail="Download produced no file")
        path = files[0]
        ext = os.path.splitext(path)[1].lower()
        with open(path, "rb") as f:
            data = f.read()
    if len(data) < 1000:
        raise HTTPException(status_code=502, detail="Download was empty")
    return Response(content=data, media_type=CONTENT_TYPES.get(ext, "audio/mp4"))


# Make sure even unexpected errors come back as {"detail": ...} JSON,
# which is what the front-end reads.
@app.exception_handler(Exception)
def _any_error(_req, exc):  # noqa: ANN001
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": str(exc)})
