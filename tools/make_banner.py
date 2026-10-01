"""Renders assets/banner.gif: name, role, languages and a looping block-puzzle board.

    python tools/make_banner.py

The board starts and ends in the same state: two lines are cleared per loop
(a single row, then a row and a column at once), using only cells placed
during the loop, so the GIF repeats seamlessly. Needs Pillow and Windows fonts.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "banner.gif")

W, H = 1760, 400
BG = (14, 18, 24)
EMPTY = (28, 35, 45)
FLASH = (240, 246, 252)
COLORS = [(245, 165, 36), (52, 211, 153), (96, 165, 250), (192, 132, 252), (251, 113, 133)]

NAME = "Mario Landáburu Clares"
ROLE = "Software developer"
LANGS = ["C++", "TypeScript", "Swift", "Python", "GDScript"]

CELL, GAP = 30, 7
STEP = CELL + GAP
BX = W - 96 - (8 * CELL + 7 * GAP)
BY = (H - (8 * CELL + 7 * GAP)) // 2

# Start state: rows 4 and 7 and column 2 are empty, so no line is ever complete
# except the ones the loop builds. Digits are color indexes.
START = [
    "13.402.1",
    "0..14.32",
    "24.0.11.",
    ".3.2403.",
    "........",
    "41.3.204",
    "2..01.13",
    "........",
]

# (cells as (row, col), color). Placed in order; full lines clear after each placement.
MOVES = [
    ([(7, 0), (7, 1), (7, 2), (7, 3)], 2),
    ([(7, 4), (7, 5), (7, 6), (7, 7)], 0),          # row 7 clears
    ([(4, 4), (4, 5), (4, 6), (4, 7)], 3),
    ([(0, 2), (1, 2), (2, 2)], 1),
    ([(4, 0), (4, 1)], 4),
    ([(5, 2), (6, 2), (7, 2)], 2),
    ([(3, 2), (4, 2), (4, 3)], 0),                  # row 4 and column 2 clear together
]

FPS_MS = 50          # 20 frames per second
DROP = 5             # frames for a piece to drop in
SETTLE = 9           # frames of rest after a placement
FLASH_F = 4
SHRINK_F = 5


def font(name, size):
    return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", name), size)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    x = 96
    d.text((x, 104), NAME, font=font("segoeuib.ttf", 76), fill=(240, 246, 252))
    d.text((x + 3, 212), ROLE, font=font("segoeui.ttf", 34), fill=(154, 166, 180))
    cx = x + 3
    mono = font("consola.ttf", 24)
    for label in LANGS:
        w = d.textlength(label, font=mono)
        d.rounded_rectangle((cx, 280, cx + w + 28, 320), 8, fill=(22, 29, 39), outline=(42, 52, 65))
        d.text((cx + 14, 286), label, font=mono, fill=(195, 207, 219))
        cx += w + 28 + 12
    return img


def cell_box(r, c, dy=0, scale=1.0):
    x, y = BX + c * STEP, BY + r * STEP + dy
    inset = CELL * (1 - scale) / 2
    return (x + inset, y + inset, x + CELL - inset, y + CELL - inset)


def draw_board(img, grid, extra=None, flash=(), shrink=(), shrink_scale=1.0):
    d = ImageDraw.Draw(img)
    for r in range(8):
        for c in range(8):
            d.rounded_rectangle(cell_box(r, c), 5, fill=EMPTY)
    for r in range(8):
        for c in range(8):
            v = grid[r][c]
            if v is None:
                continue
            if (r, c) in shrink:
                if shrink_scale > 0.05:
                    d.rounded_rectangle(cell_box(r, c, scale=shrink_scale), 4, fill=FLASH)
                continue
            d.rounded_rectangle(cell_box(r, c), 5, fill=FLASH if (r, c) in flash else COLORS[v])
    if extra:
        cells, color, dy = extra
        for r, c in cells:
            d.rounded_rectangle(cell_box(r, c, dy=dy), 5, fill=COLORS[color])


def full_lines(grid):
    cells = set()
    for r in range(8):
        if all(grid[r][c] is not None for c in range(8)):
            cells |= {(r, c) for c in range(8)}
    for c in range(8):
        if all(grid[r][c] is not None for r in range(8)):
            cells |= {(r, c) for r in range(8)}
    return cells


def main():
    grid = [[None if ch == "." else int(ch) for ch in row] for row in START]
    start = [row[:] for row in grid]
    bg = base()
    frames = []

    def snap(**kw):
        f = bg.copy()
        draw_board(f, grid, **kw)
        frames.append(f)

    for _ in range(SETTLE):
        snap()
    for cells, color in MOVES:
        assert all(grid[r][c] is None for r, c in cells), cells
        for i in range(DROP):
            t = (i + 1) / DROP
            snap(extra=(cells, color, -46 * (1 - t) ** 2))
        for r, c in cells:
            grid[r][c] = color
        cleared = full_lines(grid)
        if cleared:
            snap()
            for _ in range(FLASH_F):
                snap(flash=cleared)
            for i in range(SHRINK_F):
                snap(shrink=cleared, shrink_scale=1 - (i + 1) / SHRINK_F)
            for r, c in cleared:
                grid[r][c] = None
        for _ in range(SETTLE):
            snap()
    assert grid == start, "the loop must end where it started"

    pal = Image.new("RGB", (W, H * 2))
    pal.paste(frames[0], (0, 0))
    pal.paste(frames[len(frames) // 2], (0, H))
    ImageDraw.Draw(pal).rectangle((0, 0, 40, 40), fill=FLASH)
    for i, col in enumerate(COLORS):
        ImageDraw.Draw(pal).rectangle((50 + i * 20, 0, 60 + i * 20, 10), fill=col)
    pal = pal.quantize(colors=96, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT, save_all=True, append_images=q[1:], duration=FPS_MS, loop=0, optimize=True, disposal=1)
    print(f"{OUT}: {len(frames)} frames, {os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    main()
