#!/usr/bin/env python3
"""Build a 1080x1920 TikTok highlight from the eFootball recording."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W = os.path.dirname(os.path.abspath(__file__))
SRC = f"{W}/dl/match.mp4"
OUT = f"{W}/out"
os.makedirs(f"{OUT}/png", exist_ok=True)
os.makedirs(f"{OUT}/seg", exist_ok=True)

ANTON = f"{W}/fonts/Anton.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW = (255, 221, 0)
WHITE = (255, 255, 255)

SQ_Y = 500          # top of the gameplay square
SQ = 1080           # square size on canvas
CROP = 720          # square crop size in source px (source is 1560x720)

# ---------------------------------------------------------------- text render
_emoji_font = ImageFont.truetype(EMOJI, 109)

def is_emoji(ch):
    return ord(ch) >= 0x2600 and ch != "…"

def render_text(lines, size, fill=WHITE, stroke=10, out=None, pad=24, bg=False):
    """Render lines (centered) with Anton + colour emoji, black stroke + shadow."""
    font = ImageFont.truetype(ANTON, size)
    asc, desc = font.getmetrics()
    lh = asc + desc
    rendered = []
    for line in lines:
        line = line.replace("️", "")
        parts = []  # (img, w)
        buf = ""
        def flush():
            nonlocal buf
            if buf:
                w = int(font.getlength(buf)) + stroke * 2
                im = Image.new("RGBA", (w, lh + stroke * 2), (0, 0, 0, 0))
                d = ImageDraw.Draw(im)
                d.text((stroke + 5, stroke + 6), buf, font=font, fill=(0, 0, 0, 160),
                       stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
                d.text((stroke, stroke), buf, font=font, fill=fill,
                       stroke_width=stroke, stroke_fill=(0, 0, 0))
                parts.append(im)
                buf = ""
        for ch in line:
            if is_emoji(ch):
                flush()
                e = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
                ImageDraw.Draw(e).text((0, 0), ch, font=_emoji_font, embedded_color=True)
                e = e.crop(e.getbbox())
                s = int(size * 0.95)
                e = e.resize((int(e.width * s / e.height), s), Image.LANCZOS)
                cell = Image.new("RGBA", (e.width + 8, lh + stroke * 2), (0, 0, 0, 0))
                cell.paste(e, (4, (lh + stroke * 2 - s) // 2), e)
                parts.append(cell)
            else:
                buf += ch
        flush()
        lw = sum(p.width for p in parts)
        li = Image.new("RGBA", (max(lw, 1), lh + stroke * 2), (0, 0, 0, 0))
        x = 0
        for p in parts:
            li.paste(p, (x, 0), p)
            x += p.width
        rendered.append(li)
    tw = max(r.width for r in rendered) + pad * 2
    th = sum(r.height for r in rendered) - (len(rendered) - 1) * int(size * 0.12) + pad * 2
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if bg:
        ImageDraw.Draw(img).rounded_rectangle((0, 0, tw - 1, th - 1), 30, fill=(10, 12, 30, 215),
                                              outline=YELLOW, width=5)
    y = pad
    for r in rendered:
        img.paste(r, ((tw - r.width) // 2, y), r)
        y += r.height - int(size * 0.12)
    if out:
        img.save(out)
    return img

def score_bug(home, away, out):
    """SOMTOO FC  h - a  BARCELONA pill."""
    img = Image.new("RGBA", (1000, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 999, 103), 26, fill=(14, 16, 40, 235), outline=YELLOW, width=4)
    f = ImageFont.truetype(ANTON, 52)
    fs = ImageFont.truetype(ANTON, 64)
    d.text((40, 52), "SOMTOO FC", font=f, fill=WHITE, anchor="lm")
    d.text((960, 52), "BARCELONA", font=f, fill=WHITE, anchor="rm")
    d.rounded_rectangle((405, 10, 595, 93), 16, fill=YELLOW)
    d.text((500, 50), f"{home} - {away}", font=fs, fill=(14, 16, 40), anchor="mm")
    img.save(out)

# ---------------------------------------------------------------- segments
# start/end are source seconds; crop = [(src_t, action_center_x)];
# cap = (src_t, [lines], colour); gifs = [(file, src_t, dur, width, x, y, chroma)]
SEGS = [
    dict(name="g1", start=144, end=157.5, score=[(144, 0, 0), (155.0, 1, 0)],
         crop=[(144, 700), (151, 700), (153, 560), (154.5, 400), (157.5, 380)],
         cap=(155.0, ["GOAL!! ⚽🔥"], YELLOW),
         gifs=[("c2", 155.3, 2.2, 300, 40, SQ_Y + 30, False)]),
    dict(name="g2", start=173, end=186, score=[(173, 1, 0), (180.4, 2, 0)],
         crop=[(173, 780), (178, 780), (179.5, 520), (180.5, 400), (182.5, 400), (183.5, 850), (186, 850)],
         cap=(180.4, ["WHAT A FINISH 🚀"], YELLOW),
         gifs=[("c3", 181.0, 3.0, 300, 40, SQ_Y + 30, False)]),
    dict(name="messi", start=214, end=225, score=[(214, 2, 0), (221.3, 2, 1)],
         crop=[(214, 780), (218, 820), (220, 950), (223, 950), (223.5, 780), (225, 780)],
         cap=(221.3, ["MESSI HAD TO RUIN IT 😒"], WHITE),
         gifs=[("c8", 221.6, 3.2, 260, 40, SQ_Y + 30, False)]),
    dict(name="g3", start=243, end=258, score=[(243, 2, 1), (254.4, 3, 1)],
         crop=[(243, 780), (252, 700), (253.5, 450), (255, 380), (258, 380)],
         cap=(254.4, ["ANOTHER ONE 😎🔥"], YELLOW),
         gifs=[("c4", 254.8, 3.0, 320, 40, SQ_Y + 30, False)]),
    dict(name="ht", start=299, end=302.8, score=[(299, 3, 1)],
         crop=[(299, 780), (302.8, 780)],
         cap=(299.2, ["HALF TIME: 3-1", "EASY WIN… RIGHT? 🤡"], YELLOW),
         gifs=[("c6", 299.3, 3.4, 300, 40, SQ_Y + 30, False)]),
    dict(name="red", start=394, end=401.4, score=[(394, 3, 1)],
         crop=[(394, 900), (396.5, 820), (398.5, 780), (399.3, 360), (401.4, 360)], cap_y=f"{SQ_Y + 40}",
         cap=(399.6, ["RED CARD?! 🟥😡", "REF WAS PAID 💀"], WHITE),
         gifs=[]),
    dict(name="b2", start=474, end=484, score=[(474, 3, 1), (482.0, 3, 2)],
         crop=[(474, 780), (479, 780), (480.5, 600), (481.5, 400), (484, 380)],
         cap=(482.0, ["UH OH… 😬"], WHITE),
         gifs=[]),
    dict(name="b3", start=550, end=565, score=[(550, 3, 2), (557.6, 3, 3)],
         crop=[(550, 900), (556, 820), (557, 560), (558.3, 400), (559.6, 400), (560.2, 800), (565, 800)],
         cap=(557.6, ["3-3?!?! 💀"], WHITE),
         gifs=[("c7", 558.0, 4.5, 330, 40, SQ_Y + 30, True)]),
    dict(name="miss", start=584.5, end=592, score=[(584.5, 3, 3)],
         crop=[(584.5, 780), (587, 900), (589, 1000), (590.5, 1100), (592, 1000)],
         cap=(590.2, ["SO CLOSE 😩"], YELLOW),
         gifs=[]),
    dict(name="b4", start=597, end=618, score=[(597, 3, 3), (604.3, 3, 4)],
         crop=[(597, 780), (600, 800), (602, 640), (603, 430), (604.5, 430), (605.5, 780), (618, 780)],
         cap=(604.3, ["NAHHH 😭😭😭"], WHITE),
         gifs=[("c10", 605.0, 5.0, 340, 40, SQ_Y + 30, False),
               ("c11", 611.0, 6.5, 300, 40, SQ_Y + 30, False)]),
    dict(name="ft", start=656, end=660, score=[(656, 3, 4)],
         crop=[(656, 780), (660, 780)],
         cap=(656.2, ["FULL TIME 3-4", "I'M DELETING THE GAME 💀"], YELLOW),
         gifs=[("c12", 656.3, 3.7, 340, 40, SQ_Y + 30, False)]),
]

def lerp_expr(keys):
    """Piecewise-linear crop-x expression in segment-local t."""
    def cx(c):
        return max(0, min(1560 - CROP, c - CROP // 2))
    pts = [(t, cx(c)) for t, c in keys]
    expr = str(pts[-1][1])
    for (t0, x0), (t1, x1) in reversed(list(zip(pts, pts[1:]))):
        seg = f"{x0}+({x1}-{x0})*(t-{t0:.3f})/{max(t1 - t0, 0.001):.3f}"
        expr = f"if(lt(t,{t1:.3f}),{seg},{expr})"
    return f"if(lt(t,{pts[0][0]:.3f}),{pts[0][1]},{expr})"

# ---------------------------------------------------------------- static PNGs
render_text(["I WAS WINNING 3-1", "AT HALF TIME… 😭"], 76, WHITE, 8, f"{OUT}/png/hook.png")
render_text(["FOLLOW FOR MORE eFOOTBALL 🎮"], 46, WHITE, 6, f"{OUT}/png/follow.png")

def build(i, s):
    dur = s["end"] - s["start"]
    rel = lambda t: t - s["start"]
    # score bug pngs
    bugs = []
    for k, (t, h, a) in enumerate(s["score"]):
        p = f"{OUT}/png/{s['name']}_score{k}.png"
        score_bug(h, a, p)
        t1 = s["score"][k + 1][0] if k + 1 < len(s["score"]) else s["end"] + 1
        bugs.append((p, rel(t), rel(t1)))
    ct, clines, ccol = s["cap"]
    cap_png = f"{OUT}/png/{s['name']}_cap.png"
    render_text(clines, 88 if len(clines) > 1 else 100, ccol, 10, cap_png, pad=34 if len(clines) > 1 else 24, bg=len(clines) > 1)

    inputs = ["-ss", f"{s['start']:.3f}", "-t", f"{dur:.3f}", "-i", SRC,
              "-loop", "1", "-t", f"{dur:.3f}", "-i", f"{OUT}/png/hook.png",
              "-loop", "1", "-t", f"{dur:.3f}", "-i", f"{OUT}/png/follow.png",
              "-loop", "1", "-t", f"{dur:.3f}", "-i", cap_png]
    n = 4
    for p, _, _ in bugs:
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
    gif_idx = []
    for g in s["gifs"]:
        inputs += ["-ignore_loop", "0", "-i", f"{W}/gif/{g[0]}.gif"]
    cx = lerp_expr([(rel(t), c) for t, c in s["crop"]])
    T = rel(ct)
    f = []
    f.append("[0:v]fps=30,setpts=PTS-STARTPTS,split[a][b]")
    f.append("[a]crop=405:720:577:0,scale=270:480,boxblur=12:2,scale=1080:1920,eq=brightness=-0.22:saturation=1.2[bg]")
    f.append(f"[b]crop={CROP}:{CROP}:'{cx}':0,scale={SQ}:{SQ}:flags=lanczos,eq=saturation=1.12:contrast=1.04[sq]")
    f.append(f"[bg][sq]overlay=0:{SQ_Y},drawbox=x=0:y={SQ_Y - 6}:w=1080:h=6:color=0xFFDD00:t=fill,"
             f"drawbox=x=0:y={SQ_Y + SQ}:w=1080:h=6:color=0xFFDD00:t=fill[v0]")
    f.append(f"[v0][1:v]overlay=(W-w)/2:95[v1]")
    f.append(f"[v1][2:v]overlay=(W-w)/2:{SQ_Y + SQ + 30}[v2]")
    last = "v2"
    # score bugs (just above the square, under the hook)
    for k, (p, t0, t1) in enumerate(bugs):
        idx = 4 + k
        f.append(f"[{last}][{idx}:v]overlay=(W-w)/2:{SQ_Y - 112}:enable='between(t,{max(t0, 0):.3f},{t1:.3f})'[s{k}]")
        last = f"s{k}"
    # caption pop: scale from 55% -> 110% -> 100%
    pop = f"if(lt(t-{T:.3f},0.12),0.55+(t-{T:.3f})*4.6,if(lt(t-{T:.3f},0.24),1.10-(t-{T:.3f}-0.12)*0.83,1))"
    f.append(f"[3:v]scale=w='trunc(iw*{pop}/2)*2':h=-2:eval=frame[cap]")
    cy = s.get("cap_y", f"{SQ_Y + SQ - 330}-h/2+100")
    f.append(f"[{last}][cap]overlay=x=(W-w)/2:y={cy}:enable='gte(t,{T:.3f})'[c0]")
    last = "c0"
    base = 4 + len(bugs)
    for k, (gname, gt, gd, gw, gx, gy, chroma) in enumerate(s["gifs"]):
        g0 = rel(gt)
        key = "colorkey=0x18FE0D:0.35:0.12," if chroma else ""
        f.append(f"[{base + k}:v]{key}fps=30,scale={gw}:-2,format=rgba,trim=duration={gd:.3f},"
                 f"fade=t=in:st=0:d=0.15:alpha=1,setpts=PTS-STARTPTS+{g0:.3f}/TB[g{k}]")
        f.append(f"[{last}][g{k}]overlay={gx}:{gy}:eof_action=pass:enable='between(t,{g0:.3f},{g0 + gd:.3f})'[gg{k}]")
        last = f"gg{k}"
    f.append(f"[{last}]format=yuv420p[vout]")
    f.append(f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,volume=0.9,afade=t=in:d=0.12,"
             f"afade=t=out:st={dur - 0.15:.3f}:d=0.15[aout]")
    script = f"{OUT}/seg/{i:02d}.fg"
    open(script, "w").write(";\n".join(f))
    out = f"{OUT}/seg/{i:02d}_{s['name']}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", script,
           "-map", "[vout]", "-map", "[aout]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    return out

only = sys.argv[1:]
outs = []
for i, s in enumerate(SEGS):
    if only and s["name"] not in only:
        outs.append(f"{OUT}/seg/{i:02d}_{s['name']}.mp4")
        continue
    print("building", s["name"], flush=True)
    outs.append(build(i, s))
with open(f"{OUT}/list.txt", "w") as fh:
    for o in outs:
        fh.write(f"file '{o}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt",
                "-c", "copy", "-movflags", "+faststart", f"{OUT}/somtoo_highlights.mp4"], check=True)
print("done")
