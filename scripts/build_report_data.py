"""
Collect every number shown in reports/tourism_report.html and inject it into the page.

Usage (from anywhere, after scripts/extract_tables.py and notebook 01):
    python scripts/build_report_data.py
"""
import json
import re
import numpy as np
import pandas as pd
from tourism import (ROOT, PROC, MON, GORILLA_PERMIT_USD, load_parks_annual, load_parks_monthly, load_parks_category,
                     load_arrivals_purpose, load_arrivals_monthly, load_arrivals_region, load_overseas_markets,
                     load_gorilla, load_chimp, load_untourism, load_rainfall)

REPORT = ROOT / 'reports' / 'tourism_report.html'


def r4(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 4)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


def main():
    ap = load_arrivals_purpose().set_index('year')
    cols = ['Leisure and holiday', 'Business and professional', 'Visiting friends and relatives', 'Other']
    purpose = [{'y': int(y), **{c: r4(r[c]) for c in cols}, 'src': r['source']} for y, r in ap.iterrows()]

    ar = load_arrivals_region()
    over = ['AMERICAS', 'EAST ASIA AND THE PACIFIC', 'EUROPE', 'MIDDLE EAST', 'SOUTH ASIA']
    regions = {int(y): {'Africa': r4(r['AFRICA']), 'outside': r4(r[over].sum()), 'total': r4(r['TOTAL'])} for y, r in ar.iterrows()}
    om = load_overseas_markets()
    markets = [{'m': r['market'], 'v': int(r['arrivals'])} for _, r in om[om['year'] == 2024].sort_values('rank').iterrows()]

    tr = load_untourism('travel')
    peers = ['Uganda', 'Kenya', 'Tanzania', 'Rwanda', 'Ethiopia', 'Zambia', 'Namibia', 'South Africa', 'Botswana', 'Zimbabwe']
    receipts = {c: [{'y': int(y), 'v': r4(v)} for y, v in tr[c].loc[2015:2023].items() if pd.notna(v)] for c in peers}
    recovery = {c: r4(tr.loc[2023, c] / tr.loc[2019, c] * 100) for c in peers}

    pa = load_parks_annual()
    parks_total = [{'y': int(y), 'v': int(v)} for y, v in pa.groupby('year')['visits'].sum().items()]
    by = pa.pivot_table(index='year', columns='park', values='visits')
    top = by.loc[2024].sort_values(ascending=False).index[:6].tolist()
    parks_by = {p: [{'y': int(y), 'v': r4(v)} for y, v in by[p].items() if pd.notna(v)] for p in top}
    top3 = (by[['Murchison Falls', 'Queen Elizabeth', 'Bwindi Impenetrable']].sum(axis=1) / by.sum(axis=1))
    pc = load_parks_category().pivot_table(index='year', columns='category', values='visits')
    cats = [{'y': int(y), **{c: r4(v) for c, v in r.items()}} for y, r in pc.iterrows()]

    pm = load_parks_monthly()
    normal = pm[~pm['year'].isin([2020, 2021])]
    ps = normal.assign(s=normal['visits'] / normal.groupby('year')['visits'].transform('sum') * 100).groupby('month')['s'].mean()
    g = load_gorilla()
    gm = g[g['year'].isin([2023, 2024])].groupby('month')[['sold', 'available']].sum()
    am = load_arrivals_monthly()
    an = am[am['year'].isin([2023, 2024])]
    ams = an.assign(s=an['arrivals'] / an.groupby('year')['arrivals'].transform('sum') * 100).groupby('month')['s'].mean()
    rain = load_rainfall('Western')
    season = {'parks': [r4(v) for v in ps], 'gorilla': [r4(v) for v in gm['sold'] / gm['available'] * 100],
              'arrivals': [r4(v) for v in ams], 'rain': [r4(v) for v in rain]}
    parks_monthly = [{'d': f'{d:%Y-%m}', 'v': int(v)} for d, v in pm.set_index('date')['visits'].items()]

    gy = g.groupby('year')[['available', 'sold']].sum()
    gorilla_year = [{'y': int(y), 'a': int(r['available']), 's': int(r['sold'])} for y, r in gy.iterrows()]
    gorilla_month = {int(y): [r4(v) for v in x.sort_values('month')['utilisation'] * 100] for y, x in g[g['year'] >= 2022].groupby('year')}
    unsold24 = int(gy.loc[2024, 'available'] - gy.loc[2024, 'sold'])
    g24 = g[g['year'] == 2024].set_index('month')
    wet_unsold = int((g24.loc[[3, 4, 5, 11], 'available'] - g24.loc[[3, 4, 5, 11], 'sold']).sum())
    ch = load_chimp().groupby('year')[['available', 'sold']].sum()

    kpi = {'leisure_share': r4(ap.loc[2024, 'Leisure and holiday'] / ap.loc[2024, cols].sum() * 100),
           'leisure_2024': r4(ap.loc[2024, 'Leisure and holiday']),
           'parks_2024': int(by.loc[2024].sum()), 'parks_vs_2019': r4(by.loc[2024].sum() / by.loc[2019].sum() * 100),
           'fnr_vs_2019': r4(pc.loc[2024, 'Foreign Non Residents'] / pc.loc[2019, 'Foreign Non Residents'] * 100),
           'gorilla_sold_2024': r4(gy.loc[2024, 'sold'] / gy.loc[2024, 'available'] * 100),
           'gorilla_sold_2023': r4(gy.loc[2023, 'sold'] / gy.loc[2023, 'available'] * 100),
           'unsold_2024': unsold24, 'unsold_value_m': r4(unsold24 * GORILLA_PERMIT_USD['Foreign non-resident'] / 1e6),
           'wet_unsold_share': r4(wet_unsold / unsold24 * 100),
           'chimp_sold_2024': r4(ch.loc[2024, 'sold'] / ch.loc[2024, 'available'] * 100),
           'recovery_uganda': recovery['Uganda'], 'top3_min': r4(top3.min() * 100), 'top3_max': r4(top3.max() * 100),
           'jul_aug': r4(ps.loc[[7, 8]].sum()), 'march': r4(ps.loc[3]),
           'africa_share': r4(ar.loc[2024, 'AFRICA'] / ar.loc[2024, 'TOTAL'] * 100),
           'outside_2024': r4(ar.loc[2024, over].sum())}
    data = clean({'purpose': purpose, 'regions': regions, 'markets': markets, 'receipts': receipts, 'recovery': recovery,
                  'parks_total': parks_total, 'parks_by': parks_by, 'cats': cats, 'season': season, 'months': MON,
                  'parks_monthly': parks_monthly, 'gorilla_year': gorilla_year, 'gorilla_month': gorilla_month, 'kpi': kpi})
    payload = json.dumps(data, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')
    s = REPORT.read_text()
    s, n = re.subn(r'(<script id="report-data" type="application/json">)(.*?)(</script>)',
                   lambda m: m.group(1) + payload + m.group(3), s, flags=re.S)
    if n != 1:
        raise SystemExit(f'expected one report-data block, found {n}')
    REPORT.write_text(s)
    print(f'updated {REPORT.relative_to(ROOT)} ({len(payload) / 1024:.0f} KB of data)')
    print(json.dumps(data['kpi'], indent=0))


if __name__ == '__main__':
    main()
