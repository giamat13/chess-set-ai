"""Build the 3D "neural network" chess board in 4 printable quarters with dovetail joints.

Usage: python src/build_board.py [clearance_mm]      (default 0.15 mm per side)

Board: 8x8 squares of about 30.4 mm inside an 18.3 mm frame = 280 x 280 mm, 6 mm thick.
Each quarter is 4x4 squares (140 x 140 mm), so it fits the Bambu P1S bed (256 mm).

Joint: dovetail tabs in the lower 3.5 mm only. The top 2.5 mm meets in a straight line on the
square edge, so the top face shows a clean seam, and the piece above sits on the tabs.
  - TL and BR quarters carry the tabs and print face up (tabs lie on the bed).
  - TR and BL quarters carry the sockets and print face down (sockets open upward, no bridges).
Assembly: lay TL and BR, then drop TR and BL in from above. The tabs lock all 4 in the plane.

Colours: the top 0.6 mm is split into white and black parts (same coordinates) for an AMS print.
Output:
  stl/board/board_<q>.stl            whole quarter in print orientation (one colour, or for checks)
  stl/board/color/board_<q>_white.stl + board_<q>_black.stl   load both as one object (AMS)
  stl/board/test/                    small dovetail fit test: 1 tab + sockets at 0.10/0.15/0.20 mm
"""
import os
import sys

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

from build_set import write_stl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "stl", "board")

W_REAL, N = 280.0, 8          # board is 28 x 28 cm
SQ = W_REAL / (N + 2 * 24 / 40)  # square size, about 30.4 mm
K = SQ / 40.0                 # scale from the 2D proposal (40 units per square)
F = 24 * K                    # frame width, about 18.3 mm
W = N * SQ + 2 * F            # 280 mm
C = W / 2                     # seam line (on the edge between squares d/e and 4/5)
T, TAB_H, COLOR = 6.0, 3.5, 0.6
SEAM = 0.1                    # each quarter stops this far short of the seam line (top part)
LIFT = 0.2                    # vertical clearance above the tabs
CLEAR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
NECK, HEAD, DEPTH = 14.0, 22.0, 12.0
TAB_AT = (40.0, 100.0)        # tab centres, measured from the board centre along each seam
FONT = FontProperties(family="DejaVu Sans Mono", weight="bold")


def add(parts):
    parts = [p for p in parts if p is not None]
    if isinstance(parts[0], CrossSection):
        out = parts[0]
        for p in parts[1:]:
            out = out + p
        return out
    return Manifold.batch_boolean(parts, OpType.Add)


def rect(x0, y0, x1, y1):
    return CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))


def P(x, y):
    """2D proposal units (y down) to board mm (y up)."""
    return x * K, W - y * K


def centre(c, r):
    return P(24 + c * 40 + 20, 24 + r * 40 + 20)


def dark(c, r):
    return (c + r) % 2 == 1


def seg(a, b, w):
    return CrossSection.batch_hull([CrossSection.circle(w / 2, 20).translate(a), CrossSection.circle(w / 2, 20).translate(b)])


def text(s, size, x, y, rot=0.0):
    """Text centred on (x, y) in board mm; rot in degrees (90 = reads bottom to top)."""
    path = TextPath((0, 0), s, size=size, prop=FONT)
    polys = [p for p in path.to_polygons(closed_only=True) if len(p) >= 3]
    cs = CrossSection([np.asarray(p[:-1], dtype=float) for p in polys], FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    cs = cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))
    if rot:
        cs = cs.rotate(rot)
    return cs.translate((x, y))


def white_2d():
    """Everything white on the top face, from the '2_neural_network' proposal."""
    parts = []
    for r in range(N):
        for c in range(N):
            x, y = F + c * SQ, W - F - (r + 1) * SQ
            if not dark(c, r):
                parts.append(rect(x, y, x + SQ, y + SQ))
    for r in range(N):
        for c in range(N):
            if not dark(c, r):
                continue
            for dc, dr in ((1, 1), (-1, 1)):
                if 0 <= c + dc < N and 0 <= r + dr < N:
                    parts.append(seg(centre(c, r), centre(c + dc, r + dr), 1.4 * K))
            parts.append(CrossSection.circle((5 + (c * 3 + r * 5) % 4) * K, 64).translate(centre(c, r)))
    o = 1.0 * K  # play-area outline, 2 units wide
    parts.append(rect(F - o, F - o, W - F + o, W - F + o) - rect(F + o, F + o, W - F - o, W - F - o))
    cols = [("LOW",), ("MEDIUM",), ("HIGH",), ("XHIGH",), ("MAX",), ("MANUAL",), ("ACCEPT", "EDITS"), ("BYPASS", "PERMS")]
    yb = F / 2
    for i, lab in enumerate(cols):
        x = F + i * SQ + SQ / 2
        if len(lab) == 2:
            parts += [text(lab[0], 7 * K, x, yb + 3.36 * K), text(lab[1], 7 * K, x, yb - 3.36 * K)]
        else:
            parts.append(text(lab[0], 8 * K, x, yb))
    for r in range(N):  # rows from the top: AUTO COMPACT, then 87% .. 12% downwards
        y = W - F - r * SQ - SQ / 2
        if r == 0:
            parts += [text("AUTO", 7 * K, F / 2 - 3.36 * K, y, 90), text("COMPACT", 7 * K, F / 2 + 3.36 * K, y, 90)]
        else:
            parts.append(text(f"{int(12.5 * (N - r))}%", 8 * K, F / 2, y))
    return add(parts) ^ rect(0, 0, W, W)


