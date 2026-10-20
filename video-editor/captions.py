"""Anton caption renderer with colour emoji (from v1), no background box."""
from PIL import Image, ImageDraw, ImageFont
import os
W = os.path.dirname(os.path.abspath(__file__))
ANTON = f"{W}/fonts/Anton.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW = (255, 221, 0)
WHITE = (255, 255, 255)
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

