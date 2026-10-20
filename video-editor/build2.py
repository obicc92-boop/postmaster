#!/usr/bin/env python3
"""v2: reference-style edit — black frame, big square pitch, full-screen meme
cut-ins with their own sound, "Me" / "Bro's" labels, no text boxes, loops."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W = os.path.dirname(os.path.abspath(__file__))
SRC = f"{W}/dl/match.mp4"
OUT = f"{W}/out2"
for d in ("png", "seg", "snd"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

SERIF = f"{W}/fonts/Serif-Bold.ttf"
SQ_Y, SQ, CROP = 420, 1080, 720      # square on canvas; square crop in source px
FPS = 30
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), "-pix_fmt", "yuv420p",
       "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]

# ---------------------------------------------------------------- labels
def label_png(text, style, size=128):
    """'me' = yellow serif with dark outline, 'bro' = red serif with white outline (as in the reference)."""
    p = f"{OUT}/png/{style}_{text.replace(' ', '_').replace(chr(39), '')}_{size}.png"
    if os.path.exists(p):
        return p
    f = ImageFont.truetype(SERIF, size)
    fill, stroke, sw = ((255, 214, 0), (25, 15, 0), 7) if style == "me" else ((214, 20, 28), (255, 255, 255), 5)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    img = Image.new("RGBA", (r - l + 24, b - t + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((12 - l + 5, 12 - t + 6), text, font=f, fill=(0, 0, 0, 140), stroke_width=sw, stroke_fill=(0, 0, 0, 140))
    d.text((12 - l, 12 - t), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    img.save(p)
    return p

# ---------------------------------------------------------------- sounds
SFX = {  # name: (file, start, end) — trimmed to the usable words
    "hellnah": ("hellnah", 0.0, 3.36),   # "Oh my god… hell no man" (cut before the swearing)
    "siu": ("siu", 4.5, 6.5),
    "laugh": ("laugh", 0.0, 1.9),
    "letsgo": ("letsgo", 0.0, 2.2),
    "hehe": ("hehe", 0.2, 1.6),
    "omg": ("omg", 0.0, 1.5),
    "boom": ("boom", 0.0, 1.3),
    "bruh": ("bruh", 0.0, 0.86),
    "noo": ("noo", 0.05, 1.25),
    "violin": ("violin", 0.0, 4.6),
    "damage": ("damage", 0.3, 3.3),
}

def sfx_wav(name):
    f, a, b = SFX[name]
    p = f"{OUT}/snd/{name}.wav"
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", f"{b - a:.3f}", "-i", f"{W}/snd/{f}.mp3",
                        "-af", "loudnorm=I=-13:TP=-1.5:LRA=11,afade=t=out:st=%.3f:d=0.08" % max(b - a - 0.08, 0),
                        "-ar", "48000", "-ac", "2", p], check=True)
    return p

MEMES = {  # name: (path, is_gif)
    "dog": ("mm/m6.mp4", False), "speedbw": ("mm/m1.mp4", False), "speed": ("mm/m2.mp4", False),
    "monkey": ("mm/m3.mp4", False), "monkey2": ("mm/m14.mp4", False), "baby": ("mm/m4.mp4", False),
    "rage": ("mm/m8.mp4", False, "crop=640:328:0:0,"), "cry": ("mm/m13.mp4", False), "penguin": ("mm/m12.mp4", False),
    "siu": ("gif/c2.gif", True), "ace": ("gif/c3.gif", True),
}

def meme_input(name):
    path, gif = MEMES[name][:2]
    return (["-ignore_loop", "0"] if gif else ["-stream_loop", "-1"]) + ["-i", f"{W}/{path}"]

def lerp_expr(keys):
    def cx(c):
        return max(0, min(1560 - CROP, c - CROP // 2))
    pts = [(t, cx(c)) for t, c in keys]
    expr = str(pts[-1][1])
    for (t0, x0), (t1, x1) in reversed(list(zip(pts, pts[1:]))):
        expr = f"if(lt(t,{t1:.3f}),{x0}+({x1}-{x0})*(t-{t0:.3f})/{max(t1 - t0, 0.001):.3f},{expr})"
    return f"if(lt(t,{pts[0][0]:.3f}),{pts[0][1]},{expr})"

# ---------------------------------------------------------------- timeline
# game: source window; labels = (text, style, cx, y, t0_src, t1_src); sfx = (name, at_src, vol)
# ovl = (meme, at_src, dur, width, x, y); meme: full-screen cut-in with its own sound
P = [
    dict(kind="meme", m="dog", dur=3.3, sfx="hellnah", label=("Me", "me", 540, SQ_Y + 120)),
    dict(kind="game", start=33.4, end=38.0, fit=True,
         labels=[("Bro's", "bro", 300, 600, 33.4, 38.0), ("Me", "me", 760, 600, 33.4, 38.0)]),
    dict(kind="game", start=144, end=157.0, crop=[(144, 700), (151, 700), (153, 560), (154.5, 400), (157, 380)]),
    dict(kind="meme", m="siu", dur=2.1, sfx="siu", label=("Me", "me", 820, SQ_Y + 60)),
    dict(kind="game", start=173, end=183.0, crop=[(173, 780), (178, 780), (179.5, 520), (180.5, 400), (183, 400)]),
    dict(kind="meme", m="baby", dur=1.9, sfx="laugh", label=("Me", "me", 820, SQ_Y + 60)),
    dict(kind="game", start=214, end=225, crop=[(214, 780), (218, 820), (220, 950), (223, 950), (223.5, 780), (225, 780)],
         ovl=[("monkey2", 222.2, 2.8, 380, 30, None)], sfx=[("bruh", 222.2, 1.0)],
         labels=[("Me", "me", 220, None, 222.2, 225)]),
    dict(kind="game", start=243, end=256.2, crop=[(243, 780), (252, 700), (253.5, 450), (255, 380), (256.2, 380)]),
    dict(kind="meme", m="ace", dur=2.2, sfx="letsgo", label=("Me", "me", 540, SQ_Y + 60)),
    dict(kind="game", start=299.2, end=301.8, crop=[(299, 780), (302, 780)]),
    dict(kind="meme", m="penguin", dur=1.6, sfx="hehe", label=("Me", "me", 540, SQ_Y + 40)),
    dict(kind="game", start=394, end=401.4, crop=[(394, 900), (396.5, 820), (398.5, 780), (399.3, 360), (401.4, 360)]),
    dict(kind="meme", m="speedbw", dur=1.6, sfx="omg", label=("Me", "me", 820, SQ_Y + 60)),
    dict(kind="game", start=474, end=483.9, crop=[(474, 780), (479, 780), (480.5, 600), (481.5, 400), (483.9, 380)],
         ovl=[("monkey", 482.2, 1.7, 360, 30, None)], sfx=[("boom", 482.1, 1.0)],
         labels=[("Me", "me", 210, None, 482.2, 483.9)]),
    dict(kind="game", start=550, end=559.6, crop=[(550, 900), (556, 820), (557, 560), (558.3, 400), (559.6, 400)]),
    dict(kind="meme", m="speed", dur=2.3, sfx="omg", label=("Me", "me", 540, SQ_Y + 40)),
    dict(kind="game", start=584.5, end=592, crop=[(584.5, 780), (587, 900), (589, 1000), (590.5, 1100), (592, 1000)],
         sfx=[("noo", 590.5, 1.0)]),
    dict(kind="game", start=597, end=606.0, crop=[(597, 780), (600, 800), (602, 640), (603, 430), (604.5, 430), (606, 700)]),
    dict(kind="split", start=606.0, end=611.5, cx=780, m="cry", sfx=("violin", 0.9), gamevol=0.45,
         labels=[("Bro's", "bro", 540, SQ_Y + 20), ("Me", "me", 860, SQ_Y + SQ // 2 + 20)]),
    dict(kind="game", start=656, end=658.6, crop=[(656, 780), (660, 780)]),
    dict(kind="meme", m="rage", dur=3.1, sfx="damage", label=("Me", "me", 540, SQ_Y + 40)),
    dict(kind="meme", m="dog", dur=0.9, sfx=None, label=("Me", "me", 540, SQ_Y + 120)),   # loops into the opening
]

def run(cmd):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cmd], check=True)

def build_meme(i, p):
    dur = p["dur"]
    lab = label_png(p["label"][0], p["label"][1])
    lw = Image.open(lab).width
    ins = ["-f", "lavfi", "-t", f"{dur}", "-i", f"color=black:s=1080x1920:r={FPS}", *meme_input(p["m"]),
           "-loop", "1", "-t", f"{dur}", "-i", lab]
    if p["sfx"]:
        ins += ["-i", sfx_wav(p["sfx"])]
    else:
        ins += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo"]
    pre = MEMES[p["m"]][2] if len(MEMES[p["m"]]) > 2 else ""
    f = [f"[1:v]{pre}fps={FPS},scale=1080:-2:flags=lanczos,crop=1080:'min(ih,1080)',setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[m]",
         f"[0:v][m]overlay=0:{SQ_Y}+({SQ}-h)/2[v0]",
         f"[v0][2:v]overlay={p['label'][2] - lw // 2}:{p['label'][3]}:enable='gte(t,0.08)',format=yuv420p[v]",
         f"[3:a]aresample=48000,apad,atrim=duration={dur}[a]"]
    return ins, f

def build_game(i, p):
    s, e = p["start"], p["end"]
    dur = e - s
    rel = lambda t: t - s
    ins = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=black:s=1080x1920:r={FPS}",
           "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    n = 2
    f = []
    if p.get("fit"):
        f.append(f"[1:v]fps={FPS},setpts=PTS-STARTPTS,scale=1080:-2:flags=lanczos[g]")
        f.append(f"[0:v][g]overlay=0:{SQ_Y}+({SQ}-h)/2[v0]")
    else:
        cx = lerp_expr([(rel(t), c) for t, c in p["crop"]])
        f.append(f"[1:v]fps={FPS},setpts=PTS-STARTPTS,crop={CROP}:{CROP}:'{cx}':0,scale={SQ}:{SQ}:flags=lanczos,"
                 f"eq=saturation=1.1:contrast=1.03[g]")
        f.append(f"[0:v][g]overlay=0:{SQ_Y}[v0]")
    last = "v0"
    ovl_top = {}
    for k, (m, at, d, w, x, y) in enumerate(p.get("ovl", [])):
        ins += meme_input(m)
        t0 = rel(at)
        f.append(f"[{n}:v]fps={FPS},scale={w}:-2,trim=duration={d},setpts=PTS-STARTPTS+{t0:.3f}/TB[o{k}]")
        yy = y if y is not None else f"{SQ_Y + SQ - 30}-h"
        f.append(f"[{last}][o{k}]overlay={x}:{yy}:eof_action=pass:enable='between(t,{t0:.3f},{t0 + d:.3f})'[ov{k}]")
        last = f"ov{k}"
        n += 1
        # remember overlay top so a label can sit above it
        h = int(w * {"monkey": 270 / 216, "monkey2": 498 / 376}.get(m, 1.0))
        ovl_top[k] = SQ_Y + SQ - 30 - h
    for k, (text, style, cx_, y, t0, t1) in enumerate(p.get("labels", [])):
        lab = label_png(text, style, 110 if p.get("ovl") else 128)
        im = Image.open(lab)
        if y is None:
            y = ovl_top.get(0, SQ_Y + 40) - im.height + 10
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx_ - im.width // 2}:{y}:enable='between(t,{rel(t0):.3f},{rel(t1):.3f})'[l{k}]")
        last = f"l{k}"
        n += 1
    f.append(f"[{last}]format=yuv420p[v]")
    # audio: game + sound effects
    amix = [f"[1:a]asetpts=PTS-STARTPTS,aresample=48000,volume={p.get('gamevol', 1.0)}[ga]"]
    labels_a = ["[ga]"]
    for k, (name, at, vol) in enumerate(p.get("sfx", [])):
        ins += ["-i", sfx_wav(name)]
        ms = int(rel(at) * 1000)
        amix.append(f"[{n}:a]volume={vol},adelay={ms}|{ms}[sx{k}]")
        labels_a.append(f"[sx{k}]")
        n += 1
    amix.append(f"{''.join(labels_a)}amix=inputs={len(labels_a)}:duration=first:normalize=0,"
                f"afade=t=in:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]")
    return ins, f + amix

def build_split(i, p):
    s, e = p["start"], p["end"]
    dur = e - s
    half = SQ // 2
    x0 = max(0, min(1560 - 1440, p["cx"] - 720))
    ins = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=black:s=1080x1920:r={FPS}",
           "-ss", f"{s:.3f}", "-t", f"{dur:.3f}", "-i", SRC, *meme_input(p["m"])]
    f = [f"[1:v]fps={FPS},setpts=PTS-STARTPTS,crop=1440:720:{x0}:0,scale=1080:{half}:flags=lanczos[top]",
         f"[2:v]fps={FPS},scale=1080:{half}:force_original_aspect_ratio=increase,crop=1080:{half},setsar=1,"
         f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[bot]",
         f"[0:v][top]overlay=0:{SQ_Y}[v0]", f"[v0][bot]overlay=0:{SQ_Y + half}[v1]"]
    last, n = "v1", 3
    for k, (text, style, cx_, y) in enumerate(p["labels"]):
        lab = label_png(text, style)
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", lab]
        f.append(f"[{last}][{n}:v]overlay={cx_ - Image.open(lab).width // 2}:{y}[l{k}]")
        last, n = f"l{k}", n + 1
    f.append(f"[{last}]format=yuv420p[v]")
    name, vol = p["sfx"]
    ins += ["-i", sfx_wav(name)]
    f.append(f"[1:a]asetpts=PTS-STARTPTS,aresample=48000,volume={p['gamevol']}[ga]")
    f.append(f"[{n}:a]volume={vol}[sx]")
    f.append(f"[ga][sx]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={dur - 0.08:.3f}:d=0.08[a]")
    return ins, f

def build(i, p):
    ins, f = {"meme": build_meme, "game": build_game, "split": build_split}[p["kind"]](i, p)
    dur = p.get("dur") or (p["end"] - p["start"])
    out = f"{OUT}/seg/{i:02d}.mkv"
    script = f"{OUT}/seg/{i:02d}.fg"
    open(script, "w").write(";\n".join(f))
    run([*ins, "-filter_complex_script", script, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", *ENC, out])
    return out

if __name__ == "__main__":
    only = {int(x) for x in sys.argv[1:]}
    outs = []
    for i, p in enumerate(P):
        out = f"{OUT}/seg/{i:02d}.mkv"
        if not only or i in only:
            print("piece", i, p["kind"], p.get("m") or p.get("start"), flush=True)
            build(i, p)
        outs.append(out)
    with open(f"{OUT}/list.txt", "w") as fh:
        fh.writelines(f"file '{o}'\n" for o in outs)
    run(["-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/joined.mkv"])
    print("joined")