def dovetail(x, y, ang):
    """Tab rooted on the seam at (x, y), pointing along ang (deg). Starts 1 mm behind the seam."""
    pts = [(-1.0, -NECK / 2), (DEPTH, -HEAD / 2), (DEPTH, HEAD / 2), (-1.0, NECK / 2)]
    cs = CrossSection([pts]).offset(-1.0, JoinType.Round).offset(1.0, JoinType.Round)  # round the corners
    return cs.rotate(ang).translate((x, y))


QUADS = {  # name: footprint (x0, y0, x1, y1)
    "TL": (0, C, C, W), "TR": (C, C, W, W), "BL": (0, 0, C, C), "BR": (C, 0, W, C),
}
TABS = {  # tab quarter: tabs (seam point, direction)
    "TL": [((C, C + d), 0) for d in TAB_AT] + [((C - d, C), -90) for d in TAB_AT],
    "BR": [((C, C - d), 180) for d in TAB_AT] + [((C + d, C), 90) for d in TAB_AT],
}


def footprint(q):
    x0, y0, x1, y1 = QUADS[q]
    x0 = x0 + SEAM if x0 == C else x0
    x1 = x1 - SEAM if x1 == C else x1
    y0 = y0 + SEAM if y0 == C else y0
    y1 = y1 - SEAM if y1 == C else y1
    return rect(x0, y0, x1, y1)


def slab(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


def quarter(q):
    fp = footprint(q)
    if q in TABS:
        tabs = add([dovetail(*p, a) for p, a in TABS[q]])
        return slab(fp + tabs, 0, TAB_H) + slab(fp, TAB_H, T)
    others = [dovetail(*p, a) for k in TABS for p, a in TABS[k]]
    sockets = add(others).offset(CLEAR, JoinType.Round) ^ rect(*QUADS[q])
    return slab(fp, 0, T) - slab(sockets, -1, TAB_H + LIFT)


def place(m, q):
    """Move to print orientation: socket quarters face down, all at the origin."""
    if q not in TABS:
        m = m.mirror((0, 0, 1))
    lo = m.bounding_box()[:3]
    return m.translate((-lo[0], -lo[1], -lo[2]))


def place_parts(parts, q):
    whole = add(parts)
    flip = q not in TABS
    if flip:
        parts = [p.mirror((0, 0, 1)) for p in parts]
        whole = whole.mirror((0, 0, 1))
    lo = whole.bounding_box()[:3]
    return [p.translate((-lo[0], -lo[1], -lo[2])) for p in parts]


def fit_test():
    """One tab coupon and three socket coupons (0.10 / 0.15 / 0.20 mm); notches = clearance."""
    d = os.path.join(OUT, "test")
    os.makedirs(d, exist_ok=True)
    tab = slab(rect(-30, -20, 0, 20) + dovetail(0.1, 0, 0), 0, TAB_H) + slab(rect(-30, -20, 0, 20), TAB_H, T)
    write_stl(tab.translate((30, 20, 0)), os.path.join(d, "test_tab.stl"))
    for i, cl in enumerate((0.10, 0.15, 0.20)):
        sock = dovetail(0, 0, 0).offset(cl, JoinType.Round)
        body = slab(rect(0.1, -20, 25, 20), 0, T) - slab(sock, -1, TAB_H + LIFT)
        for k in range(i + 1):  # 1, 2 or 3 notches on the back edge
            body = body - Manifold.cube((3, 2, T + 2)).translate((6 + k * 5, 19, -1))
        body = body.mirror((0, 0, 1))
        lo = body.bounding_box()[:3]
        write_stl(body.translate((-lo[0], -lo[1], -lo[2])), os.path.join(d, f"test_socket_{int(cl * 100):03d}.stl"))


def main():
    os.makedirs(os.path.join(OUT, "color"), exist_ok=True)
    print("@@step 2D artwork", flush=True)
    white = white_2d()
    black = rect(0, 0, W, W) - white
    for q in QUADS:
        print(f"@@step quarter {q}", flush=True)
        body = quarter(q)
        top = slab(black ^ rect(*QUADS[q]), T - COLOR, T + 1) ^ body
        whitep = body - top
        w, b = place_parts([whitep, top], q)
        write_stl(place(body, q), os.path.join(OUT, f"board_{q}.stl"))
        write_stl(w, os.path.join(OUT, "color", f"board_{q}_white.stl"))
        write_stl(b, os.path.join(OUT, "color", f"board_{q}_black.stl"))
        sz = place(body, q).bounding_box()
        print(f"board_{q}: {sz[3]:.1f} x {sz[4]:.1f} x {sz[5]:.1f} mm, {body.volume() / 1000:.0f} cm3", flush=True)
    print("@@step fit test", flush=True)
    fit_test()
    print(f"done (clearance {CLEAR} mm per side)", flush=True)


if __name__ == "__main__":
    main()
