"""Static experiment figures using the project's existing Pillow runtime."""
import sys
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from figures import _font, PALETTE, FG, MUTED, GRID, AXIS

LABELS = {'full': 'All features', 'ratings_only': 'Hazard ratings only',
    'without_ratings': 'Without hazard ratings', 'geophone_only': 'Geophone only',
    'without_geophone': 'Without geophone', 'seismic_activity_only': 'Seismic activity only',
    'without_seismic_activity': 'Without seismic activity', 'operation_only': 'Shift type only',
    'without_operation': 'Without shift type'}


def render(root):
    out = root / 'results/figures'
    ablation = pd.read_csv(root / 'results/feature_ablation.csv')
    img = Image.new('RGB', (1400, 830), 'white'); d = ImageDraw.Draw(img)
    d.text((40, 25), 'Engineering feature groups on the same 2,063 test rows', font=_font(30, True), fill=FG)
    maximum = max(.12, ablation.pr_auc.max() * 1.15)
    variants = list(LABELS)
    for panel, model in enumerate(('LR', 'CART')):
        ox, oy, width = 340 + panel * 505, 145, 390
        d.text((ox + width / 2, 90), model, font=_font(27, True), fill=FG, anchor='mm')
        for t in range(5):
            value = maximum * t / 4; x = ox + width * t / 4
            d.line((x, oy - 15, x, oy + 9 * 62), fill=GRID, width=1)
            d.text((x, oy + 9 * 62 + 12), '%.3f' % value, font=_font(20), fill=MUTED, anchor='ma')
        for i, variant in enumerate(variants):
            value = float(ablation[(ablation.model == model) & (ablation.variant == variant)].pr_auc.iloc[0])
            y = oy + i * 62
            if panel == 0:
                d.text((ox - 18, y + 16), LABELS[variant], font=_font(22, variant == 'full'), fill=FG, anchor='rm')
            x = ox + width * value / maximum
            d.rectangle((ox, y, x, y + 30), fill=PALETTE[panel])
            d.text((x + 8, y + 15), '%.4f' % value, font=_font(21), fill=FG, anchor='lm')
        d.text((ox + width / 2, 755), 'Average precision', font=_font(23), fill=FG, anchor='mm')
    d.text((40, 794), 'Fixed model settings and record-order folds; no selection of feature sets from test outcomes.', font=_font(21), fill=MUTED)
    img.save(out / 'engineering_ablation.png')

    budgets = pd.read_csv(root / 'results/warning_budgets.csv')
    img = Image.new('RGB', (1400, 1000), 'white'); d = ImageDraw.Draw(img)
    d.text((40, 25), 'Warning detection versus realized inspection workload', font=_font(30, True), fill=FG)
    for panel, (scheme, model) in enumerate((('time', 'LR'), ('time', 'CART'), ('holdout', 'LR'), ('holdout', 'CART'))):
        part = budgets[(budgets.validation == scheme) & (budgets.model == model)].sort_values('budget')
        ox, oy = 100 + panel % 2 * 690, 155 + panel // 2 * 420
        width, height = 470, 260
        xmax = max(.10, float(part.alert_rate.max()) * 1.3)
        d.text((ox + width / 2, oy - 48), '%s | %s (%d hazards)' % (model, 'Record order' if scheme == 'time' else 'Holdout', int(part.positives.iloc[0])), font=_font(24, True), fill=FG, anchor='mm')
        for t in range(5):
            x, y = ox + width * t / 4, oy + height * t / 4
            d.line((x, oy, x, oy + height), fill=GRID); d.line((ox, y, ox + width, y), fill=GRID)
            d.text((x, oy + height + 10), '%.0f%%' % (100 * xmax * t / 4), font=_font(20), fill=MUTED, anchor='ma')
            d.text((ox - 10, y), '%.2f' % (1 - t / 4), font=_font(20), fill=MUTED, anchor='rm')
        d.rectangle((ox, oy, ox + width, oy + height), outline=AXIS, width=2)
        points = [(ox + width * r.alert_rate / xmax, oy + height * (1 - r.recall)) for _, r in part.iterrows()]
        d.line(points, fill=PALETTE[panel % 2], width=3)
        for i, ((x, y), (_, r)) in enumerate(zip(points, part.iterrows())):
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=PALETTE[panel % 2])
            d.text((x + 10, y - 18 - i % 2 * 15), '%.0f%%' % (r.budget * 100), font=_font(21, True), fill=FG)
        d.text((ox + width / 2, oy + height + 55), 'Actual alerted fraction of test rows', font=_font(22), fill=FG, anchor='mm')
        d.text((ox, oy - 17), 'Recall', font=_font(20), fill=MUTED)
    d.text((40, 958), 'Point labels: training reference budgets. Lines connect evaluated policies; future alert rates may differ.', font=_font(21), fill=MUTED)
    img.save(out / 'warning_budget_tradeoff.png')
