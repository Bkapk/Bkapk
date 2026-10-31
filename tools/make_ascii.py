"""Turn a white-background headshot into ASCII art for the profile card.

Usage: python make_ascii.py photo.jpg COLS [left top right bottom] [--dark]
--dark maps bright areas to dense glyphs, for light text on a dark card.
Paste the output into ART in update_profile.py.
"""
import sys
from PIL import Image, ImageFilter, ImageOps

CHAR_ASPECT = 4.8 / 9   # monospace glyph width / line height of the art in the SVG (8px font, 9px lines)
RAMP = " .:-=+*#%@"     # light -> dark

dark = "--dark" in sys.argv
args = [a for a in sys.argv[1:] if a != "--dark"]
src, cols = args[0], int(args[1])
img = Image.open(src).convert("RGB")
if len(args) == 6:
    img = img.crop(tuple(int(v) for v in args[2:6]))
rows = round(img.height / img.width * cols * CHAR_ASPECT)
small = img.resize((cols, rows), Image.LANCZOS)
# sharpen features, then push skin toward white so eyes, brows and beard carry the shape
LO, HI, GAMMA = 45, 205, 0.55
gray = (img.filter(ImageFilter.UnsharpMask(radius=6, percent=180, threshold=2))
        .convert("L").resize((cols, rows), Image.LANCZOS)
        .point(lambda v: round(255 * min(1, max(0, (v - LO) / (HI - LO))) ** GAMMA)))

# background = near-white cells connected to the image border (keeps the white T-shirt)
white = {(x, y) for y in range(rows) for x in range(cols) if min(small.getpixel((x, y))) > 222}
bg, stack = set(), [(x, y) for (x, y) in white if x in (0, cols - 1) or y == 0]
while stack:
    p = stack.pop()
    if p in bg or p not in white:
        continue
    bg.add(p)
    x, y = p
    stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

for y in range(rows):
    line = ""
    for x in range(cols):
        if (x, y) in bg:
            line += " "
        else:
            v = gray.getpixel((x, y))
            ink = v if dark else 255 - v
            line += RAMP[min(len(RAMP) - 1, int(ink / 256 * len(RAMP)) + 1)]
    print(line.rstrip())
