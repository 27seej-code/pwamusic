# Seal Music Player

A simple installable web app for playing your own audio files, with playlists, shuffle, repeat, and 15-second skip.

## Add songs from YouTube (laptop server)

Tap the **YouTube** button to search and download audio straight into your
library. This talks to a small backend that runs on your own laptop (it uses
`yt-dlp`), exposed over `https://` with a Cloudflare tunnel. The code and full
setup steps are in [`server/`](server/).

First use: tap YouTube → enter the **Server URL** (your Cloudflare tunnel URL)
and the **Password** (the server's `API_KEY`). These are saved on the device.

## Important: you must host this, you can't just open the file

iOS Safari will not install a PWA or run a service worker from a `file://` path. You need to serve these files over **HTTPS** first. Easiest free options:

1. **GitHub Pages** (recommended, free, permanent)
   - Create a new GitHub repo, upload all files in this folder (`index.html`, `manifest.json`, `sw.js`, `icons/`) to the repo root.
   - In the repo Settings → Pages, set the source to your main branch.
   - You'll get a URL like `https://yourname.github.io/reponame/`.

2. **Any static host** (Netlify, Vercel, Cloudflare Pages) — drag-and-drop this folder in.

## Installing on your iPhone 11

1. Open the hosted URL in **Safari** (must be Safari, not Chrome).
2. Tap the Share icon → **Add to Home Screen**.
3. Open it from the home screen icon — it now runs full-screen like a native app.

## Using it

- **Add songs**: tap "Add songs" to pick individual files. These go straight into your library (no playlist prompt).
- **Add folder → becomes a playlist**: tap **"Add folder"**, select a folder of audio files, and the app will ask you to name a playlist for that batch (leave the name blank if you just want them in your library, no playlist). All the songs in the folder are imported and added to that playlist in one step.
  - To grab an entire album folder on iPhone: open the folder in the Files picker, tap **Select** (top right), tap **Select All**, then tap the checkmark/Open button. Any non-audio file swept up (like a `cover.jpg`) is skipped automatically.
  - **iPhone limitation**: iOS Safari doesn't tell the browser what folder a file came from, so on iPhone you'll always type the playlist name yourself in the prompt. (On desktop browsers that do support folder selection, the folder's name is pre-filled for you automatically.)
  - Importing into the same playlist name twice just adds the new songs to the existing playlist rather than making a duplicate.
  - Any common audio format is accepted — MP3, M4A/AAC, WAV, AIFF, FLAC, ALAC, OGG, WMA, etc. Note: a small number of formats (Ogg Vorbis, WMA) aren't actually decodable by iOS's audio engine even though the file can be imported — if one of those fails to play, the app will tell you rather than failing silently. MP3, AAC/M4A, WAV, AIFF, and FLAC all play natively on iPhone.
  - Files are copied into the app's local storage (IndexedDB) on import, so you only need to do this once per song.
- **Playlists**: switch to the Playlists tab, create a playlist, then use the **⋯** menu next to any song to add/remove it from playlists.
- **Playback**: tap any song to play it and queue the rest of that list. Controls: shuffle, repeat (off/all/one), previous/next track, ±15s skip, and a scrub bar.
- **Search**: the search bar filters whichever list you're looking at (library or an open playlist).
- **Lock screen controls**: play/pause/skip/seek show up on the iPhone lock screen and Control Center while a track is loaded.

## Known iOS limitations (not bugs, just how Safari works)

- Safari can occasionally clear site storage if the app goes unused for a long time (Apple's storage eviction policy). If your library disappears after weeks of not opening it, you'll need to re-import songs.
- Background/lock-screen audio works while the app is open or backgrounded normally, but iOS may pause audio if the app is force-quit.
- There's no cloud sync — your library lives only on this device, in this browser.
