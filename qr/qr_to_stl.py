#!/usr/bin/env python3
"""Convert the Sparrowhawk QR code into a 3D-printable STL.

Geometry: a solid base plate covering the QR + quiet-zone border, with the
DARK modules raised as boxes on top. Print the base in one colour and insert a
filament change at the top of the base layer so the raised modules come out in
a contrasting colour — that gives a reliably scannable code.

Run:
    /tmp/qrenv/bin/python qr/qr_to_stl.py
"""
import struct
import segno

URL = "https://keaneypj.github.io/sparrowhawk-garden/"
OUT = "qr/sparrowhawk-qr.stl"

# ---- print parameters (millimetres) ----
MODULE_MM = 2.0      # size of one QR cell -> overall size = cells * MODULE_MM
BASE_MM   = 1.6      # base plate thickness
RELIEF_MM = 0.8      # how far dark modules rise above the base
BORDER    = 4        # quiet-zone cells around the code (QR standard = 4)

qr = segno.make(URL, error="h")

# matrix_iter yields rows top->bottom, cols left->right, 1 = dark, 0 = light.
matrix = [list(row) for row in qr.matrix_iter(scale=1, border=BORDER)]
n_rows = len(matrix)
n_cols = len(matrix[0])

tris = []  # each: (v0, v1, v2)


def add_box(x0, y0, z0, x1, y1, z1):
    """Append an axis-aligned box as 12 triangles with outward-facing winding."""
    v000 = (x0, y0, z0); v100 = (x1, y0, z0); v110 = (x1, y1, z0); v010 = (x0, y1, z0)
    v001 = (x0, y0, z1); v101 = (x1, y0, z1); v111 = (x1, y1, z1); v011 = (x0, y1, z1)
    raw = [
        (v000, v100, v110), (v000, v110, v010),   # bottom
        (v001, v101, v111), (v001, v111, v011),   # top
        (v000, v100, v101), (v000, v101, v001),   # -Y
        (v010, v110, v111), (v010, v111, v011),   # +Y
        (v000, v010, v011), (v000, v011, v001),   # -X
        (v100, v110, v111), (v100, v111, v101),   # +X
    ]
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    for a, b, c in raw:
        nx, ny, nz = _normal(a, b, c)
        # face centroid relative to box centre — flip winding if normal points in
        fx = (a[0] + b[0] + c[0]) / 3 - cx
        fy = (a[1] + b[1] + c[1]) / 3 - cy
        fz = (a[2] + b[2] + c[2]) / 3 - cz
        if nx * fx + ny * fy + nz * fz < 0:
            b, c = c, b
        tris.append((a, b, c))


def _normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


# Base plate spans the whole footprint (code + quiet zone).
W = n_cols * MODULE_MM
H = n_rows * MODULE_MM
add_box(0, 0, 0, W, H, BASE_MM)

# Raised dark modules. Flip the row axis so the print reads the same as the
# on-screen QR (not mirrored) when viewed from the top (+Z).
for i, row in enumerate(matrix):
    y0 = (n_rows - 1 - i) * MODULE_MM
    for j, dark in enumerate(row):
        if dark:
            x0 = j * MODULE_MM
            # sink 0.2 mm into the base so the solids overlap (clean union,
            # no coincident coplanar faces) while keeping RELIEF_MM above it.
            add_box(x0, y0, BASE_MM - 0.2, x0 + MODULE_MM, y0 + MODULE_MM, BASE_MM + RELIEF_MM)

# ---- write binary STL ----
with open(OUT, "wb") as f:
    f.write(b"Sparrowhawk QR  " + b"\0" * 64)   # 80-byte header
    f.write(struct.pack("<I", len(tris)))
    for a, b, c in tris:
        nx, ny, nz = _normal(a, b, c)
        L = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        f.write(struct.pack("<3f", nx / L, ny / L, nz / L))
        for v in (a, b, c):
            f.write(struct.pack("<3f", *v))
        f.write(struct.pack("<H", 0))

print(f"wrote {OUT}")
print(f"encoded: {URL}  (QR version {qr.version}, error {qr.error})")
print(f"grid: {n_cols} x {n_rows} cells @ {MODULE_MM} mm")
print(f"size: {W:.1f} x {H:.1f} x {BASE_MM + RELIEF_MM:.1f} mm  |  {len(tris)} triangles")
