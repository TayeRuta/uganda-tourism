"""
Download every input for the tourism project.

Usage (from anywhere):
    python scripts/fetch_data.py
    python scripts/extract_tables.py

Outputs
  data/raw/pdf/            Ministry of Tourism Statistical Abstract 2025 and January–June 2026 performance report;
                           Uganda Bureau of Statistics Statistical Abstracts 2017 and 2020; Uganda Wildlife
                           Authority conservation tariff 2024–2026 (not committed: re-downloaded here)
  data/raw/untourism/      UN Tourism inbound arrivals, arrivals by purpose and inbound expenditure, all countries
  data/raw/rainfall_by_region.csv   monthly regional rainfall, from the uganda-rainfall-analysis project
"""
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
import certifi

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
SSL = ssl.create_default_context(cafile=certifi.where())
MTWA = 'https://www.tourism.go.ug/wp-content/uploads/publications/'
PDFS = {
    'mtwa_statistical_abstract_2025.pdf': MTWA + 'statistical-abstract-2025-full.pdf',
    'mtwa_performance_jan_jun_2026.pdf': MTWA + 'statistics-performance-report-jan-june-2026.pdf',
    'uwa_conservation_tariff_2024_2026.pdf': MTWA + 'uwa-conservation-tariff-2024-2026.pdf',
    'ubos_statistical_abstract_2017.pdf': 'https://www.ubos.org/wp-content/uploads/publications/03_20182017_Statistical_Abstract.pdf',
    'ubos_statistical_abstract_2020.pdf': 'https://library.health.go.ug/sites/default/files/resources/UBOS%20Statistical%20Abstract%202020.pdf',
}
UNT = 'https://pre-webunwto.s3.eu-west-1.amazonaws.com/s3fs-public/'
UN_TOURISM = ['2026-09/UN_Tourism_inbound_arrivals_09_2026.xlsx', '2025-12/UN_Tourism_inbound_arrivals_by_purpose_12_2025.xlsx',
              '2025-12/UN_Tourism_inbound_expenditure_12_2025.xlsx']
RAINFALL = 'https://raw.githubusercontent.com/TayeRuta/uganda-rainfall-analysis/main/data/raw/uganda_rainfall_by_region_1990_2025.csv'


def get(url, dest):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600, context=SSL) as r, open(dest, 'wb') as f:
            shutil.copyfileobj(r, f)
    except urllib.error.URLError as e:
        # ubos.org doesn't send its intermediate certificate; curl completes and verifies the chain
        if not isinstance(e.reason, ssl.SSLCertVerificationError):
            raise
        subprocess.run(['curl', '-sfL', '-A', 'Mozilla/5.0', '-o', str(dest), url], check=True)


def main():
    for d in ('pdf', 'untourism'):
        (RAW / d).mkdir(parents=True, exist_ok=True)
    for name, url in PDFS.items():
        get(url, RAW / 'pdf' / name)
        print('saved', name)
    for path in UN_TOURISM:
        get(UNT + path, RAW / 'untourism' / Path(path).name)
        print('saved', Path(path).name)
    get(RAINFALL, RAW / 'rainfall_by_region.csv')
    print('saved rainfall_by_region.csv')


if __name__ == '__main__':
    main()
