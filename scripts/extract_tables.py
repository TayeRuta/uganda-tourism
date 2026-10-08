"""
Extract the tourism tables used in this project from the published PDFs into tidy CSVs.

Each table has its own rule for blank cells (WFP-style "-" or an empty cell shifts the numbers left), and
every table is checked against its own printed totals before it is saved.

Usage (from anywhere, after scripts/fetch_data.py):
    python scripts/extract_tables.py

Inputs (data/raw/pdf/)
  mtwa_statistical_abstract_2025.pdf   Ministry of Tourism, Wildlife and Antiquities, Statistical Abstract 2025 (2020–2024)
  ubos_statistical_abstract_2017.pdf   Uganda Bureau of Statistics, Statistical Abstract 2017 (2012–2016)
  ubos_statistical_abstract_2020.pdf   Uganda Bureau of Statistics, Statistical Abstract 2020 (2015–2019)

Outputs (data/processed/)
  parks_annual.csv          visits by national park and wildlife reserve, 2012–2024
  parks_monthly.csv         visits to all national parks by month, 2015–2024
  parks_category.csv        visits by category of visitor, 2016 and 2020–2024
  arrivals_purpose.csv      tourist arrivals by purpose of visit, 2012–2016 and 2020–2024
  arrivals_monthly.csv      tourist arrivals by month, 2020–2024
  arrivals_country.csv      tourist arrivals by country of residence, 2020–2024 (main countries)
  arrivals_region.csv       tourist arrivals by region of residence, 2020–2024 (checked against the total)
  overseas_markets.csv      top 10 overseas source markets, 2023 and 2024
  gorilla_permits.csv       gorilla tracking permits available and sold by month, 2020–2024
  chimp_permits.csv         chimpanzee tracking permits available and sold by quarter, 2020–2024
  hotel_occupancy.csv       hotel room occupancy by month (2020–2024) and by region
"""
import re
from pathlib import Path
import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
PDF, PROC = ROOT / 'data' / 'raw' / 'pdf', ROOT / 'data' / 'processed'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']
NUM = r'\(?-?[\d,]+(?:\.\d+)?%?\)?|-'


def pages(name):
    with pdfplumber.open(PDF / name) as pdf:
        return [(p.extract_text() or '') for p in pdf.pages]


def block(texts, title, span=2):
    """Text from a table title to its 'Source' line, joining the next page when the table runs over.
    Skips contents-page entries (titles followed by dot leaders)."""
    for i, t in enumerate(texts):
        j = t.find(title)
        if j < 0 or re.search(re.escape(title) + r'[^\n]*(?:\.\s?){4,}', t):
            continue
        seg = '\n'.join(texts[i:i + span])[j:]
        k = seg.find('\nSource')          # the source line, not the word in a title
        return seg[:k] if k > 0 else seg
    raise SystemExit(f'table not found: {title}')


def row(line):
    """Split a table line into its label and the numbers that follow it ('-' becomes None)."""
    m = re.match(r'^(.*?)((?:\s+(?:' + NUM + r'))+)\s*$', ' ' + line.strip())   # numbers are space-separated
    if not m:
        return line.strip(), []
    vals = []
    for t in re.findall(NUM, m.group(2)):
        if not re.search(r'\d', t):        # '-' or a bare bracket: a blank cell
            vals.append(None)
            continue
        neg = t.startswith('(') or t.startswith('-')
        v = float(t.strip('()%-').replace(',', ''))
        vals.append(-v if neg else v)
    return m.group(1).strip(), vals


def grab(text, labels, n, align='left'):
    """Values for each expected label. `n` values are taken; when a row has fewer numbers than the table
    has columns, `align` says where the blanks are ('right' = missing leading years)."""
    out = {}
    for line in text.splitlines():
        lab, vals = row(line)
        for L in labels:
            if lab.lower().replace(' ', '') == L.lower().replace(' ', '') and L not in out:
                out[L] = vals
    missing = [L for L in labels if L not in out]
    if missing:
        raise SystemExit(f'rows not found: {missing}')
    return out


