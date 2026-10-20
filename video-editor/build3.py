#!/usr/bin/env python3
"""v3: full-screen vertical with a ball-following camera (autocam), hook first,
then lineup, kickoff and the match. Meme cut-ins / labels as in v2."""
import os, subprocess, sys
from PIL import Image

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
import build2 as b2
from build2 import label_png, sfx_wav, meme_input, MEMES, run, FPS, ENC, SRC
import autocam

OUT = f"{W}/out3"
for d in ("seg", "base"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)
LABEL_Y = 430
MONKEY_BOTTOM = 1480       # keep overlays above TikTok's caption area

P = [
    dict(kind="game", start=585.0, end=592.0, sfx=[("noo", 590.5, 1.0)]),                       # hook
    dict(kind="meme", m="dog", dur=3.36, sfx="hellnah", label=("Me", "me")),
    dict(kind="fit", start=33.4, end=38.0, labels=[("Bro's", "bro", 300, 620), ("Me", "me", 760, 620)]),
    dict(kind="game", start=47.6, end=51.0),                                                      # kickoff
    dict(kind="game", start=144, end=157.0),
    dict(kind="meme", m="siu", dur=2.1, sfx="siu", label=("Me", "me")),
    dict(kind="game", start=173, end=183.0),
    dict(kind="meme", m="baby", dur=1.9, sfx="laugh", label=("Me", "me")),
    dict(kind="game", start=214, end=225, ovl=[("monkey2", 222.2, 2.8, 380)], sfx=[("bruh", 222.2, 1.0)]),
    dict(kind="game", start=243, end=256.2),
    dict(kind="meme", m="ace", dur=2.2, sfx="letsgo", label=("Me", "me")),
    dict(kind="game", start=299.2, end=301.8),
    dict(kind="meme", m="penguin", dur=1.6, sfx="hehe", label=("Me", "me")),
    dict(kind="game", start=394, end=401.4, force=[(5.2, 7.4, 560, 900)]),                        # red card
    dict(kind="meme", m="speedbw", dur=1.6, sfx="omg", label=("Me", "me")),
    dict(kind="game", start=474, end=483.9, ovl=[("monkey", 482.2, 1.7, 360)], sfx=[("boom", 482.1, 1.0)]),
    dict(kind="game", start=550, end=559.6),
    dict(kind="meme", m="speed", dur=2.3, sfx="boom", label=("Me", "me")),
    dict(kind="game", start=597, end=606.0),
    dict(kind="split", start=606.0, end=611.5, cx=780, m="cry", sfx=("violin", 0.9), gamevol=0.45),
    dict(kind="game", start=656, end=658.6, force=[(0, 2.6, 780, 1400)]),
    dict(kind="meme", m="rage", dur=3.1, sfx="damage", label=("Me", "me")),
]

BG = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:3,eq=brightness=-0.28"


def base_clip(p):
    out = f"{OUT}/base/{p['start']:.1f}_{p['end']:.1f}.mp4"
    if not os.path.exists(out):
        autocam.render(SRC, p["start"], p["end"] - p["start"], out, force=p.get("force", ()))
    return out


def build_meme(p):
    dur = p["dur"]
    lab = label_png(*p["label"])
    lw = Image.open(lab).width
    pre = MEMES[p["m"]][2] if len(MEMES[p["m"]]) > 2 else ""
    ins = [*meme_input(p["m"]), "-loop", "1", "-t", f"{dur}", "-i", lab, "-i", sfx_wav(p["sfx"])]
    f = [f"[0:v]{pre}fps={FPS},setsar=1,trim=duration={dur},setpts=PTS-STARTPTS,split[m0][m1]",
         f"[m0]{BG}[bg]",
         f"[m1]scale=1080:-2:flags=lanczos,crop=1080:'min(ih,1500)'[fg]",
         f"[bg][fg]overlay=0:(H-h)/2[v0]",
         f"[v0][1:v]overlay={540 - lw // 2}:{LABEL_Y}:enable='gte(t,0.08)',format=yuv420p[v]",
         f"[2:a]aresample=48000,apad,atrim=duration={dur}[a]"]
    return ins, f, dur


