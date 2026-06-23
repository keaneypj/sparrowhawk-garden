#!/usr/bin/env python3
"""Generate the Sparrowhawk QR codes.

Run with segno installed:
    python3 -m venv /tmp/qrenv && /tmp/qrenv/bin/pip install segno
    /tmp/qrenv/bin/python qr/generate.py
"""
import segno

URL = "https://keaneypj.github.io/sparrowhawk-garden/"
OLIVE = "#2F3826"   # --olive-ink, the site's main text colour

# error='h' = 30% recovery, robust for a printed outdoor sign (and leaves
# room to drop the sparrowhawk mark in the centre later if we want).
qr = segno.make(URL, error="h")

# Scalable vector — best for print at any size.
qr.save("qr/sparrowhawk-qr.svg", dark=OLIVE, light="#ffffff", border=4, scale=10)

# High-res raster, olive on white.
qr.save("qr/sparrowhawk-qr.png", dark=OLIVE, light="#ffffff", border=4, scale=16)

# Pure black/white fallback — highest contrast, scans in any condition.
qr.save("qr/sparrowhawk-qr-black.png", dark="#000000", light="#ffffff", border=4, scale=16)

print("encoded:", URL)
print("version:", qr.version, "| error:", qr.error)
