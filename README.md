# AirLens

College **Data Visualization using Python** project. Five screens: Overview, City explorer, Comparison, Trends, Map. Lamp-black / rust desktop UI — course work, not the internship flagship.

Run **`app.py`**.

## Run

```text
pip install -r requirements.txt
python app.py
```

On Windows, if `python` is the wrong interpreter, use `py app.py`.

The window opens maximised. Charts follow the window size.

CSV path: `data/city_day.csv`.

If the CSV is missing, a popup warns you and a small demo table is used.

## Tabs

| Tab | Historical CSV | Extra |
| --- | --- | --- |
| Overview | Average AQI, most/least polluted cities, category donut, AQI histogram | Sidebar **Now** line is live Open-Meteo for Delhi |
| City explorer | Latest CSV day, pollutant bars, monthly AQI | **Now** line follows the selected city |
| Comparison | Top 10 AQI bars, z-scored city × pollutant heatmap | Click a bar to open Map for that city |
| Trends | Monthly AQI, 3-month average, worst month | **Now** line follows the selected city |
| Map | Cities sit on a 2D India outline (lon/lat). Click: yellow glow + X at the exact point, a card with lon/lat and that city’s CSV AQI | **Now** line follows the selected city |

**Refresh live** re-fetches Open-Meteo. No API key. Charts always use the CSV. Live **EAQI** is European AQI, not CPCB.

Teacher write-up: [REPORT.md](REPORT.md).

## Dataset

About 12 cities, 2018–2020. Columns: City, Date, PM2.5, PM10, NO2, SO2, CO, O3, AQI, AQI_Bucket.

Missing AQI rows are dropped. Pollutant gaps use that city’s median.

City explorer bars: µg/m³ except CO in the CSV (mg/m³).

## CPCB bands (CSV AQI only)

| Category | AQI |
| --- | --- |
| Good | 0–50 |
| Satisfactory | 51–100 |
| Moderate | 101–200 |
| Poor | 201–300 |
| Very Poor | 301–400 |
| Severe | above 400 |

## Stack

Python, FreeSimpleGUI, Pandas, NumPy, Matplotlib, Seaborn. Live air: Open-Meteo over `urllib` (stdlib).

## License

MIT. See [LICENSE](LICENSE). No live web demo — this is a desktop GUI.
