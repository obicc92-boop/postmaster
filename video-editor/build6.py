#!/usr/bin/env python3
"""Match 2 (Barcelona 1-2 Somtoo FC) in the v5 style: steady 4:3 box, commentary above, memes."""
import os, sys

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
import build2 as b2
import build5 as b5
from captions import YELLOW, WHITE

SRC = f"{W}/m2/match.mp4"
OUT = f"{W}/out6"
b2.OUT = b5.OUT = OUT
b2.SRC = b5.SRC = SRC
for d in ("seg", "base", "png", "snd"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)
LT = b5.LT

# extra meme library (lib/) and sounds, so each video can use different reactions
b2.MEMES.update({
    "sweat": ("lib/L43.mp4", False), "rocklaugh": ("lib/L74.mp4", False), "arsenalfan": ("lib/L03.mp4", False),
    "rockcool": ("lib/L73.mp4", False), "sideeye": ("lib/L69.mp4", False), "fansdown": ("lib/L39.mp4", False),
    "mbappe": ("lib/L84.mp4", False), "speedhype": ("lib/L82.mp4", False), "hulk": ("lib/L63.mp4", False),
    "pikachu": ("lib/L31.mp4", False), "messi": ("lib/L09.mp4", False), "ronaldo": ("lib/L14.mp4", False),
    "nervous2": ("lib/L46.mp4", False), "shock2": ("lib/L47.mp4", False), "cryfan": ("lib/L38.mp4", False),
    "brazilcry": ("lib/L42.mp4", False), "rockbrow": ("lib/L70.mp4", False), "speedhyped": ("lib/L80.mp4", False),
})
b2.SFX.update({
    "sheesh": ("sheesh", 0.0, 2.0), "ohno": ("ohno", 0.0, 2.8), "wow": ("wow", 0.1, 2.6),
    "suspense": ("suspense", 0.0, 1.4), "gigachad": ("gigachad", 0.0, 2.4), "dramatic": ("dramatic", 0.0, 1.3),
    "cheer": ("cheer", 0.0, 2.4),
})
b5.MONKEY_H["sideeye"] = 1.0

P = [
    # hook: the late winner's build-up, cut just before it goes in
    dict(kind="game", start=557.0, end=562.3, caps=[(557.0, ["LAST MINUTE, 1-1… 😳"], WHITE)]),
    dict(kind="meme", m="sweat", dur=2.2, sfx="suspense", label=("Me", "me", 540, LT + 60),
         caps=[(0, ["WAIT FOR IT… 👀"], YELLOW)]),
    # lineups
    dict(kind="game", start=21.0, end=24.8, force=[(0, 3.8, 780, 0)],
         labels=[("Bro's", "bro", 540, LT, 21.0, 21.95), ("Me", "me", 540, LT, 21.95, 24.8)],
         caps=[(21.0, ["ME vs BRO 🎮"], WHITE)]),
    dict(kind="game", start=39.6, end=43.0, caps=[(39.6, ["LET'S GO ⚽"], WHITE)]),
    # Barcelona's early chance
    dict(kind="game", start=76.0, end=86.6, caps=[(83.4, ["BRO ALMOST SCORED 😰"], WHITE)],
         labels=[("Bro's", "bro", 540, LT, 84.9, 86.6)]),
    dict(kind="meme", m="rocklaugh", dur=2.6, sfx="ohno", label=("Me", "me", 540, LT),
         caps=[(0, ["NOT TODAY BRO 😂"], YELLOW)]),
    # half time
    dict(kind="game", start=278.4, end=280.8, caps=[(278.4, ["HALF TIME: 0-0 😐"], WHITE)]),
    # 0-1
    dict(kind="game", start=303.0, end=320.9, caps=[(314.0, ["GOAL!! ⚽🔥"], YELLOW)]),
    dict(kind="meme", m="arsenalfan", dur=2.0, sfx="sheesh", label=("Me", "me", 820, LT), caps=[(0, ["GOAL!! ⚽🔥"], YELLOW)]),
    # keeper save
    dict(kind="game", start=384.0, end=395.0, caps=[(392.6, ["WHAT A SAVE 🧤🔥"], YELLOW)]),
    dict(kind="meme", m="rockcool", dur=2.2, sfx="gigachad", label=("Me", "me", 540, LT),
         caps=[(0, ["MY KEEPER SAID NO 🧤"], YELLOW)]),
    # 1-1
    dict(kind="game", start=486.0, end=496.6, ovl=[("sideeye", 494.8, 1.8, 300)], sfx=[("dramatic", 494.7, 1.0)],
         labels=[("Me", "me", 180, None, 494.8, 496.6)], caps=[(494.4, ["1-1?! NAHHH 😭"], WHITE)]),
    dict(kind="meme", m="fansdown", dur=1.9, sfx="violin", label=("Me", "me", 540, LT),
         caps=[(0, ["1-1?! NAHHH 😭"], WHITE)]),
    # the winner, in full this time
    dict(kind="game", start=550.0, end=563.6, caps=[(562.6, ["WHAT A GOAL 🚀🔥"], YELLOW)]),
    dict(kind="meme", m="mbappe", dur=2.0, sfx="wow", label=("Me", "me", 540, LT),
         caps=[(0, ["WHAT A GOAL 🚀🔥"], YELLOW)]),
    dict(kind="game", start=569.0, end=572.6, caps=[(569.0, ["INZAGHI AGAIN 😎🔥"], YELLOW)]),
    dict(kind="meme", m="speedhype", dur=2.3, sfx="cheer", label=("Me", "me", 540, LT),
         caps=[(0, ["INZAGHI AGAIN 😎🔥"], YELLOW)]),
    # full time
    dict(kind="game", start=595.0, end=598.6, force=[(0, 3.6, 780, 0)],
         caps=[(595.0, ["FULL TIME 1-2", "BRO GOT COOKED 🔥"], YELLOW)]),
    dict(kind="meme", m="hulk", dur=3.1, sfx="damage", label=("Bro's", "bro", 540, LT),
         caps=[(0, ["FULL TIME 1-2", "BRO GOT COOKED 🔥"], YELLOW)]),
]

if __name__ == "__main__":
    only = {int(x) for x in sys.argv[1:]}
    outs = []
    for i, p in enumerate(P):
        if not only or i in only:
            print("piece", i, p["kind"], p.get("m") or p.get("start"), flush=True)
            b5.build(i, p)
        outs.append(f"{OUT}/seg/{i:02d}.mkv")
    with open(f"{OUT}/list.txt", "w") as fh:
        fh.writelines(f"file '{o}'\n" for o in outs)
    b2.run(["-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/joined.mkv"])
    print("joined", flush=True)
