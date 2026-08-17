# AirLens — assignment note

Use this with the running app in a viva. It describes what the program actually does.

## 1. What the project is

AirLens is a desktop dashboard for the **Data Visualization using Python** course. It reads daily air-quality records for Indian cities and lets you explore them in five screens: Overview, City explorer, Comparison, Trends, and Map.

It is a local Python program, not a website. There is no login, no database, and no machine learning.

## 2. How to run it

Python 3.10 or newer.

```text
pip install -r requirements.txt
python app.py
```

On this PC, if `python` is the wrong interpreter, use `py app.py`.

Keep `data/city_day.csv` next to the code (the app also looks beside `app.py` if the file is still in the old place). The window opens maximised. Charts grow if you resize the window.

## 3. Stack (what to say if asked “which libraries?”)

| Library | Job in this project |
| --- | --- |
| **Pandas** | Load the CSV, parse dates, group by city and month, fill missing pollutant values |
| **NumPy** | Numeric work (means, argmax for the worst month, z-scores for the heatmap) |
| **Matplotlib** | Draw the charts inside the window |
| **Seaborn** | Bar chart and heatmap styling |
| **FreeSimpleGUI** | Window, sidebar, buttons, city dropdown |

`urllib` from the Python standard library is used only for the optional live reading. No extra package and no API key.

## 4. Data

**Historical file:** `data/city_day.csv`

This copy has about **13,152 rows**, **12 cities**, from **1 Jan 2018 to 31 Dec 2020**. Columns used: City, Date, PM2.5, PM10, NO2, SO2, CO, O3, AQI, AQI_Bucket.

Cleaning:

1. Column names are normalised if they differ only by case/spaces.
2. Date becomes a real datetime. AQI is forced to numbers; blank AQI rows are dropped.
3. Missing pollutant cells are filled with **that city’s median**, then 0 if a city has no readings at all.

The charts and the big average AQI number all come from this file. That is the assignment dataset.

**Live reading (optional):** Open-Meteo Air Quality API  
`https://air-quality-api.open-meteo.com/v1/air-quality`  
No sign-up. The sidebar line **Now · city · EAQI … · PM2.5 …** is current CAMS-based air quality for that city’s coordinates. **EAQI is the European AQI, not CPCB AQI.** Do not mix it with the 2018–2020 CPCB-style numbers in the charts. If the PC is offline, the dashboard still runs; the Now line says Open-Meteo is unreachable. **Refresh live** fetches again.

## 5. What each screen shows

**Overview**  
National average AQI from the CSV (large number) plus most polluted / cleanest cities. Donut = share of days in each AQI category. Histogram = how AQI values are spread.

**City explorer**  
Pick a city. The large number is the **last day in the CSV** for that city (end of 2020 in this file), not the live API. Left chart: average PM2.5, PM10, NO2, SO2, CO, O3. Right chart: monthly average AQI. Units: µg/m³ except CO in the CSV which is mg/m³.

**Comparison**  
Left: top 10 cities by average AQI (worst at the top). Colour follows the CPCB band of that average. Right: heatmap of cities vs pollutants. Each pollutant is **z-scored** (standardised) so CO is not crushed by PM10. A high cell means that city is high *for that pollutant*, not a raw µg/m³.

**Trends**  
Monthly average AQI, a 3-month rolling average, and the worst month marked. The large number is that worst-month average.

**Map**  
Cities plotted by longitude/latitude, coloured by mean CSV AQI. Click anywhere on the chart: a yellow glow + X marks the exact click (lon/lat), a card shows that point and the nearest city’s mean AQI / latest day, and a bright ring sits on that city. Clicks far from every city still keep the mark and coordinates. Clicking a bar on Comparison jumps here for that city.

## 6. AQI categories used on the historical charts

These are the usual CPCB bands applied to the CSV AQI column:

| Category | AQI |
| --- | --- |
| Good | 0–50 |
| Satisfactory | 51–100 |
| Moderate | 101–200 |
| Poor | 201–300 |
| Very Poor | 301–400 |
| Severe | above 400 |

## 7. Program flow (one paragraph)

`app.py` starts, finds `data/city_day.csv`, cleans it, and opens a maximised window. Sidebar buttons switch the five views. Matplotlib figures are drawn onto a Tk canvas; when the window size changes enough, the current figure is redrawn to fit. City explorer, Trends, and Map take the selected city from the dropdown. Clicking the map (or a Comparison bar) updates that city. Live Open-Meteo values are cached for about ten minutes so the API is not hit on every click.

## 8. Folder

```text
AirLens/
  app.py
  requirements.txt
  README.md
  REPORT.md
  data/city_day.csv
```

## 9. Honest limits

- The CSV is 2018–2020, not “today’s CPCB bulletin”.
- Live EAQI and CSV AQI are different scales. Say that if asked.
- Open-Meteo needs internet. The assignment still works without it.
- This is a visualisation tool, not a forecast and not a government product.
