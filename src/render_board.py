"""Render images/board_preview.png: top view of the 4 board quarters pulled apart, tabs shown in grey.

Usage: python src/render_board.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

import build_board as bb

GAP = 25.0  # how far each quarter is pulled away from the centre


def draw(ax, cs, colour, dx, dy, edge="none"):
    verts, codes = [], []
    for poly in cs.to_polygons():
        pts = [(x + dx, y + dy) for x, y in poly]
        verts += pts + [pts[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1) + [Path.CLOSEPOLY]
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=colour, edgecolor=edge, lw=0.6))


def main():
    white = bb.white_2d()
    fig, ax = plt.subplots(figsize=(10, 10), dpi=110)
    for q, (x0, y0, x1, y1) in bb.QUADS.items():
        dx = GAP if x0 >= bb.C else -GAP
        dy = GAP if y0 >= bb.C else -GAP
        fp = bb.footprint(q)
        if q in bb.TABS:
            draw(ax, bb.add([bb.dovetail(*p, a) for p, a in bb.TABS[q]]), "#9a9a9a", dx, dy, "#555")
        draw(ax, fp, "#111111", dx, dy, "#555")
        draw(ax, white ^ fp, "#f4f4f4", dx, dy)
    ax.set_xlim(-GAP - 10, bb.W + GAP + 10)
    ax.set_ylim(-GAP - 10, bb.W + GAP + 10)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.patch.set_facecolor("#7a8a99")
    out = os.path.join(bb.ROOT, "images", "board_preview.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    print("wrote", out)


if __name__ == "__main__":
    main()
