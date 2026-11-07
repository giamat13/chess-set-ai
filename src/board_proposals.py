"""Write 2D SVG proposals for an AI-themed chess board into boards/proposals/ (pure black and white).

Usage: python src/board_proposals.py
Each board is 8x8 squares of 40 units inside a 20-unit frame (360 x 360 total).
Only #000 and #fff are used (no greys, no opacity), so a proposal reads the same in a one-colour print.
"""
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "boards", "proposals")
S, F, N = 40, 24, 8
W = N * S + 2 * F
K, WH = "#000", "#fff"


def sq(c, r):  # top-left corner of the square in column c, row r (row 0 = top)
    return F + c * S, F + r * S


def centre(c, r):
    x, y = sq(c, r)
    return x + S / 2, y + S / 2


def dark(c, r):
    return (c + r) % 2 == 1


def svg(body, bg=K):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="720" height="720">\n'
            f'<rect width="{W}" height="{W}" fill="{bg}"/>\n{body}</svg>\n')


def squares(dark_fill=K, light_fill=WH):
    return [f'<rect x="{sq(c, r)[0]}" y="{sq(c, r)[1]}" width="{S}" height="{S}" '
            f'fill="{dark_fill if dark(c, r) else light_fill}"/>' for r in range(N) for c in range(N)]


def labels(colour=WH, off=0):
    out = []
    for i in range(N):
        x, _ = centre(i, 0)
        _, y = centre(0, i)
        out.append(f'<text x="{x}" y="{W - 6 - off}" fill="{colour}" font-size="9" font-family="monospace" text-anchor="middle">{"abcdefgh"[i]}</text>')
        out.append(f'<text x="{7 + 2 * off}" y="{y + 3}" fill="{colour}" font-size="9" font-family="monospace" text-anchor="middle">{N - i}</text>')
    return "\n".join(out)


def outline(width=1.5):
    return f'<rect x="{F}" y="{F}" width="{N * S}" height="{N * S}" fill="none" stroke="{WH}" stroke-width="{width}"/>'


def circuit():
    random.seed(1)
    b = squares()
    for r in range(N):
        for c in range(N):
            if dark(c, r):  # a trace with 45-degree bends and solder pads
                x, y = sq(c, r)
                cx, cy = centre(c, r)
                d = random.choice([(-1, 1), (1, 1), (-1, -1), (1, -1)])
                pts = [(x + 6, cy), (cx - 6 * d[0], cy), (cx + 4 * d[0], cy + 10 * d[1]), (x + S - 6, cy + 10 * d[1])]
                b.append('<polyline points="' + " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts) +
                         f'" fill="none" stroke="{WH}" stroke-width="1.6" stroke-linejoin="round"/>')
                for p in (pts[0], pts[-1]):
                    b.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.4" fill="{WH}"/>')
    for i in range(N * 2):  # chip pins along the frame
        p = F + 4 + i * (N * S - 8) / (N * 2 - 1)
        for (x, y, w, h) in ((p - 2, 1, 4, 7), (p - 2, W - 8, 4, 7), (1, p - 2, 7, 4), (W - 8, p - 2, 7, 4)):
            b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" fill="{WH}"/>')
    for x, y in ((9, 9), (W - 9, 9), (9, W - 9), (W - 9, W - 9)):
        b.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{K}" stroke="{WH}"/><path d="M{x - 2.5} {y} H{x + 2.5}" stroke="{WH}"/>')
    b.append(labels(WH, 4))
    return svg("\n".join(b))


def neural():
    b = squares()
    for r in range(N):  # dark squares touch diagonally: link them into a network
        for c in range(N):
            if not dark(c, r):
                continue
            for dc, dr in ((1, 1), (-1, 1)):
                if 0 <= c + dc < N and 0 <= r + dr < N:
                    (x1, y1), (x2, y2) = centre(c, r), centre(c + dc, r + dr)
                    b.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{WH}" stroke-width="1.4"/>')
    for r in range(N):
        for c in range(N):
            if dark(c, r):
                x, y = centre(c, r)
                b.append(f'<circle cx="{x}" cy="{y}" r="{5 + (c * 3 + r * 5) % 4}" fill="{WH}"/>')
    b.append(outline(2))
    cols = [("LOW", ""), ("MEDIUM", ""), ("HIGH", ""), ("XHIGH", ""), ("MAX", ""),
            ("MANUAL", ""), ("ACCEPT", "EDITS"), ("BYPASS", "PERMS")]  # effort levels, then permission modes
    t = 'fill="#fff" font-family="monospace" text-anchor="middle"'
    for i, (a, c2) in enumerate(cols):
        x = centre(i, 0)[0]
        y = W - F / 2
        if c2:
            b.append(f'<text x="{x}" y="{y - 1.5}" font-size="7" {t}>{a}</text><text x="{x}" y="{y + 6}" font-size="7" {t}>{c2}</text>')
        else:
            b.append(f'<text x="{x}" y="{y + 2.5}" font-size="8" {t}>{a}</text>')
    for r in range(N):  # context fill: 12% at the bottom up to 87%, then auto-compact at the top
        y = centre(0, r)[1]
        if r == 0:
            b.append(f'<text transform="translate({F / 2 - 2.5} {y}) rotate(-90)" font-size="7" {t}>AUTO</text>'
                     f'<text transform="translate({F / 2 + 5} {y}) rotate(-90)" font-size="7" {t}>COMPACT</text>')
        else:
            b.append(f'<text x="{F / 2}" y="{y + 3}" font-size="8" {t}>{int(12.5 * (N - r))}%</text>')
    return svg("\n".join(b))


