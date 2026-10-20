#!/usr/bin/env python3
"""v4: one steady 1:1 square for the whole video (no zoom changes). Gameplay square
pans smoothly with the ball (autocam.render_square); memes, labels, split as in v2."""
import os, sys
from PIL import Image

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
import build2 as b2
from build2 import label_png, sfx_wav, meme_input, run, FPS, ENC, SRC, SQ_Y, SQ
import autocam

OUT = f"{W}/out4"
b2.OUT = OUT
for d in ("seg", "base", "png", "snd"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

TOP = SQ_Y + 60
P = [
    dict(kind="game", start=585.0, end=592.0, sfx=[("noo", 590.5, 1.0)]),                        # hook
    dict(kind="meme", m="dog", dur=3.36, sfx="hellnah", label=("Me", "me", 540, SQ_Y + 120)),
    dict(kind="game", start=34.0, end=38.0, force=[(0, 4.0, 780, 0)],                              # lineup
         labels=[("Bro's", "bro", 300, TOP, 34.0, 38.0), ("Me", "me", 800, TOP, 34.0, 38.0)]),
    dict(kind="game", start=47.6, end=51.0),                                                       # kickoff
    dict(kind="game", start=144, end=157.0),
    dict(kind="meme", m="siu", dur=2.1, sfx="siu", label=("Me", "me", 820, TOP)),
    dict(kind="game", start=173, end=183.0),
    dict(kind="meme", m="baby", dur=1.9, sfx="laugh", label=("Me", "me", 820, TOP)),
    dict(kind="game", start=214, end=225, ovl=[("monkey2", 222.2, 2.8, 380)], sfx=[("bruh", 222.2, 1.0)],
         labels=[("Me", "me", 220, None, 222.2, 225)]),
    dict(kind="game", start=243, end=256.2),
    dict(kind="meme", m="ace", dur=2.2, sfx="letsgo", label=("Me", "me", 540, TOP)),
    dict(kind="game", start=299.2, end=301.8),
    dict(kind="meme", m="penguin", dur=1.6, sfx="hehe", label=("Me", "me", 540, SQ_Y + 40)),
    dict(kind="game", start=394, end=401.4, force=[(5.2, 7.4, 360, 0)]),                          # red card
    dict(kind="meme", m="speedbw", dur=1.6, sfx="omg", label=("Me", "me", 820, TOP)),
    dict(kind="game", start=474, end=483.9, ovl=[("monkey", 482.2, 1.7, 360)], sfx=[("boom", 482.1, 1.0)],
         labels=[("Me", "me", 210, None, 482.2, 483.9)]),
    dict(kind="game", start=550, end=559.6),
    dict(kind="meme", m="speed", dur=2.3, sfx="boom", label=("Me", "me", 540, SQ_Y + 40)),
    dict(kind="game", start=597, end=606.0),
    dict(kind="split", start=606.0, end=611.5, cx=780, m="cry", sfx=("violin", 0.9), gamevol=0.45,
         labels=[("Bro's", "bro", 540, SQ_Y + 20), ("Me", "me", 860, SQ_Y + SQ // 2 + 20)]),
    dict(kind="game", start=656, end=658.6, force=[(0, 2.6, 780, 0)]),
    dict(kind="meme", m="rage", dur=3.1, sfx="damage", label=("Me", "me", 540, SQ_Y + 40)),
]

MONKEY_H = {"monkey": 270 / 216, "monkey2": 498 / 376}


def build_game(p):
    s, e = p["start"], p["end"]
    dur = e - s
    rel = lambda t: t - s
    base = f"{OUT}/base/{s:.1f}_{e:.1f}.mp4"
    if not os.path.exists(base):
        autocam.render_square(SRC, s, dur, base, force=p.get("force", ()))
    ins = ["-i", base, "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    f, last, n = ["[0:v]setpts=PTS-STARTPTS[v0]"], "v0", 2
    ovl_top = None
    for k, (m, at, d, w) in enumerate(p.get("ovl", [])):
        ins += meme_input(m)
        t0 = rel(at)
        f.append(f"[{n}:v]fps={FPS},scale={w}:-2,trim=duration={d},setpts=PTS-STARTPTS+{t0:.3f}/TB[o{k}]")
        f.append(f"[{last}][o{k}]overlay=30:{SQ_Y + SQ - 30}-h:eof_action=pass:"
                 f"enable='between(t,{t0:.3f},{t0 + d:.3f})'[ov{k}]")
        last, n = f"ov{k}", n + 1
        ovl_top = SQ_Y + SQ - 30 - int(w * MONKEY_H[m])
    for k, (text, style, cx, y, t0, t1) in enumerate(p.get("labels", [])):
        lab = label_png(text, style, 110 if p.get("ovl") else 128)
        im = Image.open(lab)
        if y is None:
            y = ovl_top - im.height + 10
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx - im.width // 2}:{y}:enable='between(t,{rel(t0):.3f},{rel(t1):.3f})'[l{k}]")
        last, n = f"l{k}", n + 1
    f.append(f"[{last}]format=yuv420p[v]")
    a = [f"[1:a]asetpts=PTS-STARTPTS,aresample=48000[ga]"]
    labs = ["[ga]"]
    for k, (name, at, vol) in enumerate(p.get("sfx", [])):
        ins += ["-i", sfx_wav(name)]
        ms = int(rel(at) * 1000)
        a.append(f"[{n}:a]volume={vol},adelay={ms}|{ms}[sx{k}]")
        labs.append(f"[sx{k}]")
        n += 1
    a.append(f"{''.join(labs)}amix=inputs={len(labs)}:duration=first:normalize=0,"
             f"afade=t=in:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]")
    return ins, f + a, dur


def build(i, p):
    if p["kind"] != "game":
        return b2.build(i, p)          # meme / split: v2 square layouts, written to out4/seg
    ins, f, dur = build_game(p)
    out = f"{OUT}/seg/{i:02d}.mkv"
    script = f"{OUT}/seg/{i:02d}.fg"
    open(script, "w").write(";\n".join(f))
    run([*ins, "-filter_complex_script", script, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", *ENC, out])


if __name__ == "__main__":
    only = {int(x) for x in sys.argv[1:]}
    outs = []
    for i, p in enumerate(P):
        if not only or i in only:
            print("piece", i, p["kind"], p.get("m") or p.get("start"), flush=True)
            build(i, p)
        outs.append(f"{OUT}/seg/{i:02d}.mkv")
    with open(f"{OUT}/list.txt", "w") as fh:
        fh.writelines(f"file '{o}'\n" for o in outs)
    run(["-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/joined.mkv"])
    print("joined", flush=True)
