#!/usr/bin/env python3
"""Generate portrait assets (v8 — pixel-native hair).

Face and features use SVG-to-pixel pipeline (4x render, BOX downscale).
Hair uses direct pixel placement via PIL polygons for precise control.
Quantized to Endesga-32 palette for clean pixel art output.
"""

from PIL import Image, ImageDraw
import cairosvg
import io
import math
import os
import numpy as np

SIZE = 96
RENDER_SCALE = 4
RENDER_SIZE = SIZE * RENDER_SCALE
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "portrait")

# ── Palette (Endesga-32 subset) ──────────────────────────────

P = {
    "sk_hi": (234, 212, 170),
    "sk_ba": (232, 183, 150),
    "sk_sh": (194, 133, 105),
    "sk_ol": (115, 62, 57),

    "hr_hh": (254, 174, 52),
    "hr_hi": (194, 133, 105),
    "hr_ba": (115, 62, 57),
    "hr_sh": (62, 39, 49),

    "ey_wh": (255, 255, 255),
    "ey_ir": (0, 153, 219),
    "ey_id": (18, 78, 137),
    "ey_pu": (24, 20, 37),
    "ey_li": (38, 43, 68),
    "ey_lo": (90, 105, 136),

    "li_ba": (215, 118, 67),
    "li_sh": (184, 111, 80),

    "blush": (246, 117, 122),

    "heart": (228, 59, 68),
    "hrt_h": (246, 117, 122),
    "sweat": (192, 203, 220),
    "swt_h": (255, 255, 255),

    "outln": (62, 39, 49),
}

QUANT_COLORS = list(P.values()) + [(30, 30, 40)]


def h(key):
    c = P[key]
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


# ── SVG rendering pipeline ──────────────────────────────────

def svg_to_layer(svg_str, quantize=False):
    png_data = cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        output_width=RENDER_SIZE,
        output_height=RENDER_SIZE,
    )
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")
    img = img.resize((SIZE, SIZE), Image.BOX)

    if quantize:
        # Split alpha, quantize RGB, recombine
        r, g, b, a = img.split()
        rgb = Image.merge("RGB", (r, g, b))
        pal_img = Image.new("P", (1, 1))
        pal_data = []
        for c in QUANT_COLORS:
            pal_data.extend(c[:3])
        pal_data.extend([0] * (768 - len(pal_data)))
        pal_img.putpalette(pal_data)
        qrgb = rgb.quantize(palette=pal_img, dither=0).convert("RGB")
        qr, qg, qb = qrgb.split()
        img = Image.merge("RGBA", (qr, qg, qb, a))

    return img


def wrap(inner):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" '
        'shape-rendering="geometricPrecision">'
        f'{inner}</svg>'
    )


def save(img, name):
    os.makedirs(ASSET_DIR, exist_ok=True)
    img.save(os.path.join(ASSET_DIR, name))
    print(f"  {name}")


# ── Body base ────────────────────────────────────────────────