def check(df, total, cols, name, tol=0.006):
    s = df[cols].sum()
    bad = [(c, s[c], total[c]) for c in cols if total[c] and abs(s[c] - total[c]) > tol * total[c] + 2]
    if bad:
        raise SystemExit(f'{name}: column sums do not match printed totals: {bad}')
    print(f'{name}: OK ({len(df)} rows, totals match)')


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    m25, u17, u20 = pages('mtwa_statistical_abstract_2025.pdf'), pages('ubos_statistical_abstract_2017.pdf'), \
        pages('ubos_statistical_abstract_2020.pdf')
    Y12, Y15, Y20 = list(range(2012, 2017)), list(range(2015, 2020)), list(range(2020, 2025))

    # ---------------------------------------------------------------- parks by park
    def parks(text, years, labels, src):
        g = grab(text, labels + ['Total'], len(years))
        d = pd.DataFrame({L: g[L][:len(years)] for L in labels}, index=years).T
        check(d, dict(zip(years, g['Total'][:len(years)])), years, f'parks {src}')
        return d.reset_index(names='park').melt(id_vars='park', var_name='year', value_name='visits').assign(source=src)
    p12 = parks(block(u17, 'Table 3.6 O:'), Y12, ['Queen Elizabeth', 'Murchison Falls', 'Lake Mburo', 'Bwindi Impenetrable',
                'Kibaale', 'Semliki', 'Mgahinga Gorilla', 'Kidepo Valley', 'Rwenzori Mountains', 'Mount Elgon', 'Toro Semliki'], 'UBOS 2017')
    p15 = parks(block(u20, 'Tables 3.8 6:'), Y15, ['Murchison Falls', 'Queen Elizabeth', 'Bwindi Impenetrable', 'Lake Mburo',
                'Semliki', 'Kibaale', 'Kidepo Valley', 'Mgahinga Gorilla', 'Rwenzori Mountains', 'Mount Elgon', 'Toro Semliki'], 'UBOS 2020')
    p20 = parks(block(m25, 'Table 18:'), Y20, ['Murchison Falls National Park', 'Queen Elizabeth National Park',
                'Lake Mburo National Park', 'Bwindi Impenetrable National Park', 'Semliki National Park', 'Kibale National Park',
                'Kidepo Valley National Park', 'Mgahinga Gorilla National Park', 'Rwenzori Mountains National Park',
                'Mount Elgon National Park', 'Pian Upe Wildlife Reserve', 'Katonga-Wildlife Reserve',
                'Toro Semliki Wildlife Reserve'], 'MTWA 2025')
    p20['park'] = p20['park'].str.replace(' National Park', '').str.replace('-Wildlife', ' Wildlife')
    pa = pd.concat([p12, p15, p20])
    pa['park'] = pa['park'].replace({'Kibaale': 'Kibale', 'Toro Semliki': 'Toro Semliki Wildlife Reserve'})
    # Overlapping years (2015–2016) must agree between the two UBOS editions
    ov = pa[pa['year'].isin([2015, 2016])].pivot_table(index=['park', 'year'], columns='source', values='visits')
    if (ov['UBOS 2017'] - ov['UBOS 2020']).abs().max() > 0:
        raise SystemExit('UBOS 2017 and 2020 editions disagree on 2015–2016 park visits')
    pa = pa.sort_values('source').drop_duplicates(['park', 'year'], keep='last')
    pa.sort_values(['year', 'park']).to_csv(PROC / 'parks_annual.csv', index=False)

    # ---------------------------------------------------------------- parks by month
    t = block(u20, 'Table 3.6 J:')
    rows = []
    for line in t.splitlines():
        lab, v = row(line)
        if re.fullmatch(r'20\d\d', lab or '') is None and len(v) == 14 and 2014 < v[0] < 2020:
            lab, v = str(int(v[0])), v[1:]
        if re.fullmatch(r'201[5-9]', lab) and len(v) == 13:
            if abs(sum(v[:12]) - v[12]) > 2:
                raise SystemExit(f'monthly parks {lab}: months do not add up')
            rows += [{'year': int(lab), 'month': m + 1, 'visits': v[m]} for m in range(12)]
    t = block(m25, 'Table 48:')
    g = grab(t, MONTHS + ['Total'], 5)
    for m, M in enumerate(MONTHS):
        vals = g[M]
        if len(vals) == 6:          # a blank 2020 cell is printed as '-', so rows are complete
            raise SystemExit(f'unexpected row length for {M}')
        rows += [{'year': y, 'month': m + 1, 'visits': vals[i] or 0} for i, y in enumerate(Y20)]
    pm = pd.DataFrame(rows)
    tot = pm[pm['year'] >= 2020].groupby('year')['visits'].sum()
    if any(abs(tot[y] - g['Total'][i]) > 2 for i, y in enumerate(Y20)):
        raise SystemExit(f'monthly parks 2020–2024 do not add to totals: {tot.tolist()} vs {g["Total"][:5]}')
    ann = pa.groupby('year')['visits'].sum()
    for y, v in pm.groupby('year')['visits'].sum().items():
        if abs(v - ann[y]) > 2:
            raise SystemExit(f'monthly and annual park totals differ in {y}: {v} vs {ann[y]}')
    print(f'parks monthly: OK ({len(pm)} months, match annual totals)')
    pm.to_csv(PROC / 'parks_monthly.csv', index=False)

    # ---------------------------------------------------------------- park visitors by category
    cats = ['Foreign Non Residents', 'Foreign Residents', 'East African Residents', 'Students', 'Others']
    g = grab(block(m25, 'Table 47:'), cats + ['Overall'], 5)
    pc = pd.DataFrame({c: g[c][:5] for c in cats}, index=Y20).T
    check(pc, dict(zip(Y20, g['Overall'][:5])), Y20, 'park visitor categories')
    t16 = block(u17, 'Table 3.6 P:')
    tot16 = [v for lab, v in map(row, t16.splitlines()) if lab == 'Total'][0]
    c16 = pd.DataFrame({2016: dict(zip(['Foreign Non Residents', 'Foreign Residents', 'East African Residents',
                                         'Students', 'Others'], tot16[:5]))})
    pc = pd.concat([c16, pc], axis=1).reset_index(names='category').melt(id_vars='category', var_name='year', value_name='visits')
    pc.to_csv(PROC / 'parks_category.csv', index=False)
    print('park visitor categories 2016: Foreign non-residents', tot16[0], 'of', tot16[5])

    # ---------------------------------------------------------------- arrivals by purpose
    g = grab(block(u17, 'Table 3.8.4:'), ['Leisure, recreation and holidays', 'Business and professional conferences',
             'Visiting friends and relatives', 'Others*', 'Total'], 5)
    a12 = pd.DataFrame({'Leisure and holiday': g['Leisure, recreation and holidays'][:5],
                        'Business and professional': g['Business and professional conferences'][:5],
                        'Visiting friends and relatives': g['Visiting friends and relatives'][:5],
                        'Other': g['Others*'][:5]}, index=Y12) * 1000
    if (a12.sum(axis=1) - pd.Series(g['Total'][:5], index=Y12) * 1000).abs().max() > 2000:
        raise SystemExit('arrivals by purpose 2012–2016 do not add up')
    g = grab(block(m25, 'Table 32:'), ['Business & Professional', 'Leisure & Holiday', 'Others',
             'Visiting Friends and Relatives', 'TOTAL'], 5)
    a20 = pd.DataFrame({'Leisure and holiday': g['Leisure & Holiday'][:5], 'Business and professional': g['Business & Professional'][:5],
                        'Visiting friends and relatives': g['Visiting Friends and Relatives'][:5], 'Other': g['Others'][:5]}, index=Y20)
    check(a20.T, dict(zip(Y20, g['TOTAL'][:5])), Y20, 'arrivals by purpose 2020–2024')
    ap = pd.concat([a12.assign(source='UBOS 2017 (arrival cards)'), a20.assign(source='MTWA 2025 (PISCES immigration system)')])
    ap.reset_index(names='year').to_csv(PROC / 'arrivals_purpose.csv', index=False)

    # ---------------------------------------------------------------- arrivals by month
    g = grab(block(m25, 'Table 33:'), MONTHS + ['TOTAL'], 5)
    am = pd.DataFrame([{'year': y, 'month': m + 1, 'arrivals': g[M][i]} for m, M in enumerate(MONTHS) for i, y in enumerate(Y20)])
    tot = am.groupby('year')['arrivals'].sum()
    if any(abs(tot[y] - g['TOTAL'][i]) > 2 for i, y in enumerate(Y20)):
        raise SystemExit('monthly arrivals do not add to totals')
    print('arrivals monthly: OK')
    am.to_csv(PROC / 'arrivals_monthly.csv', index=False)

    # ---------------------------------------------------------------- arrivals by country of residence
    t = block(m25, 'Table 34:', span=6)
    rows = []
    for line in t.splitlines():
        lab, v = row(line)
        if not lab or lab.isupper() or len(v) < 4 or lab.startswith(('Region', '2024')):
            continue
        vals = v[:-2]                          # drop the share and % change columns
        vals = [None] * (5 - len(vals)) + vals  # blanks are the earliest years
        rows.append({'country': lab, **dict(zip(Y20, vals[-5:]))})
    ac = pd.DataFrame(rows).drop_duplicates('country')
    ac.to_csv(PROC / 'arrivals_country.csv', index=False)   # main countries; small 'other' rows are incomplete

    # Regions: the top-level regions add up exactly to the printed total, so checks run at this level
    regions = ['AFRICA', 'EAST AFRICA', 'AMERICAS', 'EAST ASIA AND THE PACIFIC', 'EUROPE', 'MIDDLE EAST', 'SOUTH ASIA',
               'NOT SPECIFIED', 'TOTAL']
    g = grab(t, regions, 5)
    ar = pd.DataFrame({r_: g[r_][:5] for r_ in regions}, index=Y20)
    top = ['AFRICA', 'AMERICAS', 'EAST ASIA AND THE PACIFIC', 'EUROPE', 'MIDDLE EAST', 'SOUTH ASIA', 'NOT SPECIFIED']
    if (ar[top].sum(axis=1) - ar['TOTAL']).abs().max() > 0.001 * ar['TOTAL'].max():
        raise SystemExit(f'arrivals by region do not add up: {ar[top].sum(axis=1).tolist()} vs {ar["TOTAL"].tolist()}')
    print('arrivals by region: OK (regions add up to the printed total)')
    ar.reset_index(names='year').to_csv(PROC / 'arrivals_region.csv', index=False)

    # Top 10 overseas markets, 2023 and 2024 (Table 3)
    t3 = block(m25, 'Table 3:')
    rows = []
    for line in t3.splitlines():
        m = re.match(r'^(\d+) (.+?) ([\d,]+) ([\d.]+) (\d+) (.+?) ([\d,]+) ([\d.]+)$', line.strip())
        if m:
            rows += [{'year': 2023, 'rank': int(m[1]), 'market': m[2], 'arrivals': int(m[3].replace(',', ''))},
                     {'year': 2024, 'rank': int(m[5]), 'market': m[6], 'arrivals': int(m[7].replace(',', ''))}]
    if len(rows) != 20:
        raise SystemExit(f'top overseas markets: parsed {len(rows)} entries, expected 20')
    pd.DataFrame(rows).to_csv(PROC / 'overseas_markets.csv', index=False)
    print('top overseas markets: OK')
    top = ac.set_index('country')[2024].sort_values(ascending=False)
    print(f'arrivals by country: {len(ac)} countries; top 2024:', top.head(5).astype(int).to_dict())

    # ---------------------------------------------------------------- gorilla and chimp permits
    def permits(avail_title, sold_title, labels, name, span=2):
        a = grab(block(m25, avail_title, span), labels + ['Total'], 5)
        st = block(m25, sold_title, span)
        has_total = any(row(l)[0] == 'Total' for l in st.splitlines())   # the chimp sold table prints no total
        s = grab(st, labels + (['Total'] if has_total else []), 5)
        rows = []
        for L in labels:
            av = a[L][:5]
            sv = s[L][:-2]                              # drop share and % change
            sv = [None] * (5 - len(sv)) + sv            # a blank is a month with none sold (2020 lockdown)
            rows += [{'period': L, 'year': y, 'available': av[i], 'sold': sv[i] if sv[i] is not None else 0}
                     for i, y in enumerate(Y20)]
        d = pd.DataFrame(rows)
        for col, src in [('available', a)] + ([('sold', s)] if has_total else []):
            tot = d.groupby('year')[col].sum()
            if any(abs(tot[y] - src['Total'][i]) > 2 for i, y in enumerate(Y20)):
                raise SystemExit(f'{name} {col}: {tot.tolist()} vs printed {src["Total"][:5]}')
        print(f'{name}: OK (' + ('available and sold match printed totals' if has_total else 'available matches printed totals; sold has no total') + ')')
        return d
    permits('Table 57:', 'Table 58:', MONTHS, 'gorilla permits').to_csv(PROC / 'gorilla_permits.csv', index=False)
    permits('Table 59:', 'Table 60:', ['Jan-Mar (Q3)', 'Apr-Jun (Q4)', 'Jul-Sept (Q1)', 'Oct-Dec (Q2)'],
            'chimp permits').to_csv(PROC / 'chimp_permits.csv', index=False)

    # ---------------------------------------------------------------- hotel occupancy
    short = [m[:3] for m in MONTHS]
    g = grab(block(m25, 'Table 39:'), short + ['Overall'], 5)
    rows = []
    for m, M in enumerate(short):
        v = g[M]
        vals = v[:5] if len(v) == 6 else v[:4] + [None]     # 2024 runs to September only
        rows += [{'scope': 'national', 'year': y, 'month': m + 1, 'occupancy': vals[i]} for i, y in enumerate(Y20)]
    g = grab(block(m25, 'Table 41:'), ['Central', 'Eastern', 'Kampala', 'Northern', 'Western'], 5)
    for r_, v in g.items():
        rows += [{'scope': r_, 'year': y, 'month': None, 'occupancy': v[i]} for i, y in enumerate(Y20)]
    pd.DataFrame(rows).to_csv(PROC / 'hotel_occupancy.csv', index=False)
    print('hotel occupancy: saved (2024 runs to September)')


if __name__ == '__main__':
    main()
