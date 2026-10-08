# Uganda's Tourism: Who Comes, When, and What Goes Unsold

Who actually visits Uganda, how its visitor earnings have recovered against its peers, how national park visits have grown and who drives that growth, when visitors come, and how much of Uganda's most valuable product, gorilla tracking, goes unsold. Built from the Ministry of Tourism's and the Uganda Bureau of Statistics' published tables, UN Tourism data and the companion rainfall analysis.

**Read the report: [Uganda's tourism: who comes, when, and what goes unsold](https://tayeruta.github.io/uganda-tourism/reports/tourism_report.html)**

## Key findings

- **Most "tourists" are not on holiday.** In 2024, 19% of tourist arrivals (265,000 of 1.37 million) came for leisure; the rest came to visit friends and relatives, or for business, study or health. Nine in ten came from Africa, and Kenya and Rwanda alone sent 63%. About 137,000 (10%) came from outside Africa, led by India, the United States, China and the United Kingdom.
- **The arrival counts are not comparable over time.** Counting moved from arrival cards to the PISCES immigration system in 2019, and the published 2019 figures range from 657,000 to 1.54 million depending on source and definition.
- **National parks had a record 2024, built on domestic visitors.** Visits reached 437,000, 35% above 2019, but foreign non-resident visitors (160,000) were only 4% above their 2019 level; Ugandan students and East African residents drove the growth. Murchison Falls, Queen Elizabeth and Bwindi take two-thirds to three-quarters of all visits.
- **Visitors come in July and August**, which bring 29% of park visits; March brings 5%. The link to rainfall is weak (rank correlation −0.18 for park visits, −0.48 for gorilla bookings, neither significant); northern-hemisphere holidays may matter as much.
- **Gorilla capacity outgrew demand.** Permits rose 26% in 2024 but sales only 7%, so the share sold fell from 69% to 58%, leaving about 30,000 permits unsold, worth up to about US$24 million at the foreign non-resident price. 55% of the unsold permits fell in March–May and November.
- **Visitor earnings recovered more slowly than the neighbours'.** Travel receipts were 94% of their 2019 level in 2023, against 100% for Kenya, 123% for Rwanda and 130% for Tanzania (UN Tourism).
- **The 2026 low-season gorilla discount shows no clear effect yet.** With permits cut from US$800 to US$600 in April and May 2026 (as reported by tour operators; not yet in a published tariff), April–May sales grew about 4 points faster than January–March, the same gap as in 2025 without a discount. Sales would need to rise a third to keep permit revenue level; they ran about 4% above trend. The discount was announced five weeks before April, so this is an early read.
- **Park growth is uneven.** Since 2019, Semliki (+88%), Queen Elizabeth (+60%) and Murchison Falls (+34%) grew while Kidepo Valley (−40%), Rwenzori (−20%) and Mount Elgon (−62%) shrank. In January–June 2026 park visits fell 8%, entirely at Queen Elizabeth (−40%); the source gives no reason.

## Repository structure

```
├── data/
│   ├── raw/
│   │   ├── pdf/                     # source PDFs (not committed; see fetch_data.py)
│   │   ├── untourism/               # UN Tourism inbound arrivals and expenditure, all countries
│   │   └── rainfall_by_region.csv   # from the uganda-rainfall-analysis project
│   └── processed/                   # tables extracted from the PDFs, and notebook outputs
├── notebooks/
│   ├── 01_tourism.ipynb             # who comes, earnings, parks, seasonality, gorilla permits, shocks
│   └── 02_low_season_and_parks.ipynb  # the 2026 low-season discount test and park-by-park changes
├── reports/
│   └── tourism_report.html          # the write-up, published on GitHub Pages
├── scripts/
│   ├── fetch_data.py                # downloads every input
│   ├── extract_tables.py            # extracts the tables from the PDFs, checking each against its printed totals
│   ├── tourism.py                   # shared loading code
│   ├── build_notebooks.py           # generates the notebook from source
│   └── build_report_data.py         # injects the notebook's results into the report
└── requirements.txt
```

## Data and methods

- **Extraction.** Tables are read from the Ministry of Tourism's Statistical Abstract 2025 (2020–2024) and the Uganda Bureau of Statistics' Statistical Abstracts 2017 (2012–2016) and 2020 (2015–2019). Each has its own rule for blank cells, and every table is checked against its printed totals (and, for park visits, monthly against annual totals and the two UBOS editions against each other) before it is saved.
- **Benchmark.** UN Tourism inbound travel receipts from the balance of payments, 2015–2023, for Uganda and nine African peers. These include all visitor spending (students, patients, business travellers), so they measure the visitor economy rather than holiday tourism alone.
- **Seasonality.** Average monthly shares of the year, compared with Western Uganda's 1991–2020 rainfall (CHIRPS) by rank correlation.
- **Gorilla permits.** Permits available and sold by month; the unsold value is an upper bound at the US$800 foreign non-resident price in the Uganda Wildlife Authority's 2024–2026 tariff.
- **Discount test.** Growth in gorilla permit sales in the discounted months (April–May 2026) against the full-price months before them (January–March), compared with the same gap in 2025, a year without a discount. Uses the Ministry's January–June 2026 report, whose 2022–2024 figures agree exactly with the 2025 abstract.

## Reproducing the analysis

```bash
pip install -r requirements.txt
python scripts/fetch_data.py
python scripts/extract_tables.py
python scripts/build_notebooks.py
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
python scripts/build_report_data.py
```

## Data sources

| Dataset | Provider |
|---|---|
| [Statistical Abstract 2025 and Tourism Statistics January–June 2026](https://www.tourism.go.ug/publications) | Ministry of Tourism, Wildlife and Antiquities |
| [Statistical Abstracts 2017 and 2020](https://www.ubos.org/) | Uganda Bureau of Statistics |
| [Conservation tariff 2024–2026](https://www.tourism.go.ug/publications) | Uganda Wildlife Authority, via the Ministry of Tourism |
| [Inbound tourism data](https://www.untourism.int/tourism-statistics/tourism-data-inbound-tourism) | UN Tourism |
| [Regional rainfall](https://github.com/TayeRuta/uganda-rainfall-analysis) | CHIRPS, via the Uganda rainfall analysis |

## Limitations

- **Breaks in arrival counts.** Arrival counts change basis in 2019, and purpose of visit is not published for 2017–2019.
- **Short series.** Most series are annual and run 2012–2024 at best, so few formal tests are possible.
- **Hotel occupancy.** The hotel survey appears to cover mainly urban hotels and shows little seasonality.
- **Gorilla permits.** In July and August 2023, recorded sales exceed listed permits by up to a third in the source.
- **Earnings.** Travel receipts include non-holiday spending; the Ministry's 2024–2025 earnings are not yet in the comparable series.
- **Discount.** The 2026 discount is reported by tour operators but not yet in a published tariff, and only one partial season of data exists.

## Related projects

- [Uganda hospitality](https://github.com/TayeRuta/uganda-hospitality): hotel occupancy, value added, where the graded hotels are, and an audit of the statistics
- [Uganda agriculture synthesis](https://tayeruta.github.io/uganda-agriculture/): rainfall, food prices, coffee, irrigation and food trade
- [Uganda rainfall analysis](https://github.com/TayeRuta/uganda-rainfall-analysis): national, regional and Indian Ocean Dipole analysis

## License

Code is released under the MIT License. Data remain under the terms of their original providers.
