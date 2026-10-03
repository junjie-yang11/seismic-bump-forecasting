"""Paper figures from audited extended experiment tables."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from figures import _font, PALETTE, FG, MUTED, GRID, AXIS


def render(root):
    out = root / 'results/figures'
    importance = pd.read_csv(root / 'results/shap_importance.csv')
    global_rows = importance[(importance.validation == 'time') & (importance.fold == -1)].sort_values('mean_abs', ascending=False).head(8)
    phase = importance[(importance.validation == 'time') & (importance.fold >= 0)]
    img = Image.new('RGB', (1400, 700), 'white'); d = ImageDraw.Draw(img)
    d.text((35, 24), 'XGBoost contributions and stability across four test phases', font=_font(31, True), fill=FG)
    ox, oy, width = 240, 140, 350
    maximum = float(global_rows.mean_abs.max()) * 1.15
    d.text((ox + width / 2, 96), 'Global mean absolute contribution', font=_font(24), fill=FG, anchor='mm')
    for t in range(5):
        x = ox + width * t / 4
        d.line((x, oy - 10, x, oy + 8 * 57), fill=GRID)
        d.text((x, oy + 8 * 57 + 10), '%.2f' % (maximum * t / 4), font=_font(22), fill=MUTED, anchor='ma')
    for j, (_, r) in enumerate(global_rows.iterrows()):
        y = oy + j * 57
        d.text((ox - 18, y + 18), r.feature, font=_font(26), fill=FG, anchor='rm')
        x = ox + width * float(r.mean_abs) / maximum
        d.rectangle((ox, y, x, y + 34), fill=PALETTE[0])
        for f in range(4):
            part = phase[phase.fold == f]
            share = float(part[part.feature == r.feature].mean_abs.iloc[0] / part.mean_abs.sum())
            tint = min(1, share / .30); colour = (int(245 - 195 * tint), int(249 - 126 * tint), int(255 - 75 * tint))
            left = 745 + f * 142
            d.rectangle((left, y, left + 136, y + 42), fill=colour)
            d.text((left + 68, y + 21), '%.1f%%' % (share * 100), font=_font(25), fill='white' if tint > .75 else FG, anchor='mm')
    for f in range(4):
        d.text((813 + f * 142, 96), 'Phase %d' % (f + 1), font=_font(25, True), fill=FG, anchor='mm')
    d.text((35, 632), 'Top eight global features; heatmap cells give within-phase shares of absolute feature contributions.', font=_font(23), fill=MUTED)
    d.text((35, 664), 'Native exact TreeSHAP on raw log-odds; training leaf covers define the reference distribution.', font=_font(23), fill=MUTED)
    img.save(out / 'shap_phase_stability.png')

    budgets = pd.read_csv(root / 'results/warning_budgets.csv')
    img = Image.new('RGB', (1400, 760), 'white'); d = ImageDraw.Draw(img)
    d.text((35, 24), 'Detection and workload under training reference budgets', font=_font(31, True), fill=FG)
    for panel, scheme in enumerate(('time', 'holdout')):
        ox, oy, w, h = 100 + 700 * panel, 145, 510, 390
        d.text((ox + w / 2, 98), 'Record-order tests' if scheme == 'time' else 'Previously inspected holdout', font=_font(26, True), fill=FG, anchor='mm')
        for t in range(5):
            x, y = ox + w * t / 4, oy + h * t / 4
            d.line((x, oy, x, oy + h), fill=GRID); d.line((ox, y, ox + w, y), fill=GRID)
            d.text((x, oy + h + 12), '%d%%' % (10 * t), font=_font(24), fill=MUTED, anchor='ma')
            d.text((ox - 12, y), '%.2f' % (.5 * (1 - t / 4)), font=_font(23), fill=MUTED, anchor='rm')
        d.rectangle((ox, oy, ox + w, oy + h), outline=AXIS, width=2)
        d.text((ox, oy - 25), 'Recall', font=_font(23), fill=FG)
        for ci, model in enumerate(('LR', 'CART', 'XGBoost')):
            part = budgets[(budgets.validation == scheme) & (budgets.model == model)].sort_values('budget')
            points = [(ox + w * r.alert_rate / .4, oy + h * (1 - r.recall / .5)) for _, r in part.iterrows()]
            d.line(points, fill=PALETTE[ci], width=3)
            for i, (x, y) in enumerate(points):
                radius = (5, 8, 11, 14)[i]
                d.ellipse((x - radius, y - radius, x + radius, y + radius), outline=PALETTE[ci], width=3)
        d.text((ox + w / 2, oy + h + 58), 'Actual alerted fraction of test rows', font=_font(25), fill=FG, anchor='mm')
    for ci, model in enumerate(('LR', 'CART', 'XGBoost')):
        x = 100 + 220 * ci
        d.line((x, 641, x + 38, 641), fill=PALETTE[ci], width=4)
        d.text((x + 48, 641), model, font=_font(25), fill=FG, anchor='lm')
    d.text((800, 641), 'Larger circles: 1, 5, 10, 20% budgets', font=_font(23), fill=FG, anchor='lm')
    d.text((35, 705), 'Same model scores across policies; thresholds frozen inside training. Lines connect evaluated policies.', font=_font(24), fill=MUTED)
    img.save(out / 'research_warning_tradeoff.png')

    shap = pd.read_csv(root / 'results/shap_predictions.csv').query('validation == "time"')
    from data import load
    X, _, names, _ = load()
    img = Image.new('RGB', (1400, 520), 'white'); d = ImageDraw.Draw(img)
    d.text((35, 22), 'Feature values and test-set contributions', font=_font(30, True), fill=FG)
    for panel, feature in enumerate(global_rows.feature.head(3)):
        raw = X[shap.row.to_numpy(dtype=int), names.index(feature)]
        transformed = np.sign(raw) * np.log1p(np.abs(raw))
        contribution = shap['shap__' + feature].to_numpy()
        ox, oy, w, h = 85 + panel * 460, 120, 350, 265
        xmin, xmax = transformed.min(), transformed.max(); ymin, ymax = contribution.min(), contribution.max()
        xspan, yspan = max(xmax - xmin, .01), max(ymax - ymin, .01)
        d.text((ox + w / 2, 83), feature, font=_font(27, True), fill=FG, anchor='mm')
        d.rectangle((ox, oy, ox + w, oy + h), outline=AXIS, width=2)
        for f in range(4):
            mask = shap.fold.to_numpy() == f
            for x, y in zip(transformed[mask], contribution[mask]):
                px, py = ox + (x - xmin) / xspan * w, oy + h - (y - ymin) / yspan * h
                d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=PALETTE[f])
        for value, y in ((ymin, oy + h), (ymax, oy)):
            d.text((ox - 8, y), '%.1f' % value, font=_font(22), fill=MUTED, anchor='rm')
        for value, x in ((xmin, ox), (xmax, ox + w)):
            d.text((x, oy + h + 8), '%.1f' % value, font=_font(22), fill=MUTED, anchor='ma')
        d.text((ox + w / 2, 435), 'Signed log1p of observed feature value', font=_font(21), fill=FG, anchor='mm')
    for f in range(4):
        d.text((65 + f * 285, 484), 'Phase %d' % (f + 1), font=_font(24), fill=PALETTE[f])
    img.save(out / 'shap_dependence.png')

    cases = pd.read_csv(root / 'results/shap_cases.csv').query('validation == "holdout" and available == True')
    values = pd.read_csv(root / 'results/shap_case_contributions.csv')
    img = Image.new('RGB', (1400, 530), 'white'); d = ImageDraw.Draw(img)
    d.text((35, 22), 'Holdout warning cases at the 10% training reference budget', font=_font(29, True), fill=FG)
    for panel, (_, case) in enumerate(cases.iterrows()):
        part = values[(values.validation == 'holdout') & (values.category == case.category)].copy()
        part['absolute'] = part.contribution.abs(); part = part.sort_values('absolute', ascending=False)
        top = list(zip(part.feature.head(5), part.contribution.head(5))) + [('Other features', part.contribution.iloc[5:].sum())]
        left = 35 + panel * 460
        oy = 165; ox = left + 320; half = 100
        maximum = max(abs(v) for _, v in top) * 1.15
        d.text((left, 88), '%s | mirror row %d' % (case.category, int(case.row) + 1), font=_font(27, True), fill=FG)
        d.text((left, 124), 'p=%.4f | cutoff=%.4f' % (case.score, case.threshold), font=_font(24), fill=FG)
        d.line((ox, oy - 8, ox, oy + 6 * 39), fill=AXIS, width=2)
        for j, (feature, value) in enumerate(top):
            y = oy + j * 39; end = ox + half * value / maximum
            d.text((left, y + 13), 'Others' if feature == 'Other features' else feature, font=_font(24), fill=FG, anchor='lm')
            d.rectangle((min(ox, end), y, max(ox, end), y + 26), fill=PALETTE[1 if value > 0 else 0])
            d.text((left + 145, y + 13), '%+.3f' % value, font=_font(24), fill=FG, anchor='lm')
        d.text((left, 440), 'Bias %.3f | margin %.3f' % (case.bias, case.margin), font=_font(24), fill=MUTED)
    d.text((35, 489), 'First chronological row per outcome. Contributions plus bias reconstruct raw log-odds; Others pools remaining features.', font=_font(23), fill=MUTED)
    img.save(out / 'shap_warning_cases.png')
