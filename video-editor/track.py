"""Per-frame ball + cursor tracker for the eFootball recording (1560x720)."""
import json, subprocess, sys
import cv2, numpy as np

SRC_W, SRC_H, FPS = 1560, 720, 30
FIELD = (42, 575)            # rows that hold the pitch (skip scoreboard bar and radar)
RADAR = (680, 880, 560, 720)  # x0, x1, y0, y1 of the radar / buttons to ignore


def frames(src, start, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", src,
           "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = SRC_W * SRC_H * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(SRC_H, SRC_W, 3)
    p.wait()


def detect(im):
    b, g, r = (im[:, :, i].astype(np.int16) for i in range(3))
    y0, y1 = FIELD
    # pitch check: mostly green frame means live gameplay (not a cutscene / menu)
    sub = im[y0:y1:8, ::8].astype(np.int16)
    green = np.mean((sub[:, :, 1] > sub[:, :, 2] + 25) & (sub[:, :, 1] > sub[:, :, 0] + 10))
    cyan = (r < 110) & (g > 170) & (b > 160) & (np.abs(g - b) < 70)
    cyan[:y0] = False; cyan[y1:] = False
    cyan[:64, :540] = False; cyan[:80, 1240:] = False
    cur = None
    ys, xs = np.nonzero(cyan)
    if len(xs) > 60:
        cur = (float(np.median(xs)), float(np.median(ys)))
    white = ((r > 212) & (g > 212) & (b > 212)).astype(np.uint8)
    white[:y0] = 0; white[y1:] = 0
    x0, x1, ry0, ry1 = RADAR
    white[ry0:ry1, x0:x1] = 0
    white[:64, :540] = 0          # scoreboard
    white[:80, 1240:] = 0         # pause / record buttons
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    balls = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if 10 <= a <= 220 and 0.55 < w / h < 1.8 and a / (w * h) > 0.45 and w <= 18:
            # must sit on grass: the ring around the blob is mostly green
            xa, xb, ya, yb = max(0, x - 10), min(SRC_W, x + w + 10), max(0, y - 10), min(SRC_H, y + h + 10)
            pg, pr, pb = g[ya:yb, xa:xb], r[ya:yb, xa:xb], b[ya:yb, xa:xb]
            grass = np.mean((pg > pb + 20) & (pg > pr + 5))
            if grass > 0.25:
                balls.append((float(cen[i][0]), float(cen[i][1]), int(a)))
    if not balls and cur:
        # far-side / shaded ball: looser whiteness, but only right at the controlled player's feet
        loose = ((r > 195) & (g > 195) & (b > 195)).astype(np.uint8)
        xa, xb = int(max(0, cur[0] - 90)), int(min(SRC_W, cur[0] + 90))
        ya, yb = int(max(y0, cur[1] - 70)), int(min(y1, cur[1] + 70))
        n2, _, st2, cen2 = cv2.connectedComponentsWithStats(loose[ya:yb, xa:xb])
        best = None
        for i in range(1, n2):
            x, y, w, h, a = st2[i]
            if 5 <= a <= 160 and 0.5 < w / h < 2 and a / (w * h) > 0.4 and w <= 16:
                c = (cen2[i][0] + xa, cen2[i][1] + ya)
                d = (c[0] - cur[0]) ** 2 + (c[1] - cur[1]) ** 2
                if best is None or d < best[0]:
                    best = (d, c)
        if best:
            balls.append((float(best[1][0]), float(best[1][1]), 0))
    return green, cur, balls


def track(src, start, dur):
    out, prev = [], None
    miss = drift = 0
    for k, im in enumerate(frames(src, start, dur)):
        green, cur, balls = detect(im)
        ball = None
        if balls:
            ref = prev or (cur[0], cur[1]) if (prev or cur) else None
            if ref:
                cands = sorted(balls, key=lambda c: (c[0] - ref[0]) ** 2 + (c[1] - ref[1]) ** 2)
                c = cands[0]
                lim = 90 + 40 * min(miss, 10)
                if (c[0] - ref[0]) ** 2 + (c[1] - ref[1]) ** 2 <= lim ** 2:
                    ball = (c[0], c[1])
            elif len(balls) == 1:
                ball = balls[0][:2]
        # re-lock: if the track has drifted far from the controlled player, take the blob at his feet
        if cur and balls:
            near = min(balls, key=lambda c: (c[0] - cur[0]) ** 2 + (c[1] - cur[1]) ** 2)
            dn = ((near[0] - cur[0]) ** 2 + (near[1] - cur[1]) ** 2) ** 0.5
            far = not ball or ((ball[0] - cur[0]) ** 2 + (ball[1] - cur[1]) ** 2) ** 0.5 > 350
            drift = drift + 1 if far else 0
            if dn < 70 and drift > 12:
                ball, drift = near[:2], 0
        if ball:
            prev, miss = ball, 0
        else:
            miss += 1
            if miss > 45:
                prev = None
        out.append(dict(t=round(k / FPS, 3), green=round(float(green), 3),
                        cur=cur and [round(cur[0]), round(cur[1])],
                        ball=ball and [round(ball[0]), round(ball[1])]))
    return out


if __name__ == "__main__":
    src, start, dur, dst = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    json.dump(track(src, start, dur), open(dst, "w"))
