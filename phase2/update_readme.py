"""Generate the homepage decision table from saved counts, without fitting."""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN GENERATED DECISION TABLE -->'
END = '<!-- END GENERATED DECISION TABLE -->'


def decision_table(path):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        rows = [row for row in csv.DictReader(handle)
                if row['model'] == 'XGBoost' and row['workflow'] == 'fixed'
                and row['mechanism'] == 'C' and float(row['cost']) == 10]
    rows.sort(key=lambda row: float(row['budget']))
    if [float(row['budget']) for row in rows] != [.01, .05, .10, .20]:
        raise ValueError('Expected one pooled fixed XGBoost C row per locked budget at r=10')
    cohorts = {(int(float(row['n'])), int(float(row['tp']))+int(float(row['fn']))) for row in rows}
    if len(cohorts) != 1:
        raise ValueError('Displayed policies must cover the same pooled records')
    n, positives = cohorts.pop()
    lines = [f'**Fixed XGBoost · rule C · r=10 · four later blocks pooled ({n:,} shifts; {positives} hazardous labels).**', '',
             '| Historical budget | Δ loss / 100 vs no alarms | TP | FN | Alerts |',
             '| --- | --- | --- | --- | --- |']
    for row in rows:
        tp, fp, fn, alerts = (int(float(row[key])) for key in ('tp', 'fp', 'fn', 'alerts'))
        if alerts != tp+fp or tp+fn != positives:
            raise ValueError('Inconsistent confusion counts')
        delta = 100*(fp-10*tp)/n
        if abs(delta-float(row['delta_loss_vs_no_alarm_100'])) > 1e-10:
            raise ValueError('Saved relative loss does not agree with its underlying counts')
        formatted = '0.00' if delta == 0 else f'{delta:+.2f}'
        lines.append(f'| {float(row["budget"]):.0%} | {formatted} | {tp} | {fn} | {alerts} |')
    lines.extend(['', '**Negative differences mean lower assumed loss; positive differences mean higher loss.** '
                  'False-alert cost is 1 and missed hazardous-shift cost is 10. Budgets constrain historical selection, '
                  'not later workload. TP counts hazardous shifts flagged, not inspections completed or accidents prevented.', '',
                  'Generated from [saved pooled results](results/phase2/decision_value_pooled.csv) by '
                  '[the table updater](phase2/update_readme.py); Δ loss is independently reconstructed as `100(FP − 10TP)/N`.'])
    return '\n'.join(lines)


def update(root=ROOT, check=False):
    root = Path(root)
    path = root/'README.md'
    text = path.read_text(encoding='utf-8')
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError('Expected exactly one pair of generated table markers')
    before, rest = text.split(BEGIN)
    _, after = rest.split(END)
    generated = before+BEGIN+'\n'+decision_table(root/'results/phase2/decision_value_pooled.csv')+'\n'+END+after
    if check:
        if generated != text:
            raise AssertionError('Homepage decision table is stale: run python -m phase2.update_readme')
    else:
        path.write_text(generated, encoding='utf-8')
    print('Homepage decision table matches saved counts.' if check else 'Homepage decision table regenerated from saved counts.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    update(check=parser.parse_args().check)
