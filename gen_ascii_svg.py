from PIL import Image, ImageEnhance, ImageFilter
import random, html

# ── config ────────────────────────────────────────────────────────────────────
PORTRAIT  = "portrait.jpg"
OUT       = "avi-ascii.svg"
COLS      = 155          # many more columns = denser mosaic
FONT_SIZE = 4.0          # smaller font for tighter grid
CHAR_W    = FONT_SIZE * 0.600
CHAR_H    = FONT_SIZE * 1.18
PADDING   = 20
BG_COLOR  = "#060a12"
DOT_COLOR = "#1e4fc2"

random.seed(77)

# Dense character ramp: sparse (bright) → dense (dark)
CHARS = " .`-':_,^=+!r*/sLTv)J7(|Fi1tlu[neoZ5Yjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"

# ── load & prepare ────────────────────────────────────────────────────────────
img = Image.open(PORTRAIT).convert("RGB")
W, H = img.size

# Crop to face + shoulders, drop very bottom
img = img.crop((0, 0, W, int(H * 0.90)))

# Aggressive contrast + darker brightness to push background toward black
# and sharpen edges so boundary blending zone is minimal
img = ImageEnhance.Contrast(img).enhance(1.85)
img = ImageEnhance.Brightness(img).enhance(0.72)
img = img.filter(ImageFilter.SHARPEN)
img = img.filter(ImageFilter.SHARPEN)
img = ImageEnhance.Color(img).enhance(1.25)

ROWS = int(COLS * (img.height / img.width) * (CHAR_W / CHAR_H))
img_s = img.resize((COLS, ROWS), Image.LANCZOS)
gray  = img_s.convert("L")

SVG_W = int(COLS * CHAR_W + PADDING * 2)
SVG_H = int(ROWS * CHAR_H + PADDING * 2)
print(f"Grid: {ROWS}r x {COLS}c  ->  {SVG_W}x{SVG_H}px")

# ── decorations ───────────────────────────────────────────────────────────────
def rand_bin(n): return "".join(random.choice("01") for _ in range(n))

edge = SVG_W // 6
binary_groups = []
for zone_x in [range(2, edge - 8), range(SVG_W - edge + 8, SVG_W - 2)]:
    for _ in range(12):
        bx = random.choice(zone_x)
        by = random.randint(12, SVG_H - 12)
        lines = [rand_bin(random.randint(4, 6)) for _ in range(random.randint(2, 5))]
        binary_groups.append((bx, by, lines))

dots = [(random.randint(3, SVG_W-3),
         random.randint(3, SVG_H-3),
         random.choice([1.0, 1.3, 1.6, 2.0])) for _ in range(55)]

# ── SVG ───────────────────────────────────────────────────────────────────────
p = []
p.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">
<defs>
  <radialGradient id="rg" cx="50%" cy="44%" r="54%">
    <stop offset="0%"   stop-color="#0c1828"/>
    <stop offset="100%" stop-color="{BG_COLOR}"/>
  </radialGradient>
  <filter id="dg" x="-400%" y="-400%" width="900%" height="900%">
    <feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{SVG_W}" height="{SVG_H}" fill="url(#rg)"/>
''')

# Binary text blocks
for bx, by, lines in binary_groups:
    for i, line in enumerate(lines):
        gy = by + i * 9
        if 2 < gy < SVG_H - 2:
            s = random.randint(32, 72)
            c = f"#{s:02x}{s+16:02x}{s+52:02x}"
            p.append(f'<text x="{bx}" y="{gy}" font-family="ui-monospace,monospace" '
                     f'font-size="7" fill="{c}" opacity="0.50">{html.escape(line)}</text>\n')

# Circuit dots
for dx, dy, dr in dots:
    p.append(f'<circle cx="{dx}" cy="{dy}" r="{dr}" fill="{DOT_COLOR}" '
             f'filter="url(#dg)" opacity="0.68"/>\n')

# ── collect every rendered character in top→bottom, left→right order ─────────
all_chars = []
for row in range(ROWS):
    for col in range(COLS):
        lum = gray.getpixel((col, row))
        if lum < 10 or lum > 220:
            continue
        r, g, b = img_s.getpixel((col, row))
        idx = len(CHARS) - 1 - int((lum / 255) * (len(CHARS) - 1))
        ch  = CHARS[max(0, min(idx, len(CHARS) - 1))]
        if ch == " ":
            continue
        scale = 0.88
        rf = min(255, int(r * scale))
        gf = min(255, int(g * scale * 0.95))
        bf = min(255, int(b * scale * 0.86))
        cx = PADDING + col * CHAR_W
        cy = PADDING + row * CHAR_H + FONT_SIZE
        all_chars.append((cx, cy, ch, f"#{rf:02x}{gf:02x}{bf:02x}"))

n = len(all_chars)
print(f"Total chars: {n}")

# ── loop + flicker timing ─────────────────────────────────────────────────────
CYCLE      = 5.0   # full loop cycle in seconds
TYPE_END   = 3.0   # chars all visible by this time
FLICK_START= 4.05  # flicker begins
RESET_START= 4.75  # all chars vanish → reset for next loop

# Inject shared CSS class (font props only — no animation here)
css = (
    "<style>.c{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;"
    f"font-size:{FONT_SIZE}px}}</style>\n"
)
p_str = "".join(p)
p_str = p_str.replace("</defs>", css + "</defs>", 1)
p = [p_str]

# ── wrapper group: flicker animation applied to all chars at once ─────────────
fs = FLICK_START / CYCLE
re = RESET_START / CYCLE
p.append(
    f'<g>\n'
    f'<animate attributeName="opacity" calcMode="discrete"'
    f' values="1;1;0.04;1;0.06;1;0.03;1;0.05;1;0;0;1"'
    f' keyTimes="0;{fs:.3f};{fs+0.02:.3f};{fs+0.04:.3f};{fs+0.07:.3f};'
    f'{fs+0.09:.3f};{fs+0.12:.3f};{fs+0.14:.3f};{fs+0.17:.3f};'
    f'{re:.3f};{re+0.01:.3f};0.998;1"'
    f' dur="{CYCLE}s" repeatCount="indefinite"/>\n'
)

# ── per-char SMIL: each letter pops in at its own time, loops every CYCLE s ──
for i, (cx, cy, ch, color) in enumerate(all_chars):
    T      = i * TYPE_END / n          # appear time within cycle
    t_frac = max(0.0001, T / CYCLE)    # keyTime fraction (never exactly 0)
    r_frac = RESET_START / CYCLE       # when all chars vanish for reset

    p.append(
        f'<text class="c" x="{cx:.1f}" y="{cy:.1f}" fill="{color}" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;1;0"'
        f' keyTimes="0;{t_frac:.4f};{r_frac:.3f};1"'
        f' dur="{CYCLE}s" repeatCount="indefinite"/>'
        f'{html.escape(ch)}</text>\n'
    )

p.append('</g>\n')
p.append('</svg>\n')

with open(OUT, "w", encoding="utf-8") as f:
    f.write("".join(p))
print(f"Written -> {OUT}")
