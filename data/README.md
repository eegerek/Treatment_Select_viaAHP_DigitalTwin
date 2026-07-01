# Data

Two of these files are cached snapshots of public **World Bank** indicators for
Turkiye; the pipeline fetches them live from the World Bank API when it can and
only falls back to these copies when the network is unavailable.

| File | Series | Source |
|------|--------|--------|
| `wb_cpi_TUR.csv` | Inflation, consumer prices (annual %) | World Bank `FP.CPI.TOTL.ZG` |
| `wb_urban_TUR.csv` | Urban population (% of total) | World Bank `SP.URB.TOTL.IN.ZS` |
| `electricity_tariff_TR.csv` | Industrial electricity tariff (nominal TRY/kWh) | TUIK / EPDK-TEDAS anchors |

The electricity tariff has no clean public API, so it is bundled as a small set
of anchor points; update them as newer figures are published. To refresh the
World Bank snapshots, hit the URLs noted in each CSV header and paste the
`date,value` pairs back in (or just let the live fetch run).
