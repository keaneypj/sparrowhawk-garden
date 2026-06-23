#!/usr/bin/env python3
"""Vectorize the painted Sparrowhawk mark (logo/source.jpg) into clean assets.

Outputs into logo/:
  sparrowhawk-mark.svg            olive (#2F3826), the primary mark
  sparrowhawk-mark-cream.svg      cream (#F4F3EB) for dark backgrounds
  sparrowhawk-mark.png            transparent, 1024px wide
  sparrowhawk-mark-512.png        transparent, 512px wide
  favicon-64.png                  square, padded — small-size legibility check

Run:  /tmp/qrenv/bin/python logo/build_logo.py
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OLIVE = "#2F3826"
CREAM = "#F4F3EB"
THR = 115
SRC = "logo/source.jpg"

g = np.asarray(Image.open(SRC).convert("L"), dtype=np.uint8)
mask = g < THR

lbl, n = ndimage.label(mask)
sizes = ndimage.sum(np.ones_like(lbl), lbl, index=np.arange(1, n + 1))
hawk = (lbl == (np.argmax(sizes) + 1))

ys, xs = np.where(hawk)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
pad = 24
y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
y1, x1 = y1 + pad + 1, x1 + pad + 1
hawk = hawk[y0:y1, x0:x1]
# light cleanup only — keep crisp wingtips and the central diamond
hawk = ndimage.binary_closing(hawk, iterations=1)
Hh, Ww = hawk.shape

filled = ndimage.binary_fill_holes(hawk)
hl, hn = ndimage.label(filled & ~hawk)
hsz = ndimage.sum(np.ones_like(hl), hl, index=np.arange(1, hn + 1)) if hn else []
keep = [i + 1 for i, s in enumerate(hsz) if s > hawk.sum() * 0.0008]

NBR = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]


def trace(bmask):
    H, W = bmask.shape
    p = np.argwhere(bmask)[0]
    start = (int(p[0]), int(p[1]))
    b, cur, out = (start[0], start[1] - 1), start, [start]
    for _ in range(int(bmask.sum()) * 8 + 1000):
        bi = NBR.index((b[0] - cur[0], b[1] - cur[1]))
        nxt = None
        for k in range(1, 9):
            idx = (bi + k) % 8
            ny, nx = cur[0] + NBR[idx][0], cur[1] + NBR[idx][1]
            if 0 <= ny < H and 0 <= nx < W and bmask[ny, nx]:
                b = (cur[0] + NBR[(idx - 1) % 8][0], cur[1] + NBR[(idx - 1) % 8][1])
                nxt = (ny, nx); break
        if nxt is None:
            break
        out.append(nxt); cur = nxt
        if len(out) >= 3 and out[-1] == out[1] and out[-2] == out[0]:
            out.pop(); break
    return [(x, y) for y, x in out]


def rdp(points, eps):
    n = len(points)
    if n < 3:
        return points
    keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    pts = np.asarray(points, float); stack = [(0, n - 1)]
    while stack:
        a, c = stack.pop()
        if c <= a + 1:
            continue
        seg = pts[c] - pts[a]; L = np.hypot(*seg)
        rel = pts[a + 1:c] - pts[a]
        d = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / L if L else np.hypot(*rel.T)
        i = int(np.argmax(d))
        if d[i] > eps:
            keep[a + 1 + i] = True
            stack.append((a, a + 1 + i)); stack.append((a + 1 + i, c))
    return [points[i] for i in range(n) if keep[i]]


EPS = 2.0
outer = rdp(trace(hawk), EPS)
holes = [rdp(trace(hl == h), EPS) for h in keep]
print(f"crop {Ww}x{Hh} | outer pts {len(outer)} | holes {[len(h) for h in holes]}")


def d_of(poly):
    return "M " + " L ".join(f"{x},{y}" for x, y in poly) + " Z"


D = d_of(outer) + " " + " ".join(d_of(h) for h in holes)


def write_svg(path, color):
    open(path, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Ww} {Hh}" '
        f'role="img" aria-label="Sparrowhawk">\n'
        f'<path fill="{color}" fill-rule="evenodd" d="{D}"/>\n</svg>\n')


write_svg("logo/sparrowhawk-mark.svg", OLIVE)
write_svg("logo/sparrowhawk-mark-cream.svg", CREAM)


def render(scale_w, color_rgb):
    s = scale_w / Ww
    w, h = scale_w, round(Hh * s)
    mimg = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(mimg)
    dr.polygon([(x * s, y * s) for x, y in outer], fill=255)
    for hp in holes:
        dr.polygon([(x * s, y * s) for x, y in hp], fill=0)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fg = Image.new("RGBA", (w, h), color_rgb + (255,))
    return Image.composite(fg, img, mimg)


OLIVE_RGB = (47, 56, 38)
render(1024, OLIVE_RGB).save("logo/sparrowhawk-mark.png")
render(512, OLIVE_RGB).save("logo/sparrowhawk-mark-512.png")

# square favicon-size check (54px mark inside 64 padded)
fav = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
mk = render(54, OLIVE_RGB)
fav.alpha_composite(mk, ((64 - mk.width) // 2, (64 - mk.height) // 2))
fav.save("logo/favicon-64.png")
print("wrote logo/*.svg and logo/*.png")
