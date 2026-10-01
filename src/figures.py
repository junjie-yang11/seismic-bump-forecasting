"""
Figure rendering with Pillow only — no matplotlib dependency.

Produces PNG files suitable for embedding in the report:

    roc_curves.png           ROC curves, 4 model x validation combinations
    pr_curves.png            precision-recall curves, same 4 combinations
    pr_auc_by_scheme.png     PR-AUC by model and validation scheme
    prevalence_drift.png     label prevalence across the record sequence

Fonts: tries a few common Windows TrueType fonts, falls back to the Pillow
default bitmap font if none is present.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\verdana.ttf",
]
_BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
]

BG = (255, 255, 255)
FG = (34, 34, 34)
MUTED = (95, 95, 95)
GRID = (228, 228, 228)
AXIS = (130, 130, 130)
PALETTE = [(44, 111, 187), (192, 57, 43), (31, 111, 60), (176, 106, 0)]


def _font(size: int, bold: bool = False):
    for path in (_BOLD_CANDIDATES if bold else _FONT_CANDIDATES):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _rotated_label(img, text, font, fill, centre_xy):
    """Draw `text` rotated 90 degrees anticlockwise, centred on centre_xy."""
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    w = int(probe.textlength(text, font=font)) + 12
    h = 34
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((w // 2, h // 2), text, font=font, fill=fill,
                             anchor="mm")
    tmp = tmp.rotate(90, expand=True)
    img.paste(tmp, (int(centre_xy[0] - tmp.width / 2),
                    int(centre_xy[1] - tmp.height / 2)), tmp)


def _frame(d, ox, oy, w, h):
    d.rectangle([ox, oy, ox + w, oy + h], outline=AXIS, width=2)
    for i in range(1, 10):
        x = ox + w * i / 10
        y = oy + h * i / 10
        if i % 2 == 0:
            d.line([x, oy, x, oy + h], fill=GRID, width=1)
            d.line([ox, y, ox + w, y], fill=GRID, width=1)


def save_curves_png(path, curves, title, xlab, ylab, diagonal=False,
                    legend_cols=2):
    """curves: list of (label, points Nx2 in [0,1], colour_index, dashed)"""
    W, H = 1120, 720
    ox, oy, pw, ph = 118, 108, 700, 470
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = _font(25, True)
    f_lab = _font(19)
    f_tick = _font(15)
    f_leg = _font(17)

    d.text((48, 34), title, font=f_title, fill=FG)
    _frame(d, ox, oy, pw, ph)
    if diagonal:
        d.line([ox, oy + ph, ox + pw, oy], fill=(205, 205, 205), width=2)

    for v in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        d.text((ox - 12, oy + ph - v * ph), "%.1f" % v, font=f_tick, fill=MUTED,
               anchor="rm")
        d.text((ox + v * pw, oy + ph + 10), "%.1f" % v, font=f_tick, fill=MUTED,
               anchor="ma")

    # curves, with a genuine dash pattern
    for label, pts, ci, dashed in curves:
        colour = PALETTE[ci % len(PALETTE)]
        prev = None
        for k, (x, y) in enumerate(pts):
            x = min(max(float(x), 0.0), 1.0)
            y = min(max(float(y), 0.0), 1.0)
            cur = (ox + x * pw, oy + ph - y * ph)
            if prev is not None:
                if not dashed or (k // 3) % 2 == 0:
                    d.line([prev[0], prev[1], cur[0], cur[1]], fill=colour, width=3)
            prev = cur

    d.text((ox + pw / 2, oy + ph + 36), xlab, font=f_lab, fill=FG, anchor="ma")
    _rotated_label(img, ylab, f_lab, FG, (52, oy + ph / 2))

    # legend: 2 columns, one entry per model x validation combination
    lx0, ly0 = 118, oy + ph + 78
    col_w = 460
    for n, (label, _, ci, dashed) in enumerate(curves):
        col, row = n % legend_cols, n // legend_cols
        lx = lx0 + col * col_w
        ly = ly0 + row * 32
        colour = PALETTE[ci % len(PALETTE)]
        if dashed:
            for seg in range(3):
                x1 = lx + seg * 14
                d.line([x1, ly, x1 + 8, ly], fill=colour, width=4)
        else:
            d.line([lx, ly, lx + 42, ly], fill=colour, width=4)
        d.text((lx + 54, ly), label, font=f_leg, fill=FG, anchor="lm")
    img.save(path)
    return path


def save_reliability_png(path, panels, title):
    """Reliability diagrams, one panel per curve set.

    panels: list of (subtitle, mean_pred, obs_freq, counts). Each panel gets its
    own axes, because the whole point is that the before/after scales differ by
    an order of magnitude.
    """
    import numpy as np
    n = len(panels)
    pw, ph = 400, 400
    gap = 150
    W = 130 + n * pw + (n - 1) * gap + 130
    H = 150 + ph + 170
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = _font(25, True)
    f_sub = _font(19, True)
    f_lab = _font(16)
    f_tick = _font(14)
    f_leg = _font(16)

    d.text((48, 32), title, font=f_title, fill=FG)

    for k, (sub, mp, of, cnt) in enumerate(panels):
        ox = 130 + k * (pw + gap)
        oy = 130
        hi = float(max(np.max(mp), np.max(of))) if len(mp) else 1.0
        for cand in (0.05, 0.1, 0.2, 0.25, 0.5, 1.0):
            if hi <= cand:
                hi = cand
                break
        _frame(d, ox, oy, pw, ph)
        d.text((ox, oy - 34), sub, font=f_sub, fill=FG)

        # diagonal = perfect calibration
        d.line([ox, oy + ph, ox + pw, oy], fill=(195, 195, 195), width=2)

        colour = PALETTE[k % len(PALETTE)]
        pts = []
        for a, b in zip(mp, of):
            x = ox + min(float(a) / hi, 1.0) * pw
            y = oy + ph - min(float(b) / hi, 1.0) * ph
            pts.append((x, y))
        for i in range(len(pts) - 1):
            d.line([pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]],
                   fill=colour, width=3)
        for x, y in pts:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=colour)

        for v in (0.0, 0.25, 0.5, 0.75, 1.0):
            d.text((ox - 10, oy + ph - v * ph), "%.2f" % (v * hi), font=f_tick,
                   fill=MUTED, anchor="rm")
            d.text((ox + v * pw, oy + ph + 10), "%.2f" % (v * hi), font=f_tick,
                   fill=MUTED, anchor="ma")

    ly = 150 + ph + 54
    d.text((130 + (n * pw + (n - 1) * gap) / 2, ly + 22),
           "mean predicted probability", font=f_lab, fill=FG, anchor="ma")
    _rotated_label(img, "observed frequency", f_lab, FG, (74, 130 + ph / 2))
    d.text((130, ly + 2),
           "grey diagonal = perfect calibration   \u00b7   points = decile bins",
           font=f_leg, fill=MUTED)
    img.save(path)
    return path


def save_bars_png(path, labels, values, title, ymax=1.0, fmt="%.3f",
                  highlight=None):
    """Horizontal bar chart. `highlight` = index to colour differently."""
    n = len(labels)
    row = 62
    W = 1180
    H = 160 + n * row + 80
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = _font(24, True)
    f_lab = _font(19)
    f_val = _font(19, True)
    f_tick = _font(15)

    d.text((48, 34), title, font=f_title, fill=FG)
    ox = 430
    plot_w = W - ox - 140
    top = 116
    # pick tick precision from the axis range, so a small axis does not get
    # misleading labels such as "0.0, 0.0, 0.1, 0.1"
    tick_fmt = "%.3f" if ymax < 0.05 else ("%.2f" if ymax < 0.5 else "%.1f")
    d.line([ox, top - 12, ox, top + n * row], fill=AXIS, width=2)
    for i in range(6):
        x = ox + plot_w * i / 5
        d.line([x, top - 12, x, top + n * row], fill=GRID, width=1)
        d.text((x, top + n * row + 12), tick_fmt % (ymax * i / 5), font=f_tick,
               fill=MUTED, anchor="ma")
    for i, (lab, val) in enumerate(zip(labels, values)):
        y = top + i * row
        bar_h = 34
        w = max(2, val / ymax * plot_w)
        ci = highlight if (highlight is not None and i == 0) else i
        d.rectangle([ox + 1, y, ox + w, y + bar_h], fill=PALETTE[ci % len(PALETTE)])
        d.text((ox - 18, y + bar_h / 2), lab, font=f_lab, fill=FG, anchor="rm")
        d.text((ox + w + 14, y + bar_h / 2), fmt % val, font=f_val, fill=FG,
               anchor="lm")
    img.save(path)
    return path
