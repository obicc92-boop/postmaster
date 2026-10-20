# video-editor

Tools and assets for turning eFootball screen recordings (1560×720 phone captures) into
TikTok highlight videos (1080×1920) for Somtoo FC.

## Current style (v5)

- Steady **4:3 frame** (960×720 of the recording → 1080×810, centred), panned automatically with the ball.
- Short **commentary** above the video (Anton + colour emoji, no boxes).
- Full-frame **meme cut-ins with their own sound**, labelled "Me" / "Bro's" (serif, no boxes).
- **Hook first** (a goal or a big chance), then lineups, kickoff and the match.
- Audio normalised to −14 LUFS for TikTok.

## Layout

| Path | What it is |
|---|---|
| `track.py` | Per-frame ball + cursor tracker (white ball blob, cyan controlled-player ring). |
| `autocam.py` | Virtual camera from the track: `render_box` (steady 4:3, current), `render_square` (1:1), `render` (zooming vertical). `force=[(t0, t1, cx, w[, "glide"])]` sets manual framing, e.g. for fast shots the tracker can't follow. |
| `captions.py` | Commentary text renderer (Anton + Noto Color Emoji). |
| `build2.py` | Shared helpers: "Me"/"Bro's" labels, sound trimming (`SFX`), meme registry (`MEMES`). |
| `build5.py` | 4:3 builder (game / meme / split pieces) and match 1's timeline. |
| `build6.py` | Match 2 timeline; shows how to register extra memes/sounds from `lib/`. |
| `build.py`, `build3.py`, `build4.py` | Earlier styles (v1 score-bar edit, v3 vertical, v4 square). |
| `lib/` | Meme library from Tenor (`L*.mp4`); `meta.txt` lists each clip's mood category, name, length and size. |
| `mm/`, `gif/` | Memes used in the first videos. |
| `snd/` | Meme sound bites from MyInstants. Trim points live in `SFX` (build2.py / build6.py). |
| `fonts/` | Anton (commentary) and PT Serif Bold (labels). |
| `videos/` | Finished videos and the 1:1 vs 4:3 vs 16:9 comparison. |

## Making a new video

1. Download the recording to `m3/match.mp4` (or similar). Raw recordings are not committed — they are
   600–700 MB, above GitHub's 100 MB file limit.
2. Copy `build6.py` to `build7.py`, point `SRC`/`OUT` at the new files and write the timeline `P`:
   - `game` pieces: source `start`/`end` seconds, `caps` (commentary), optional `labels`, `ovl` (corner meme), `sfx`.
   - `meme` pieces: `m` (key in `MEMES`), `dur`, `sfx` (key in `SFX`), `label`.
   - `split` piece: gameplay on top, meme below.
3. Run `python build7.py` (or `python build7.py 4 9` to rebuild only some pieces), then normalise and encode:

```bash
I=$(ffmpeg -i out7/joined.mkv -vn -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1 | awk '{print $2}')
ffmpeg -i out7/joined.mkv -af "volume=$(python3 -c "print(-14-($I))")dB,alimiter=limit=0.89:level=false" \
  -c:v libx264 -preset slow -b:v 3800k -maxrate 5500k -bufsize 8000k -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -movflags +faststart final.mp4
```

4. Check every goal frame by frame; if the ball leaves the frame on a shot, add a `force` glide to that piece.

## Requirements

`ffmpeg` (6.x) and Python 3 with the packages in `requirements.txt`.