def generate_body_base():
    svg = wrap(f"""
    <defs>
        <linearGradient id="sg" x1="0" y1="0" x2="1" y2="0.6">
            <stop offset="0%" stop-color="{h('sk_hi')}"/>
            <stop offset="45%" stop-color="{h('sk_ba')}"/>
            <stop offset="90%" stop-color="{h('sk_sh')}"/>
        </linearGradient>
        <linearGradient id="ng" x1="0.2" y1="0" x2="0.9" y2="0.5">
            <stop offset="0%" stop-color="{h('sk_ba')}"/>
            <stop offset="100%" stop-color="{h('sk_sh')}"/>
        </linearGradient>
    </defs>

    <!-- Neck (shorter) -->
    <path d="M 40 65 Q 40 72, 37 82 L 59 82 Q 56 72, 56 65 Z"
          fill="url(#ng)" stroke="{h('sk_ol')}" stroke-width="0.8"/>

    <!-- Shoulders hint -->
    <path d="M 37 82 Q 28 84, 20 88 L 76 88 Q 68 84, 59 82 Z"
          fill="{h('sk_sh')}" stroke="{h('sk_ol')}" stroke-width="0.6"/>

    <!-- Ears -->
    <ellipse cx="24" cy="42" rx="4" ry="6"
             fill="{h('sk_ba')}" stroke="{h('sk_ol')}" stroke-width="0.6"/>
    <ellipse cx="24" cy="42" rx="2" ry="3" fill="{h('sk_sh')}"/>
    <ellipse cx="72" cy="42" rx="4" ry="6"
             fill="{h('sk_sh')}" stroke="{h('sk_ol')}" stroke-width="0.6"/>
    <ellipse cx="72" cy="42" rx="2" ry="3" fill="{h('sk_ol')}" opacity="0.4"/>

    <!-- Head — anime face with jawline -->
    <path d="
        M 48 14
        C 30 14, 23 24, 23 36
        C 23 44, 25 50, 29 56
        Q 34 64, 40 67
        Q 44 69, 48 69
        Q 52 69, 56 67
        Q 62 64, 67 56
        C 71 50, 73 44, 73 36
        C 73 24, 66 14, 48 14 Z"
        fill="url(#sg)" stroke="{h('sk_ol')}" stroke-width="0.9"/>

    <!-- Nose — visible small shadow -->
    <path d="M 47 50 L 46 53 L 48 54 L 50 53 L 49 50"
          fill="{h('sk_sh')}" stroke="{h('sk_ol')}" stroke-width="0.4" opacity="0.7"/>
    <circle cx="48" cy="53.5" r="0.6" fill="{h('sk_ol')}" opacity="0.5"/>
    """)
    save(svg_to_layer(svg, quantize=True), "body_base.png")


# ── Eyes (SVG) ───────────────────────────────────────────────

def _eye_svg(cx, cy, flip=False):
    """Generate SVG for one anime eye. If flip, mirror for left eye."""
    sx = -1 if flip else 1
    # Highlight offset toward upper-right (same side both eyes for light)
    hx = cx + 2.5
    hy = cy - 2

    return f"""
    <g>
        <!-- Eye white -->
        <ellipse cx="{cx}" cy="{cy}" rx="7" ry="5"
                 fill="{h('ey_wh')}" stroke="{h('ey_lo')}" stroke-width="0.4"/>

        <!-- Iris — large, with gradient for depth -->
        <defs>
            <radialGradient id="iris_{cx}" cx="0.5" cy="0.35" r="0.5">
                <stop offset="0%" stop-color="{h('ey_ir')}"/>
                <stop offset="70%" stop-color="{h('ey_id')}"/>
                <stop offset="100%" stop-color="{h('ey_pu')}"/>
            </radialGradient>
        </defs>
        <circle cx="{cx}" cy="{cy + 0.5}" r="4.5"
                fill="url(#iris_{cx})" stroke="{h('ey_id')}" stroke-width="0.3"/>

        <!-- Pupil -->
        <ellipse cx="{cx}" cy="{cy + 1}" rx="2" ry="2.2"
                 fill="{h('ey_pu')}"/>

        <!-- Upper lid — thick, dark: THE anime signature -->
        <path d="M {cx - 7.5} {cy - 1} Q {cx} {cy - 7}, {cx + 7.5} {cy - 1}"
              fill="none" stroke="{h('ey_li')}" stroke-width="2.8"
              stroke-linecap="round"/>

        <!-- Primary highlight (upper) -->
        <ellipse cx="{hx}" cy="{hy}" rx="2" ry="1.5"
                 fill="white" opacity="0.9"/>

        <!-- Secondary highlight (lower, smaller) -->
        <circle cx="{cx - 2}" cy="{cy + 2.5}" r="1"
                fill="white" opacity="0.5"/>

        <!-- Lower lash line -->
        <path d="M {cx - 6} {cy + 4} Q {cx} {cy + 6}, {cx + 6} {cy + 4}"
              fill="none" stroke="{h('ey_lo')}" stroke-width="0.7"
              stroke-linecap="round"/>
    </g>
    """


