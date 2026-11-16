# Seal Music Player — laptop YouTube backend

This is the little server that the app calls to **search YouTube and download
audio**. The PWA (GitHub Pages / Cloudflare Pages) is static and can't run
`yt-dlp`, so the heavy lifting happens here on your laptop, and a **Cloudflare
tunnel** gives the app a public `https://` URL to reach it.

```
 iPhone PWA  ──https──►  Cloudflare tunnel  ──►  this server (yt-dlp)  ──►  YouTube
```

## API (what the app calls)

| Method & path            | Auth header        | Returns                                           |
|--------------------------|--------------------|---------------------------------------------------|
| `GET /`                  | none               | `{"ok": true}` (health / wake)                    |
| `GET /search?q=<text>`   | `X-Api-Key: <pw>`  | `[{id,title,channel,duration,thumbnail}, ...]`    |
| `GET /download?id=<vid>` | `X-Api-Key: <pw>`  | raw audio bytes (`audio/mp4`)                     |

A wrong key returns `401 {"detail":"Wrong password"}`.

## Setup on the Ubuntu laptop (hostname: terrafront / terrafrontserver1)

```bash
# 1. system deps
sudo apt update
sudo apt install -y python3-venv ffmpeg   # ffmpeg optional but recommended

# 2. get this folder onto the laptop, then:
cd ~/pwamusic/server
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# 3. pick a password (this is what you type into the app)
export API_KEY='choose-a-password'

# 4. run it (listens locally; the tunnel exposes it)
uvicorn app:app --host 127.0.0.1 --port 8099
```

Leave it running, or install it as a service so it survives reboots:

```bash
# edit User / paths / API_KEY inside the unit first
sudo cp seal-music.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now seal-music
journalctl -u seal-music -f      # watch the logs
```

## Expose it with Cloudflare (you said everything is on Cloudflare)

Install cloudflared once:

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && sudo chmod +x /usr/local/bin/cloudflared
```

### Option A — quick tunnel (no domain needed, URL changes each run)

```bash
cloudflared tunnel --url http://127.0.0.1:8099
```

It prints a `https://something.trycloudflare.com` URL. Paste **that URL** and
your password into the app (YouTube button → Server URL + Password). If you
restart the tunnel you get a new URL and re-paste it.

### Option B — named tunnel on a stable hostname (recommended)

If you add a domain to Cloudflare, the URL never changes:

```bash
cloudflared tunnel login
cloudflared tunnel create seal-music
cloudflared tunnel route dns seal-music yt.yourdomain.com
# ~/.cloudflared/config.yml:
#   tunnel: seal-music
#   credentials-file: /home/seeyal/.cloudflared/<id>.json
#   ingress:
#     - hostname: yt.yourdomain.com
#       service: http://127.0.0.1:8099
#     - service: http_status:404
cloudflared tunnel run seal-music      # or install as a service: cloudflared service install
```

Then the app's Server URL is `https://yt.yourdomain.com` permanently.

## Using it in the app

1. Open the app, tap the **YouTube** button.
2. Enter the **Server URL** (the Cloudflare URL above) and the **Password**
   (your `API_KEY`). These are saved on the device.
3. Search, tap a result → it downloads the audio into your library.

## "Sign in to confirm you're not a bot"

If YouTube starts blocking the server, export a `cookies.txt` from a browser
logged in to YouTube and point the server at it:

```bash
export YT_COOKIES=/home/seeyal/pwamusic/server/cookies.txt
```

(or set it in the systemd unit), then restart.