def game_audio(p, dur, n, ins, rel):
    a = [f"[ga_in]asetpts=PTS-STARTPTS,aresample=48000,volume={p.get('gamevol', 1.0)}[ga]"]
    labs = ["[ga]"]
    for k, (name, at, vol) in enumerate(p.get("sfx", [])):
        ins += ["-i", sfx_wav(name)]
        ms = int(rel(at) * 1000)
        a.append(f"[{n}:a]volume={vol},adelay={ms}|{ms}[sx{k}]")
        labs.append(f"[sx{k}]")
        n += 1
    a.append(f"{''.join(labs)}amix=inputs={len(labs)}:duration=first:normalize=0,"
             f"afade=t=in:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]")
    return a, n


def build_game(p):
    s, e = p["start"], p["end"]
    dur = e - s
    rel = lambda t: t - s
    ins = ["-i", base_clip(p), "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    f, last, n = ["[0:v]setpts=PTS-STARTPTS[v0]"], "v0", 2
    for k, (m, at, d, w) in enumerate(p.get("ovl", [])):
        ins += meme_input(m)
        t0 = rel(at)
        f.append(f"[{n}:v]fps={FPS},scale={w}:-2,trim=duration={d},setpts=PTS-STARTPTS+{t0:.3f}/TB[o{k}]")
        f.append(f"[{last}][o{k}]overlay=40:{MONKEY_BOTTOM}-h:eof_action=pass:enable='between(t,{t0:.3f},{t0 + d:.3f})'[ov{k}]")
        n += 1
        h = int(w * {"monkey": 270 / 216, "monkey2": 498 / 376}[m])
        lab = label_png("Me", "me", 110)
        im = Image.open(lab)
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[ov{k}][{n}:v]overlay={40 + w // 2 - im.width // 2}:{MONKEY_BOTTOM - h - im.height + 10}:"
                 f"enable='between(t,{t0:.3f},{t0 + d:.3f})'[lb{k}]")
        last, n = f"lb{k}", n + 1
    f.append(f"[{last}]format=yuv420p[v]")
    f.append("[1:a]anull[ga_in]")
    a, n = game_audio(p, dur, n, ins, rel)
    return ins, f + a, dur


def build_fit(p):
    s, e = p["start"], p["end"]
    dur = e - s
    ins = ["-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    f = [f"[0:v]fps={FPS},setpts=PTS-STARTPTS,split[a][b]", f"[a]{BG}[bg]",
         "[b]scale=1080:-2:flags=lanczos[fg]", "[bg][fg]overlay=0:(H-h)/2[v0]"]
    last, n = "v0", 1
    for k, (text, style, cx, y) in enumerate(p["labels"]):
        lab = label_png(text, style)
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx - Image.open(lab).width // 2}:{y}[l{k}]")
        last, n = f"l{k}", n + 1
    f.append(f"[{last}]format=yuv420p[v]")
    f.append("[0:a]anull[ga_in]")
    a, n = game_audio(p, dur, n, ins, lambda t: t - s)
    return ins, f + a, dur


def build_split(p):
    s, e = p["start"], p["end"]
    dur = e - s
    x0 = max(0, min(1560 - 810, p["cx"] - 405))
    ins = ["-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC, *meme_input(p["m"])]
    f = [f"[0:v]fps={FPS},setpts=PTS-STARTPTS,crop=810:720:{x0}:0,scale=1080:960:flags=lanczos[top]",
         f"[1:v]fps={FPS},scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,"
         f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[bot]",
         "[top][bot]vstack[v0]"]
    last, n = "v0", 2
    for k, (text, style, cx, y) in enumerate([("Bro's", "bro", 540, 140), ("Me", "me", 820, 1010)]):
        lab = label_png(text, style)
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx - Image.open(lab).width // 2}:{y}[l{k}]")
        last, n = f"l{k}", n + 1
    f.append(f"[{last}]format=yuv420p[v]")
    name, vol = p["sfx"]
    ins += ["-i", sfx_wav(name)]
    f += [f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,volume={p['gamevol']}[ga]", f"[{n}:a]volume={vol}[sx]",
          f"[ga][sx]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]"]
    return ins, f


def build(i, p):
    kind = p["kind"]
    if kind == "split":
        (ins, f), dur = build_split(p), p["end"] - p["start"]
    else:
        ins, f, dur = {"meme": build_meme, "game": build_game, "fit": build_fit}[kind](p)
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
