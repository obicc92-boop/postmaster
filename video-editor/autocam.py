"""Ball-following virtual camera: 9:16 full screen when play is tight, zooms out
on shots / long balls so the ball, the player on it and the goal stay in frame."""
import json, os, subprocess, sys
import cv2, numpy as np
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from track import track, frames, SRC_W, SRC_H, FPS

OUT_W, OUT_H = 1080, 1920
MIN_W = SRC_H * OUT_W / OUT_H     # 405 px: crop width that fills the 9:16 screen
MARGIN = 75                       # px kept around the action on each side
BEHIND, AHEAD = 8, 24            # frames of track the camera "sees" (looks ahead to anticipate shots)


def plan(trk, force=(), fixed_w=None):
    n = len(trk)
    green = np.array([f["green"] for f in trk])
    live = green > 0.45
    bx = np.full(n, np.nan)
    for k, f in enumerate(trk):
        if f["ball"]:
            bx[k] = f["ball"][0]
    # drop isolated jumps (white socks, line crossings)
    idx = np.nonzero(~np.isnan(bx))[0]
    for k in idx:
        nb = [bx[j] for j in idx if abs(j - k) <= 5 and j != k]
        if len(nb) >= 2 and abs(bx[k] - np.median(nb)) > 140:
            bx[k] = np.nan
    cur = np.array([f["cur"][0] if f["cur"] else np.nan for f in trk])
    # fill: interpolate short gaps in the ball track, else follow the cursor
    fx = bx.copy()
    idx = np.nonzero(~np.isnan(bx))[0]
    for a, b in zip(idx, idx[1:]):
        if 1 < b - a <= 45:
            fx[a + 1:b] = np.interp(np.arange(a + 1, b), [a, b], [bx[a], bx[b]])
    gap = np.isnan(fx) & ~np.isnan(cur)
    fx[gap] = cur[gap]
    # hold last known position through anything still missing
    last = SRC_W / 2
    for k in range(n):
        if np.isnan(fx[k]) or not live[k]:
            fx[k] = last if live[k] else np.nan
        else:
            last = fx[k]
    cx = np.full(n, SRC_W / 2)
    w = np.full(n, 1000.0)
    for k in range(n):
        if not live[k]:
            continue
        cw = cur[max(0, k - 2):k + 8]
        cw = cw[np.abs(cw - fx[k]) < 300] if not np.isnan(fx[k]) else cw
        win = np.concatenate([fx[max(0, k - BEHIND):k + AHEAD], cw])
        win = win[~np.isnan(win)]
        if not len(win):
            win = np.array([cx[k - 1] if k else SRC_W / 2])
        lo, hi = win.min(), win.max()
        w[k] = np.clip(hi - lo + 2 * MARGIN, MIN_W, SRC_W)
        cx[k] = (lo + hi) / 2
    # smooth within each live / cutscene run separately (hard cut between them)
    k = 0
    while k < n:
        j = k
        while j < n and live[j] == live[k]:
            j += 1
        if j - k > 3:
            cx[k:j] = gaussian_filter1d(cx[k:j], 14 if fixed_w else 7, mode="nearest")
            w[k:j] = gaussian_filter1d(w[k:j], 9, mode="nearest")
        k = j
    for t0, t1, fcx, fw, *glide in force:  # manual framing (cutscenes, shots the tracker can't follow)
        a, b = int(t0 * FPS), int(t1 * FPS)
        cx[a:b], w[a:b] = fcx, fw
        if glide:                          # ease in/out instead of a hard cut
            lo, hi = max(0, a - 20), min(n, b + 20)
            cx[lo:hi] = gaussian_filter1d(cx[lo:hi], 6, mode="nearest")
    w = np.full(n, float(fixed_w)) if fixed_w else np.clip(w, MIN_W, SRC_W)
    x0 = np.clip(cx - w / 2, 0, SRC_W - w)
    return x0, w, live


def render(src, start, dur, out, trk=None, force=()):
    trk = trk or track(src, start, dur)
    x0, w, live = plan(trk, force)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for k, im in enumerate(frames(src, start, dur)):
        if k >= len(w):
            break
        cw = float(w[k])
        xa = int(round(x0[k]))
        xb = min(SRC_W, int(round(x0[k] + cw)))
        crop = im[:, xa:xb]
        h = int(round(OUT_W * SRC_H / crop.shape[1]))
        h = min(OUT_H, h + (h % 2))
        canvas = cv2.resize(cv2.resize(crop, (54, 96), interpolation=cv2.INTER_AREA), (OUT_W, OUT_H),
                            interpolation=cv2.INTER_CUBIC)
        canvas = cv2.GaussianBlur(canvas, (0, 0), 18)
        canvas = (canvas * 0.38).astype(np.uint8)
        sharp = cv2.resize(crop, (OUT_W, h), interpolation=cv2.INTER_LANCZOS4)
        y = (OUT_H - h) // 2
        canvas[y:y + h] = sharp
        enc.stdin.write(canvas.tobytes())
    enc.stdin.close()
    enc.wait()
    return trk


if __name__ == "__main__":
    src, start, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    t = render(src, start, dur, out)
    json.dump(t, open(out + ".json", "w"))


SQ_Y, SQ = 420, 1080


def render_square(src, start, dur, out, trk=None, force=()):
    """Steady 1:1 square (720x720 of the source) that only pans with the play; black canvas."""
    trk = trk or track(src, start, dur)
    x0, w, live = plan(trk, [(a, b, c, SRC_H) for a, b, c, _ in force], fixed_w=SRC_H)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    canvas = np.zeros((OUT_H, OUT_W, 3), np.uint8)
    for k, im in enumerate(frames(src, start, dur)):
        if k >= len(w):
            break
        xa = int(round(x0[k]))
        canvas[SQ_Y:SQ_Y + SQ] = cv2.resize(im[:, xa:xa + SRC_H], (SQ, SQ), interpolation=cv2.INTER_LANCZOS4)
        enc.stdin.write(canvas.tobytes())
    enc.stdin.close()
    enc.wait()
    return trk


def render_box(src, start, dur, out, crop_w, box_y, force=()):
    """Steady box: crop_w x 720 of the source, panned with the play, scaled to 1080 wide on black."""
    trk = track(src, start, dur)
    x0, w, live = plan(trk, [(a, b, c, crop_w, *g) for a, b, c, _, *g in force], fixed_w=crop_w)
    bh = int(round(OUT_W * SRC_H / crop_w))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    canvas = np.zeros((OUT_H, OUT_W, 3), np.uint8)
    for k, im in enumerate(frames(src, start, dur)):
        if k >= len(w):
            break
        xa = int(round(x0[k]))
        canvas[box_y:box_y + bh] = cv2.resize(im[:, xa:xa + crop_w], (OUT_W, bh), interpolation=cv2.INTER_LANCZOS4)
        enc.stdin.write(canvas.tobytes())
    enc.stdin.close()
    enc.wait()
    return trk
