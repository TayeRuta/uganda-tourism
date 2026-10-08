"""
Shared loading code for the tourism project. Used by the notebook and build_report_data.py.

Tables extracted from the PDFs by extract_tables.py live in data/processed/; UN Tourism files and regional
rainfall are read from data/raw/.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, PROC = ROOT / 'data' / 'raw', ROOT / 'data' / 'processed'
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Foreign non-resident visitors to national parks in 2018 and 2019. The UBOS 2020 abstract gives these only as
# labels on Figure 3.8.5; the text confirms them ("foreign non-residents constituted ... 48 percent ... in 2019").
PARK_FOREIGN_2018_2019 = {2018: 150931, 2019: 153911}

# Gorilla tracking permit, Uganda Wildlife Authority conservation tariff 2024–2026 (US$ per permit)
GORILLA_PERMIT_USD = {'Foreign non-resident': 800, 'Foreign resident': 700, 'Rest of Africa': 500}

PEERS = {'Uganda': 'Uganda', 'Kenya': 'Kenya', 'United Republic of Tanzania': 'Tanzania', 'Rwanda': 'Rwanda',
         'Ethiopia': 'Ethiopia', 'Zambia': 'Zambia', 'Botswana': 'Botswana', 'Namibia': 'Namibia',
         'South Africa': 'South Africa', 'Zimbabwe': 'Zimbabwe'}
EAST_AFRICA = ['Uganda', 'Kenya', 'Tanzania', 'Rwanda', 'Ethiopia']


def load_parks_annual():
    return pd.read_csv(PROC / 'parks_annual.csv')


def load_parks_monthly():
    d = pd.read_csv(PROC / 'parks_monthly.csv')
    d['date'] = pd.to_datetime(dict(year=d['year'], month=d['month'], day=1))
    return d


def load_parks_category():
    d = pd.read_csv(PROC / 'parks_category.csv')
    extra = pd.DataFrame([{'category': 'Foreign Non Residents', 'year': y, 'visits': v} for y, v in PARK_FOREIGN_2018_2019.items()])
    return pd.concat([d, extra]).sort_values(['category', 'year'])


def load_arrivals_purpose():
    return pd.read_csv(PROC / 'arrivals_purpose.csv')


def load_arrivals_monthly():
    d = pd.read_csv(PROC / 'arrivals_monthly.csv')
    d['date'] = pd.to_datetime(dict(year=d['year'], month=d['month'], day=1))
    return d


def load_arrivals_country():
    d = pd.read_csv(PROC / 'arrivals_country.csv').set_index('country')
    d.columns = d.columns.astype(int)
    return d


def load_arrivals_region():
    return pd.read_csv(PROC / 'arrivals_region.csv').set_index('year')


def load_overseas_markets():
    return pd.read_csv(PROC / 'overseas_markets.csv')


def load_gorilla():
    d = pd.read_csv(PROC / 'gorilla_permits.csv')
    d['month'] = d['period'].map({m: i + 1 for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July',
                                                                 'August', 'September', 'October', 'November', 'December'])})
    d['utilisation'] = d['sold'] / d['available']
    return d


def load_chimp():
    d = pd.read_csv(PROC / 'chimp_permits.csv')
    d['utilisation'] = d['sold'] / d['available']
    return d


def load_hotels():
    return pd.read_csv(PROC / 'hotel_occupancy.csv')


def load_untourism(kind):
    """UN Tourism indicators for Uganda and its peers, as a year × country table.
    kind: 'arrivals' (overnight visitors, thousands), 'business' / 'personal' (arrivals by purpose, thousands),
          'travel' (inbound travel receipts, balance of payments, US$ million), 'total_exp' (travel + passenger transport)."""
    files = {'arrivals': ('UN_Tourism_inbound_arrivals_09_2026.xlsx', 'inbound - trips - total - total - overnight visitors (tourists)'),
             'business': ('UN_Tourism_inbound_arrivals_by_purpose_12_2025.xlsx', 'inbound - trips - by purpose - business - overnight visitors (tourists)'),
             'personal': ('UN_Tourism_inbound_arrivals_by_purpose_12_2025.xlsx', 'inbound - trips - by purpose - personal - overnight visitors (tourists)'),
             'travel': ('UN_Tourism_inbound_expenditure_12_2025.xlsx', 'inbound - expenditure - balance of payments - travel - visitors'),
             'total_exp': ('UN_Tourism_inbound_expenditure_12_2025.xlsx', 'inbound - expenditure - balance of payments - total - visitors')}
    f, label = files[kind]
    d = pd.read_excel(RAW / 'untourism' / f, sheet_name='Data')
    d = d[(d['indicator_label'] == label) & (d['partner_area_label'] == 'World') & d['reporter_area_label'].isin(PEERS)]
    return d.assign(country=d['reporter_area_label'].map(PEERS)).pivot_table(index='year', columns='country', values='value')


def load_rainfall(region):
    """Monthly rainfall climatology (mm, 1991–2020) for a region of the rainfall project, e.g. 'Western'."""
    r = pd.read_csv(RAW / 'rainfall_by_region.csv')
    r = r[r['region'].str.startswith(region) & r['year'].between(1991, 2020)]
    return r.groupby('month')['rainfall_mm'].mean()
