"""
Embeds the avi-ascii.svg content as a nested <svg> inside now-building.svg,
replacing the broken <image href="...portrait.jpg"> that GitHub blocks.
"""
import re

# ── read both files ───────────────────────────────────────────────────────────
with open("avi-ascii.svg", encoding="utf-8") as f:
    avi_raw = f.read()

with open("now-building.svg", encoding="utf-8") as f:
    nb_raw = f.read()

# ── extract inner content of avi-ascii.svg (strip outer <svg> tags) ───────────
inner = re.sub(r"^<svg[^>]*>", "", avi_raw.strip())
inner = re.sub(r"</svg>\s*$", "", inner)

# ── build the nested <svg> that positions the ASCII art in the portrait slot ──
# Target area in now-building.svg: x=830 y=28 w=340 h=334 rx=22
# avi-ascii.svg viewBox: 0 0 412 436
nested = (
    f'<svg x="830" y="28" width="340" height="334" '
    f'viewBox="0 0 412 436" '
    f'preserveAspectRatio="xMidYMid meet" overflow="hidden">\n'
    f'{inner}\n'
    f'</svg>'
)

# ── replace the broken <image> block inside the clip-path group ───────────────
# The block to replace starts with <image href="https://raw...portrait.jpg"
# and ends just before the closing </g>
old_image = re.search(
    r'<image\s+href="https://raw\.githubusercontent[^"]*portrait\.jpg"[^/]*/>', nb_raw
)
if old_image:
    nb_raw = nb_raw[:old_image.start()] + nested + nb_raw[old_image.end():]
    print("Replaced <image> with nested ASCII SVG.")
else:
    print("ERROR: could not find the <image> tag in now-building.svg")
    raise SystemExit(1)

with open("now-building.svg", "w", encoding="utf-8") as f:
    f.write(nb_raw)

size_kb = round(len(nb_raw.encode()) / 1024, 1)
print(f"now-building.svg written — {size_kb} KB")