def generate_eyes_open():
    svg = wrap(
        _eye_svg(36, 40) +
        _eye_svg(60, 40)
    )
    save(svg_to_layer(svg, quantize=True), "eyes_open.png")


def generate_eyes_half():
    def half_eye(cx, cy):
        hx = cx + 2.5
        return f"""
        <g>
            <clipPath id="half_{cx}">
                <rect x="{cx - 8}" y="{cy - 1}" width="16" height="8"/>
            </clipPath>
            <!-- Visible lower portion of eye -->
            <g clip-path="url(#half_{cx})">
                <ellipse cx="{cx}" cy="{cy}" rx="7" ry="5"
                         fill="{h('ey_wh')}" stroke="{h('ey_lo')}" stroke-width="0.4"/>
                <circle cx="{cx}" cy="{cy + 0.5}" r="4.5"
                        fill="{h('ey_id')}" stroke="{h('ey_id')}" stroke-width="0.3"/>
                <ellipse cx="{cx}" cy="{cy + 1}" rx="2" ry="2.2"
                         fill="{h('ey_pu')}"/>
            </g>
            <!-- Drooping upper lid -->
            <path d="M {cx - 7.5} {cy} Q {cx} {cy - 3.5}, {cx + 7.5} {cy}"
                  fill="none" stroke="{h('ey_li')}" stroke-width="2.8"
                  stroke-linecap="round"/>
            <!-- Lower lash -->
            <path d="M {cx - 6} {cy + 4} Q {cx} {cy + 6}, {cx + 6} {cy + 4}"
                  fill="none" stroke="{h('ey_lo')}" stroke-width="0.7"
                  stroke-linecap="round"/>
        </g>
        """
    svg = wrap(half_eye(36, 40) + half_eye(60, 40))
    save(svg_to_layer(svg, quantize=True), "eyes_half.png")


def generate_eyes_closed():
    def closed_eye(cx, cy):
        return f"""
        <g>
            <!-- Closed eye curve with eyelashes -->
            <path d="M {cx - 7} {cy} Q {cx} {cy + 4}, {cx + 7} {cy}"
                  fill="none" stroke="{h('ey_li')}" stroke-width="1.8"
                  stroke-linecap="round"/>
            <!-- Lash tips -->
            <path d="M {cx - 7} {cy} L {cx - 8} {cy - 1.5}" fill="none"
                  stroke="{h('ey_li')}" stroke-width="0.8" stroke-linecap="round"/>
            <path d="M {cx + 7} {cy} L {cx + 8} {cy - 1.5}" fill="none"
                  stroke="{h('ey_li')}" stroke-width="0.8" stroke-linecap="round"/>
        </g>
        """
    svg = wrap(closed_eye(36, 40) + closed_eye(60, 40))
    save(svg_to_layer(svg, quantize=True), "eyes_closed.png")


# ── Mouth (SVG) ──────────────────────────────────────────────

def generate_mouth_neutral():
    svg = wrap(f"""
    <path d="M 43 58 Q 48 59, 53 58"
          fill="none" stroke="{h('li_sh')}" stroke-width="1.2"
          stroke-linecap="round"/>
    <path d="M 44 59 Q 48 60, 52 59"
          fill="none" stroke="{h('li_ba')}" stroke-width="0.6"
          stroke-linecap="round" opacity="0.6"/>
    """)
    save(svg_to_layer(svg, quantize=True), "mouth_neutral.png")


def generate_mouth_smile():
    svg = wrap(f"""
    <path d="M 42 57 Q 48 63, 54 57"
          fill="none" stroke="{h('li_sh')}" stroke-width="1.3"
          stroke-linecap="round"/>
    <!-- Lip color fill hint -->
    <path d="M 43 57.5 Q 48 62, 53 57.5"
          fill="{h('li_ba')}" opacity="0.5" stroke="none"/>
    """)
    save(svg_to_layer(svg, quantize=True), "mouth_smile.png")