def rack():
    random.seed(2)
    b = squares()
    for r in range(N):
        for c in range(N):
            if dark(c, r):
                x, y = sq(c, r)
                b.append(f'<rect x="{x + 4}" y="{y + 12}" width="{S - 8}" height="16" rx="2" fill="{K}" stroke="{WH}" stroke-width="1.4"/>')
                for k in range(4):
                    b.append(f'<line x1="{x + 8 + k * 4}" y1="{y + 16}" x2="{x + 8 + k * 4}" y2="{y + 24}" stroke="{WH}" stroke-width="1.5"/>')
                lit = random.choice([True, True, False, True])  # LED on = filled, off = ring
                b.append(f'<circle cx="{x + S - 9}" cy="{y + 20}" r="2.4" fill="{WH if lit else K}" stroke="{WH}"/>')
    for i in range(N * 2 + 1):  # rack-rail holes
        p = F + i * N * S / (N * 2)
        for x in (6, W - 12):
            b.append(f'<rect x="{x}" y="{p - 3:.1f}" width="6" height="6" rx="1.5" fill="{WH}"/>')
    b.append(labels(WH, 4))
    return svg("\n".join(b))


def heatmap():
    b = squares()
    for r in range(N):
        for c in range(N):
            if not dark(c, r):
                continue
            v = (math.sin(c * 1.3 + r * 0.7) + math.cos(r * 1.1 - c * 0.4) + 2) / 4  # 0..1 activation
            x, y = sq(c, r)
            for i in range(4):  # halftone: stronger activation = bigger white dots
                for j in range(4):
                    b.append(f'<circle cx="{x + 5 + i * 10}" cy="{y + 5 + j * 10}" r="{0.6 + 4.2 * v:.2f}" fill="{WH}"/>')
    b.append(outline())
    for i in range(6):  # scale on the frame: small dot = low, big dot = high
        b.append(f'<circle cx="{W / 2 - 25 + i * 10}" cy="10" r="{0.8 + i * 0.7:.1f}" fill="{WH}"/>')
    b.append(labels(WH, 4))
    return svg("\n".join(b))


def attention():
    b = squares()
    sx, sy = centre(3, 4)  # the "query" square, with attention arcs to others
    targets = [(0, 1, .9), (6, 2, .7), (1, 6, .5), (7, 5, .8), (5, 7, .4), (2, 3, .6), (4, 0, .5)]
    for c, r, w in targets:
        tx, ty = centre(c, r)
        mx, my = (sx + tx) / 2, min(sy, ty) - 35 * w - 10
        d = f"M{sx} {sy} Q{mx} {my} {tx} {ty}"
        wd = 1 + 3 * w
        # white halo under a black line, so the arc shows on both light and dark squares
        b.append(f'<path d="{d}" fill="none" stroke="{WH}" stroke-width="{wd + 3:.1f}" stroke-linecap="round"/>')
        b.append(f'<path d="{d}" fill="none" stroke="{K}" stroke-width="{wd:.1f}" stroke-linecap="round"/>')
    for c, r, w in targets:
        tx, ty = centre(c, r)
        b.append(f'<circle cx="{tx}" cy="{ty}" r="{3 + 4 * w:.1f}" fill="{K}" stroke="{WH}" stroke-width="2"/>')
    b.append(f'<circle cx="{sx}" cy="{sy}" r="9" fill="{WH}" stroke="{K}" stroke-width="3"/><circle cx="{sx}" cy="{sy}" r="3" fill="{K}"/>')
    b.append(outline())
    b.append(labels(WH, 4))
    return svg("\n".join(b))


BOARDS = {
    "1_circuit_board": circuit,
    "2_neural_network": neural,
    "3_server_rack": rack,
    "4_activation_heatmap": heatmap,
    "5_attention": attention,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BOARDS.items():
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(fn())
        print("wrote", name)
