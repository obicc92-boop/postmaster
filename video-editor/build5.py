#!/usr/bin/env python3
"""v5: steady 4:3 box (960x720 of the source -> 1080x810), panned with the ball, plus short
v1-style commentary in the black space above the video. Memes / labels / sounds as v4."""
import os, sys
from PIL import Image

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
import build2 as b2
from build2 import label_png, sfx_wav, meme_input, MEMES, run, FPS, ENC, SRC
import autocam, captions
from captions import YELLOW, WHITE

OUT = f"{W}/out5"
b2.OUT = OUT
for d in ("seg", "base", "png", "snd"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

CROP_W = 960
BOX_W, BOX_H = 1080, 810
BOX_Y = (1920 - BOX_H) // 2            # 555
CAP_BOTTOM = BOX_Y - 25                # commentary sits just above the video
LT = BOX_Y + 30                        # "Me" / "Bro's" label row inside the box


def X(src_x):                           # source x -> canvas x for a box centred at 780
    return int((src_x - (780 - CROP_W // 2)) * BOX_W / CROP_W)


P = [
    dict(kind="game", start=585.0, end=592.0, sfx=[("noo", 590.5, 1.0)],
         caps=[(585.0, ["88TH MINUTE, 3-3… 😳"], WHITE), (590.4, ["SO CLOSE 😩"], YELLOW)]),
    dict(kind="meme", m="dog", dur=3.36, sfx="hellnah", label=("Me", "me", 540, LT + 60),
         caps=[(0, ["SO CLOSE 😩"], YELLOW)]),
    dict(kind="game", start=34.0, end=38.0, force=[(0, 4.0, 780, 0)],
         labels=[("Bro's", "bro", 175, LT, 34.0, 38.0), ("Me", "me", X(1100), LT, 34.0, 38.0)],
         caps=[(34.0, ["ME vs BRO 🎮"], WHITE)]),
    dict(kind="game", start=47.6, end=51.0, caps=[(47.6, ["LET'S GO ⚽"], WHITE)]),
    dict(kind="game", start=144, end=157.0, caps=[(154.8, ["GOAL!! ⚽🔥"], YELLOW)]),
    dict(kind="meme", m="siu", dur=2.1, sfx="siu", label=("Me", "me", 820, LT), caps=[(0, ["GOAL!! ⚽🔥"], YELLOW)]),
    dict(kind="game", start=173, end=183.0, caps=[(180.4, ["WHAT A FINISH 🚀"], YELLOW)]),
    dict(kind="meme", m="baby", dur=1.9, sfx="laugh", label=("Me", "me", 820, LT),
         caps=[(0, ["WHAT A FINISH 🚀"], YELLOW)]),
    dict(kind="game", start=214, end=225, ovl=[("monkey2", 222.2, 2.8, 300)], sfx=[("bruh", 222.2, 1.0)],
         labels=[("Me", "me", 190, None, 222.2, 225)], caps=[(221.3, ["MESSI HAD TO RUIN IT 😒"], WHITE)]),
    dict(kind="game", start=243, end=256.2, force=[(10.9, 13.2, 470, 0, "glide")], caps=[(254.4, ["ANOTHER ONE 😎🔥"], YELLOW)]),
    dict(kind="meme", m="ace", dur=2.2, sfx="letsgo", label=("Me", "me", 540, LT),
         caps=[(0, ["ANOTHER ONE 😎🔥"], YELLOW)]),
    dict(kind="game", start=299.2, end=301.8, caps=[(299.2, ["HALF TIME: 3-1", "EASY WIN… RIGHT? 🤡"], YELLOW)]),
    dict(kind="meme", m="penguin", dur=1.6, sfx="hehe", label=("Me", "me", 540, LT),
         caps=[(0, ["HALF TIME: 3-1", "EASY WIN… RIGHT? 🤡"], YELLOW)]),
    dict(kind="game", start=394, end=401.4, force=[(5.2, 7.4, 500, 0)],
         caps=[(399.4, ["RED CARD?! 🟥😡", "REF WAS PAID 💀"], WHITE)]),
    dict(kind="meme", m="speedbw", dur=1.6, sfx="omg", label=("Me", "me", 820, LT),
         caps=[(0, ["RED CARD?! 🟥😡", "REF WAS PAID 💀"], WHITE)]),
    dict(kind="game", start=474, end=483.9, ovl=[("monkey", 482.2, 1.7, 280)], sfx=[("boom", 482.1, 1.0)],
         labels=[("Me", "me", 180, None, 482.2, 483.9)], caps=[(482.0, ["UH OH… 😬"], WHITE)]),
    dict(kind="game", start=550, end=559.6, caps=[(557.6, ["3-3?!?! 💀"], WHITE)]),
    dict(kind="meme", m="speed", dur=2.3, sfx="boom", label=("Me", "me", 540, LT), caps=[(0, ["3-3?!?! 💀"], WHITE)]),
    dict(kind="game", start=597, end=606.0, caps=[(604.3, ["NAHHH 😭😭😭"], WHITE)]),
    dict(kind="split", start=606.0, end=611.5, m="cry", sfx=("violin", 0.9), gamevol=0.45,
         caps=[(0, ["NAHHH 😭😭😭"], WHITE)]),
    dict(kind="game", start=656, end=658.6, force=[(0, 2.6, 780, 0)],
         caps=[(656.2, ["FULL TIME 3-4", "I'M DELETING THE GAME 💀"], YELLOW)]),
    dict(kind="meme", m="rage", dur=3.1, sfx="damage", label=("Me", "me", 540, LT),
         caps=[(0, ["FULL TIME 3-4", "I'M DELETING THE GAME 💀"], YELLOW)]),
]

MONKEY_H = {"monkey": 270 / 216, "monkey2": 498 / 376}
_cap_n = [0]


def cap_png(lines, colour):
    _cap_n[0] += 1
    p = f"{OUT}/png/cap{_cap_n[0]:02d}.png"
    size = 76 if len(lines) == 1 else 64
    img = captions.render_text(lines, size, colour, 7)
    if img.width > 1040:                       # keep inside the screen
        img = img.resize((1040, int(img.height * 1040 / img.width)), Image.LANCZOS)
    img.save(p)
    return p, img.height


def add_caps(p, f, ins, last, n, dur, rel):
    """Commentary lines above the box; each pops in at its time and stays until the next one."""
    caps = p.get("caps", [])
    for k, (t, lines, col) in enumerate(caps):
        t0 = max(0.0, rel(t))
        t1 = rel(caps[k + 1][0]) if k + 1 < len(caps) else dur + 1
        png, h = cap_png(lines, col)
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", png]
        pop = f"if(lt(t-{t0:.3f},0.10),0.6+(t-{t0:.3f})*4.5,if(lt(t-{t0:.3f},0.2),1.05-(t-{t0:.3f}-0.1)*0.5,1))"
        f.append(f"[{n}:v]scale=w='trunc(iw*{pop}/2)*2':h=-2:eval=frame[c{k}]")
        f.append(f"[{last}][c{k}]overlay=x=(W-w)/2:y={CAP_BOTTOM}-h:enable='between(t,{t0:.3f},{t1:.3f})'[cc{k}]")
        last, n = f"cc{k}", n + 1
    return last, n


def add_labels(p, f, ins, last, n, dur, rel, ovl_top=None):
    for k, (text, style, cx, y, t0, t1) in enumerate(p.get("labels", [])):
        lab = label_png(text, style, 100 if p.get("ovl") else 120)
        im = Image.open(lab)
        if y is None:
            y = ovl_top - im.height + 10
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx - im.width // 2}:{y}:enable='between(t,{rel(t0):.3f},{rel(t1):.3f})'[l{k}]")
        last, n = f"l{k}", n + 1
    return last, n


def mix_audio(p, f, ins, n, dur, rel, src_label="[1:a]", vol=1.0):
    f.append(f"{src_label}asetpts=PTS-STARTPTS,aresample=48000,volume={vol}[ga]")
    labs = ["[ga]"]
    for k, (name, at, v) in enumerate(p.get("sfx", [])):
        ins += ["-i", sfx_wav(name)]
        ms = int(rel(at) * 1000)
        f.append(f"[{n}:a]volume={v},adelay={ms}|{ms}[sx{k}]")
        labs.append(f"[sx{k}]")
        n += 1
    f.append(f"{''.join(labs)}amix=inputs={len(labs)}:duration=first:normalize=0,"
             f"afade=t=in:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]")


def build_game(p):
    s, e = p["start"], p["end"]
    dur = e - s
    rel = lambda t: t - s
    base = f"{OUT}/base/{s:.1f}_{e:.1f}.mp4"
    if not os.path.exists(base):
        autocam.render_box(SRC, s, dur, base, CROP_W, BOX_Y, force=p.get("force", ()))
    ins = ["-i", base, "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    f, last, n = ["[0:v]setpts=PTS-STARTPTS[v0]"], "v0", 2
    ovl_top = None
    for k, (m, at, d, w) in enumerate(p.get("ovl", [])):
        ins += meme_input(m)
        t0 = rel(at)
        bottom = BOX_Y + BOX_H - 20
        f.append(f"[{n}:v]fps={FPS},scale={w}:-2,trim=duration={d},setpts=PTS-STARTPTS+{t0:.3f}/TB[o{k}]")
        f.append(f"[{last}][o{k}]overlay=30:{bottom}-h:eof_action=pass:enable='between(t,{t0:.3f},{t0 + d:.3f})'[ov{k}]")
        last, n = f"ov{k}", n + 1
        ovl_top = bottom - int(w * MONKEY_H[m])
    last, n = add_labels(p, f, ins, last, n, dur, rel, ovl_top)
    last, n = add_caps(p, f, ins, last, n, dur, rel)
    f.append(f"[{last}]format=yuv420p[v]")
    mix_audio(p, f, ins, n, dur, rel)
    return ins, f, dur


def build_meme(p):
    dur = p["dur"]
    pre = MEMES[p["m"]][2] if len(MEMES[p["m"]]) > 2 else ""
    ins = ["-f", "lavfi", "-t", f"{dur}", "-i", f"color=black:s=1080x1920:r={FPS}", *meme_input(p["m"])]
    f = [f"[1:v]{pre}fps={FPS},scale={BOX_W}:{BOX_H}:force_original_aspect_ratio=increase,crop={BOX_W}:{BOX_H},"
         f"setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[m]", f"[0:v][m]overlay=0:{BOX_Y}[v0]"]
    text, style, cx, y = p["label"]
    p = dict(p, labels=[(text, style, cx, y, 0.08, dur)])
    last, n = add_labels(p, f, ins, "v0", 2, dur, lambda t: t)
    last, n = add_caps(p, f, ins, last, n, dur, lambda t: t)
    f.append(f"[{last}]format=yuv420p[v]")
    ins += ["-i", sfx_wav(p["sfx"])]
    f.append(f"[{n}:a]aresample=48000,apad,atrim=duration={dur}[a]")
    return ins, f, dur


def build_split(p):
    s, e = p["start"], p["end"]
    dur = e - s
    half = BOX_H // 2
    ins = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=black:s=1080x1920:r={FPS}",
           "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC, *meme_input(p["m"])]
    f = [f"[1:v]fps={FPS},setpts=PTS-STARTPTS,crop=1560:585:0:40,scale={BOX_W}:{half}[top]",
         f"[2:v]fps={FPS},scale={BOX_W}:{half}:force_original_aspect_ratio=increase,crop={BOX_W}:{half},setsar=1,"
         f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[bot]",
         f"[0:v][top]overlay=0:{BOX_Y}[v0]", f"[v0][bot]overlay=0:{BOX_Y + half}[v1]"]
    p = dict(p, labels=[("Bro's", "bro", 540, BOX_Y + 10, s, e), ("Me", "me", 860, BOX_Y + half + 10, s, e)])
    rel = lambda t: t - s
    last, n = add_labels(dict(p, ovl=[1]), f, ins, "v1", 3, dur, rel)
    last, n = add_caps(dict(p, caps=[(s, *p["caps"][0][1:])]), f, ins, last, n, dur, rel)
    f.append(f"[{last}]format=yuv420p[v]")
    name, vol = p["sfx"]
    mix_audio(dict(p, sfx=[(name, s, vol)]), f, ins, n, dur, rel, "[1:a]", p["gamevol"])
    return ins, f, dur


def build(i, p):
    ins, f, dur = {"game": build_game, "meme": build_meme, "split": build_split}[p["kind"]](p)
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