# ── Eyebrows (SVG) ───────────────────────────────────────────

def generate_brows_neutral():
    svg = wrap(f"""
    <path d="M 29 30 Q 36 28, 43 30"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.4"
          stroke-linecap="round"/>
    <path d="M 53 30 Q 60 28, 67 30"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.4"
          stroke-linecap="round"/>
    """)
    save(svg_to_layer(svg, quantize=True), "brows_neutral.png")


def generate_brows_raised():
    svg = wrap(f"""
    <path d="M 29 27 Q 36 24, 43 27"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.3"
          stroke-linecap="round"/>
    <path d="M 53 27 Q 60 24, 67 27"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.3"
          stroke-linecap="round"/>
    """)
    save(svg_to_layer(svg, quantize=True), "brows_raised.png")


def generate_brows_furrowed():
    svg = wrap(f"""
    <path d="M 30 32 Q 36 30, 42 28"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.5"
          stroke-linecap="round"/>
    <path d="M 66 32 Q 60 30, 54 28"
          fill="none" stroke="{h('hr_sh')}" stroke-width="1.5"
          stroke-linecap="round"/>
    """)
    save(svg_to_layer(svg, quantize=True), "brows_furrowed.png")


# ── Blush (SVG) ──────────────────────────────────────────────

def generate_blush():
    svg = wrap(f"""
    <defs>
        <radialGradient id="bl">
            <stop offset="0%" stop-color="{h('blush')}" stop-opacity="0.45"/>
            <stop offset="100%" stop-color="{h('blush')}" stop-opacity="0"/>
        </radialGradient>
    </defs>
    <ellipse cx="33" cy="50" rx="9" ry="4.5" fill="url(#bl)"/>
    <ellipse cx="63" cy="50" rx="9" ry="4.5" fill="url(#bl)"/>
    <!-- Manga hash lines -->
    <g stroke="{h('blush')}" stroke-width="0.5" opacity="0.3"
       stroke-linecap="round">
        <line x1="29" y1="49" x2="31" y2="50"/>
        <line x1="33" y1="48" x2="35" y2="49"/>
        <line x1="37" y1="49" x2="38" y2="50"/>
        <line x1="59" y1="49" x2="61" y2="50"/>
        <line x1="63" y1="48" x2="65" y2="49"/>
        <line x1="67" y1="49" x2="68" y2="50"/>
    </g>
    """)
    save(svg_to_layer(svg), "blush.png")


# ── Pixel-art helpers ────────────────────────────────────────

def _selective_outline(arr):
    """Apply selective outlining: lit edges get hr_ba, shadow edges hr_sh."""
    alpha = arr[:, :, 3].copy()
    outline_px = []
    for y in range(96):
        for x in range(96):
            if alpha[y, x] == 0:
                continue
            has_empty = False
            lit_side = False
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < 96 and 0 <= nx < 96) or alpha[ny, nx] == 0:
                    has_empty = True
                    if dy < 0 or dx < 0:
                        lit_side = True
            if has_empty:
                c = P['hr_ba'] if lit_side else P['hr_sh']
                outline_px.append((y, x, c))
    for y, x, c in outline_px:
        arr[y, x] = (*c, 255)


# ── Hair curve helper ───────────────────────────────────────

def _bezier_pts(p0, p1, p2, n=80):
    """Pixel positions along a quadratic Bezier curve."""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        pt = (round(x), round(y))
        if not pts or pts[-1] != pt:
            pts.append(pt)
    return pts


# ── Hair back (v11 — closer to head, wavy edges) ──────────

def generate_hair_back():
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    arr = np.array(img)

    silhouette = [
        (48, 2),
        (55, 2), (62, 4), (68, 7), (73, 12), (77, 18),
        (80, 24), (82, 30), (83, 36), (82, 42),
        (84, 48), (83, 54), (84, 60), (82, 66),
        (80, 74), (77, 82), (73, 92), (70, 96),
        (26, 96),
        (23, 92), (19, 82), (16, 74),
        (14, 66), (12, 60), (13, 54), (12, 48),
        (14, 42), (13, 36), (14, 30), (16, 24),
        (19, 18), (23, 12), (28, 7), (34, 4), (41, 2),
    ]

    mask = Image.new("L", (96, 96), 0)
    ImageDraw.Draw(mask).polygon(silhouette, fill=255)
    mask_arr = np.array(mask)

    for y in range(96):
        for x in range(96):
            if mask_arr[y, x] == 0:
                continue
            row_px = np.where(mask_arr[y] > 0)[0]
            lx, rx = row_px[0], row_px[-1]
            w = max(1, rx - lx)
            pos = (x - lx) / w
            if pos < 0.28:
                c = P['hr_hi']
            elif pos < 0.58:
                c = P['hr_ba']
            else:
                c = P['hr_sh']
            arr[y, x] = (*c, 255)

    _selective_outline(arr)
    img = Image.fromarray(arr, "RGBA")
    save(img, "hair_back.png")


# ── Hair front (v11 — tighter, scalloped bangs) ───────────

def generate_hair_front():
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    arr = np.array(img)

    dome_pts = []
    dcx, dcy, drx, dry = 48, 16, 33, 14
    for i in range(50):
        t = i / 49
        x = 15 + 66 * t
        dx_v = max(-1.0, min(1.0, (x - dcx) / drx))
        y = dcy - dry * math.sqrt(max(0, 1 - dx_v * dx_v))
        pt = (round(x), round(y))
        if not dome_pts or dome_pts[-1] != pt:
            dome_pts.append(pt)

    bottom_edge = [
        (81, 20), (81, 23),
        (80, 25), (78, 28), (76, 30), (74, 29), (72, 27),
        (70, 25),
        (68, 27), (66, 30), (64, 32), (62, 33), (60, 31), (58, 28),
        (56, 26),
        (54, 29), (52, 33), (50, 35), (48, 36),
        (46, 35), (44, 33), (42, 29),
        (40, 26),
        (38, 28), (36, 31), (34, 33), (32, 32), (30, 30), (28, 27),
        (26, 25),
        (24, 27), (22, 29), (20, 30), (18, 28), (16, 25),
        (15, 23), (15, 20),
    ]

    bang_poly = dome_pts + bottom_edge

    mask = Image.new("L", (96, 96), 0)
    ImageDraw.Draw(mask).polygon(bang_poly, fill=255)
    mask_arr = np.array(mask)

    crown = (48, 5)
    for y in range(96):
        for x in range(96):
            if mask_arr[y, x] == 0:
                continue
            row_px = np.where(mask_arr[y] > 0)[0]
            if len(row_px) == 0:
                continue
            lx, rx_v = row_px[0], row_px[-1]
            w = max(1, rx_v - lx)
            pos = (x - lx) / w

            angle = math.atan2(y - crown[1], x - crown[0])
            sector = int((angle + math.pi) * 5 / math.pi)
            shift = 0.04 if sector % 2 == 0 else -0.04
            eff = max(0.0, min(1.0, pos + shift))

            if eff < 0.28:
                c = P['hr_hi']
            elif eff < 0.60:
                c = P['hr_ba']
            else:
                c = P['hr_sh']
            arr[y, x] = (*c, 255)

    for y in range(4, 9):
        row_px = np.where(mask_arr[y] > 0)[0]
        if len(row_px) == 0:
            continue
        lx, rx_v = row_px[0], row_px[-1]
        w = max(1, rx_v - lx)
        fade = 1.0 - (y - 4) / 5.0
        for x in row_px:
            pos = (x - lx) / w
            if 0.15 < pos < 0.45:
                a = 0.35 * fade
                base = tuple(arr[y, x, :3])
                s = P['hr_hh']
                c = tuple(int(s[i] * a + base[i] * (1 - a)) for i in range(3))
                arr[y, x] = (*c, 255)

    sl_left = [
        (15, 20), (13, 26), (12, 34), (11, 42),
        (11, 48), (12, 54), (13, 58),
        (15, 54), (16, 46), (16, 38), (16, 30), (15, 24),
    ]
    sl_right = [
        (81, 20), (83, 26), (84, 34), (85, 42),
        (85, 48), (84, 54), (83, 58),
        (81, 54), (80, 46), (80, 38), (80, 30), (81, 24),
    ]
    for sl_poly, sl_lit, sl_shd in [
        (sl_left, P['hr_hi'], P['hr_ba']),
        (sl_right, P['hr_ba'], P['hr_sh']),
    ]:
        sl_mask = Image.new("L", (96, 96), 0)
        ImageDraw.Draw(sl_mask).polygon(sl_poly, fill=255)
        sl_m = np.array(sl_mask)
        for y in range(96):
            filled = np.where(sl_m[y] > 0)[0]
            if len(filled) == 0:
                continue
            lx_s, rx_s = filled[0], filled[-1]
            w_s = max(1, rx_s - lx_s)
            for x in filled:
                pos = (x - lx_s) / w_s
                arr[y, x] = (*(sl_lit if pos < 0.45 else sl_shd), 255)

    _selective_outline(arr)
    img = Image.fromarray(arr, "RGBA")
    save(img, "hair_front.png")


# ── FX sprites ───────────────────────────────────────────────

def generate_fx_hearts():
    svg = wrap(f"""
    <!-- Large heart -->
    <path d="M 76 14 C 73 9, 67 9, 67 14 C 67 19, 76 24, 76 24
             C 76 24, 85 19, 85 14 C 85 9, 79 9, 76 14 Z"
          fill="{h('heart')}" stroke="{h('outln')}" stroke-width="0.4"/>
    <ellipse cx="72" cy="12.5" rx="2" ry="1.5"
             fill="{h('hrt_h')}" opacity="0.6"/>

    <!-- Small heart -->
    <path d="M 82 25 C 80 22, 77 22, 77 25 C 77 28, 82 30, 82 30
             C 82 30, 87 28, 87 25 C 87 22, 84 22, 82 25 Z"
          fill="{h('hrt_h')}" opacity="0.7"
          stroke="{h('outln')}" stroke-width="0.3"/>
    """)
    save(svg_to_layer(svg), "fx_hearts.png")


def generate_fx_sweat():
    svg = wrap(f"""
    <path d="M 18 8 Q 13 16, 13 22 C 13 27, 17 29, 19 29
             C 21 29, 25 27, 25 22 Q 25 16, 18 8 Z"
          fill="{h('sweat')}" stroke="{h('ey_lo')}" stroke-width="0.5"/>
    <ellipse cx="18" cy="22" rx="2.5" ry="3.5"
             fill="{h('swt_h')}" opacity="0.5"/>
    """)
    save(svg_to_layer(svg), "fx_sweat.png")


def generate_fx_steam():
    svg = wrap(f"""
    <g fill="none" stroke="{h('sweat')}" stroke-width="1.4"
       stroke-linecap="round" opacity="0.35">
        <path d="M 30 7 Q 34 3, 38 7 Q 42 11, 46 7"/>
        <path d="M 42 4 Q 46 0, 50 4 Q 54 8, 58 4"/>
        <path d="M 56 8 Q 60 4, 64 8 Q 68 12, 72 8"/>
    </g>
    """)
    save(svg_to_layer(svg), "fx_steam.png")


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(ASSET_DIR, exist_ok=True)
    print("Generating portrait assets (v8 — pixel-native hair)...")

    generate_body_base()
    generate_hair_back()
    generate_hair_front()

    generate_eyes_open()
    generate_eyes_half()
    generate_eyes_closed()

    generate_mouth_neutral()
    generate_mouth_smile()

    generate_brows_neutral()
    generate_brows_raised()
    generate_brows_furrowed()

    generate_blush()

    generate_fx_hearts()
    generate_fx_sweat()
    generate_fx_steam()

    print("Done — 15 assets in assets/portrait/")
