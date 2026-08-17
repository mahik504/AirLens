import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

FONT_UI = "Segoe UI"
FONT_DISPLAY = "Bahnschrift"
FONT_MONO = "Consolas"

COLOR_BG = "#16110c"
COLOR_SURFACE = "#241c14"
COLOR_HAIRLINE = "#6a5340"
COLOR_TEXT = "#f1e4d0"
COLOR_MUTED = "#b89a7a"
COLOR_ACCENT = "#c45c26"

AQI_COLORS = {
    "Good": "#6b7f3a",
    "Satisfactory": "#a3a03a",
    "Moderate": "#c4922a",
    "Poor": "#c45c26",
    "Very Poor": "#9a2f1f",
    "Severe": "#5c1410",
}

POLLUTANT_COLORS = ["#7a6238", "#9a7840", "#c4922a", "#c45c26", "#9a2f1f", "#5c4a38"]
POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
CITY_COORDS = {
    "Ahmedabad": (23.0225, 72.5714),
    "Amritsar": (31.6340, 74.8723),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Lucknow": (26.8467, 80.9462),
    "Mumbai": (19.0760, 72.8777),
    "Patna": (25.5941, 85.1376),
    "Visakhapatnam": (17.6868, 83.2185),
}
_LIVE_CACHE = {}
_LIVE_TTL = 600.0
HEAT_CMAP = LinearSegmentedColormap.from_list(
    "airlens_heat", ["#3a2a18", "#c4922a", "#c45c26", "#5c1410"]
)

plt.rcParams["font.family"] = [FONT_DISPLAY, FONT_UI]
sns.set_theme(style="ticks")

sg.LOOK_AND_FEEL_TABLE["AirLensDesk"] = {
    "BACKGROUND": COLOR_BG,
    "TEXT": COLOR_TEXT,
    "INPUT": COLOR_SURFACE,
    "TEXT_INPUT": COLOR_TEXT,
    "SCROLL": COLOR_SURFACE,
    "BUTTON": (COLOR_TEXT, COLOR_BG),
    "PROGRESS": (COLOR_ACCENT, COLOR_SURFACE),
    "BORDER": 0,
    "SLIDER_DEPTH": 0,
    "PROGRESS_DEPTH": 0,
}
sg.theme("AirLensDesk")


def get_aqi_bucket(aqi_value):
    if pd.isna(aqi_value):
        return "Unknown"
    val = float(aqi_value)
    if val <= 50:
        return "Good"
    elif val <= 100:
        return "Satisfactory"
    elif val <= 200:
        return "Moderate"
    elif val <= 300:
        return "Poor"
    elif val <= 400:
        return "Very Poor"
    else:
        return "Severe"


def get_bucket_color(bucket_name):
    return AQI_COLORS.get(str(bucket_name).strip(), COLOR_MUTED)


def default_csv_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "city_day.csv")


def fetch_live_air(city, force=False):
    now = time.time()
    cached = _LIVE_CACHE.get(city)
    if not force and cached and now - cached["ts"] < _LIVE_TTL:
        return cached["data"]

    coords = CITY_COORDS.get(city)
    if not coords:
        return None

    lat, lon = coords
    query = urllib.parse.urlencode({
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "current": "european_aqi,pm2_5",
        "timezone": "Asia/Kolkata",
    })
    url = "https://air-quality-api.open-meteo.com/v1/air-quality?" + query
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AirLens-college-assignment"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        current = payload.get("current") or {}
        data = {
            "time": current.get("time"),
            "european_aqi": current.get("european_aqi"),
            "PM2.5": current.get("pm2_5"),
        }
        _LIVE_CACHE[city] = {"ts": now, "data": data}
        return data
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


def format_live_line(city, live):
    if not live:
        return f"Now · {city} · Open-Meteo unreachable"
    eaqi = live.get("european_aqi")
    pm25 = live.get("PM2.5")
    when = live.get("time") or ""
    eaqi_txt = "—" if eaqi is None else str(int(eaqi))
    pm_txt = "—" if pm25 is None else f"{float(pm25):.0f}"
    clock = when.replace("T", " ") if when else ""
    extra = f" · {clock}" if clock else ""
    return f"Now · {city} · EAQI {eaqi_txt} · PM2.5 {pm_txt} µg/m³{extra}"


def generate_fallback_data():
    np.random.seed(42)
    cities = ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai"]
    city_bases = {
        "Delhi": (240, 110, 200, 45, 18, 1.6, 35),
        "Mumbai": (120, 50, 90, 30, 14, 0.9, 28),
        "Bengaluru": (80, 30, 55, 20, 8, 0.6, 25),
        "Kolkata": (145, 60, 115, 32, 12, 0.8, 30),
        "Chennai": (95, 38, 70, 22, 9, 0.65, 26)
    }
    dates = pd.date_range(end=pd.Timestamp.today(), periods=60, freq="D")
    records = []

    for city in cities:
        base_aqi, p25, p10, no2, so2, co, o3 = city_bases[city]
        for d in dates:
            noise = np.random.normal(0, 10)
            aqi = max(25, int(base_aqi + noise))
            ratio = aqi / base_aqi
            records.append({
                "City": city,
                "Date": d,
                "PM2.5": max(5.0, round(p25 * ratio + np.random.normal(0, 3), 2)),
                "PM10": max(10.0, round(p10 * ratio + np.random.normal(0, 5), 2)),
                "NO2": max(2.0, round(no2 + np.random.normal(0, 2), 2)),
                "SO2": max(1.0, round(so2 + np.random.normal(0, 1), 2)),
                "CO": max(0.1, round(co * ratio + np.random.normal(0, 0.05), 2)),
                "O3": max(5.0, round(o3 + np.random.normal(0, 2), 2)),
                "AQI": aqi,
                "AQI_Bucket": get_aqi_bucket(aqi)
            })

    return pd.DataFrame(records), True


def clean_data(df):
    col_mapping = {}
    standard_cols = ["City", "Date", "PM2.5", "PM10", "NO", "NO2", "NOx", "NH3",
                     "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene", "AQI", "AQI_Bucket"]

    current_cols = {str(c).strip().lower(): c for c in df.columns}
    for scol in standard_cols:
        low = scol.lower()
        if low in current_cols:
            col_mapping[current_cols[low]] = scol

    df = df.rename(columns=col_mapping)

    if "City" not in df.columns:
        df["City"] = "Unknown City"
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    else:
        df["Date"] = pd.date_range(end=pd.Timestamp.today(), periods=len(df), freq="D")

    if "AQI" in df.columns:
        df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")
        df = df.dropna(subset=["AQI"]).copy()
    else:
        df["AQI"] = 100.0

    if "AQI_Bucket" not in df.columns or df["AQI_Bucket"].isnull().all():
        df["AQI_Bucket"] = df["AQI"].apply(get_aqi_bucket)
    else:
        df["AQI_Bucket"] = df["AQI_Bucket"].fillna(df["AQI"].apply(get_aqi_bucket))

    for col in POLLUTANTS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan
        if "City" in df.columns:
            df[col] = df.groupby("City")[col].transform(lambda s: s.fillna(s.median()))
        df[col] = df[col].fillna(0.0)

    return df.sort_values("Date").reset_index(drop=True)


def load_data(filepath=None):
    if filepath is None:
        filepath = default_csv_path()

    is_demo = False
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            df = clean_data(df)
            if len(df) == 0:
                df, is_demo = generate_fallback_data()
        except Exception:
            df, is_demo = generate_fallback_data()
    else:
        df, is_demo = generate_fallback_data()

    return df, is_demo


def canvas_wh(canvas):
    if canvas is None:
        return 1100, 460
    try:
        w = int(canvas.winfo_width())
        h = int(canvas.winfo_height())
    except Exception:
        return 1100, 460
    if w < 80 or h < 80:
        return 1100, 460
    return w, h


def new_figure(canvas, ncols=1):
    w, h = canvas_wh(canvas)
    fig_w = max(w / 100.0, 6.5)
    fig_h = max(h / 100.0, 3.4)
    if ncols == 1:
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100, constrained_layout=True)
        return fig, ax
    fig, axes = plt.subplots(1, ncols, figsize=(fig_w, fig_h), dpi=100, constrained_layout=True)
    return fig, axes


def style_axes(fig, ax):
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_SURFACE)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    ax.xaxis.label.set_color(COLOR_TEXT)
    ax.yaxis.label.set_color(COLOR_TEXT)
    ax.title.set_color(COLOR_MUTED)
    for spine in ax.spines.values():
        spine.set_color(COLOR_HAIRLINE)
        spine.set_linewidth(0.8)
    ax.grid(True, linestyle="-", alpha=0.18, color=COLOR_HAIRLINE)


def style_legend(leg):
    if not leg:
        return
    leg.get_frame().set_facecolor(COLOR_SURFACE)
    leg.get_frame().set_edgecolor(COLOR_HAIRLINE)
    for text in leg.get_texts():
        text.set_color(COLOR_TEXT)


def plot_empty(canvas, message):
    fig, ax = new_figure(canvas, 1)
    style_axes(fig, ax)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_facecolor(COLOR_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=13, color=COLOR_MUTED, transform=ax.transAxes)
    return fig


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    widget = figure_canvas_agg.get_tk_widget()
    widget.configure(background=COLOR_BG, highlightthickness=0)
    widget.pack(side="top", fill="both", expand=1)
    return figure_canvas_agg


def delete_figure_agg(figure_agg):
    if not figure_agg:
        return
    try:
        figure_agg.get_tk_widget().destroy()
    except Exception:
        pass
    try:
        plt.close(figure_agg.figure)
    except Exception:
        plt.close("all")


def monthly_aqi(df, city):
    city_df = df[df["City"] == city].dropna(subset=["Date"]).copy()
    if city_df.empty:
        return pd.DataFrame(columns=["YearMonth", "AQI", "DateStr"])
    city_df["YearMonth"] = city_df["Date"].dt.to_period("M")
    monthly = city_df.groupby("YearMonth", as_index=False)["AQI"].mean()
    monthly["DateStr"] = monthly["YearMonth"].astype(str)
    return monthly


def draw_monthly_line(ax, monthly_agg, show_peak=False, rolling=False):
    x = list(range(len(monthly_agg)))
    y = monthly_agg["AQI"].to_numpy()
    ax.plot(x, y, color=COLOR_ACCENT, linewidth=2.2, marker="o", markersize=3.2, label="Monthly average")
    ax.fill_between(x, y, color=COLOR_ACCENT, alpha=0.16)
    if rolling and len(y) >= 2:
        roll = monthly_agg["AQI"].rolling(3, min_periods=1).mean().to_numpy()
        ax.plot(x, roll, color=COLOR_MUTED, linewidth=1.8, linestyle="--", label="3-month average")
    if show_peak and len(y):
        max_idx = int(np.argmax(y))
        max_val = y[max_idx]
        max_label = monthly_agg["DateStr"].iloc[max_idx]
        ax.scatter([max_idx], [max_val], color=AQI_COLORS["Very Poor"], s=78, zorder=5, label="Worst month")
        ax.annotate(
            f"Peak {max_val:.0f}\n{max_label}",
            (max_idx, max_val),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_TEXT,
            bbox=dict(boxstyle="round,pad=0.28", fc="#3a1810", ec=AQI_COLORS["Very Poor"], lw=1.0),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color=AQI_COLORS["Very Poor"], lw=1.0)
        )
    ax.axhline(100, color=AQI_COLORS["Satisfactory"], linestyle=":", alpha=0.5, label="Satisfactory (100)")
    ax.axhline(200, color=AQI_COLORS["Moderate"], linestyle=":", alpha=0.5, label="Moderate (200)")
    step = max(1, len(monthly_agg) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(monthly_agg["DateStr"].iloc[::step], rotation=30, ha="right")
    ax.set_xlabel("Year-month")
    ax.set_ylabel("Average AQI")
    ax.set_ylim(0, max(float(y.max()) * 1.28, 250) if len(y) else 250)
    style_legend(ax.legend(loc="upper right", fontsize=8))


def plot_overview(df, canvas):
    if df.empty:
        return plot_empty(canvas, "No records to chart")

    fig, (ax_pie, ax_hist) = new_figure(canvas, 2)
    style_axes(fig, ax_pie)
    style_axes(fig, ax_hist)
    ax_pie.grid(False)
    ax_pie.set_facecolor(COLOR_BG)

    bucket_order = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    bucket_counts = df["AQI_Bucket"].value_counts()
    labels = [b for b in bucket_order if b in bucket_counts.index and bucket_counts[b] > 0]
    sizes = [bucket_counts[b] for b in labels]
    colors = [get_bucket_color(b) for b in labels]

    if sizes:
        wedges, texts, autotexts = ax_pie.pie(
            sizes,
            labels=None,
            colors=colors,
            autopct="%1.0f%%",
            startangle=140,
            pctdistance=0.72,
            wedgeprops=dict(width=0.46, edgecolor=COLOR_BG, linewidth=3),
            textprops=dict(color=COLOR_TEXT, fontsize=9)
        )
        for at in autotexts:
            at.set_color(COLOR_TEXT)
        ax_pie.axis("equal")
        ax_pie.set_title("AQI categories")
        style_legend(ax_pie.legend(wedges, labels, loc="lower center", fontsize=8, ncol=2, bbox_to_anchor=(0.5, -0.08)))
    else:
        ax_pie.text(0.5, 0.5, "No AQI categories", ha="center", va="center", color=COLOR_MUTED, transform=ax_pie.transAxes)

    ax_hist.hist(df["AQI"].dropna(), bins=28, color=COLOR_ACCENT, edgecolor=COLOR_BG, linewidth=0.6)
    for lo, hi, name in [(0, 50, "Good"), (50, 100, "Satisfactory"), (100, 200, "Moderate"),
                         (200, 300, "Poor"), (300, 400, "Very Poor"), (400, 500, "Severe")]:
        ax_hist.axvspan(lo, hi, color=get_bucket_color(name), alpha=0.10)
    ax_hist.set_title("AQI values")
    ax_hist.set_xlabel("AQI")
    ax_hist.set_ylabel("Days")
    return fig


def plot_city_explorer(df, city, canvas):
    city_df = df[df["City"] == city]
    if city_df.empty:
        return plot_empty(canvas, f"No data for {city}")

    fig, (ax_bar, ax_line) = new_figure(canvas, 2)
    style_axes(fig, ax_bar)
    style_axes(fig, ax_line)

    available = [p for p in POLLUTANTS if p in city_df.columns]
    means = [round(city_df[p].mean(), 2) for p in available]
    if not available or all(pd.isna(m) for m in means):
        ax_bar.text(0.5, 0.5, f"No pollutant readings for {city}", ha="center", va="center",
                    color=COLOR_MUTED, transform=ax_bar.transAxes)
    else:
        pollutant_df = pd.DataFrame({"Pollutant": available, "Concentration": means})
        sns.barplot(
            data=pollutant_df,
            x="Pollutant",
            y="Concentration",
            hue="Pollutant",
            legend=False,
            palette=POLLUTANT_COLORS[:len(available)],
            ax=ax_bar,
            edgecolor=COLOR_BG,
            linewidth=1.0
        )
        for p in ax_bar.patches:
            val = p.get_height()
            if val > 0:
                ax_bar.annotate(
                    f"{val:.1f}",
                    (p.get_x() + p.get_width() / 2.0, val),
                    ha="center", va="bottom",
                    fontsize=9, fontweight="bold",
                    color=COLOR_TEXT,
                    xytext=(0, 3),
                    textcoords="offset points"
                )
        ax_bar.set_xlabel("")
        ax_bar.set_ylabel("Mean (µg/m³; CO in mg/m³)")
        ax_bar.set_title("Pollutants")
        ax_bar.set_ylim(0, max(means) * 1.18)

    monthly = monthly_aqi(df, city)
    if monthly.empty:
        ax_line.text(0.5, 0.5, f"No monthly AQI for {city}", ha="center", va="center",
                     color=COLOR_MUTED, transform=ax_line.transAxes)
        ax_line.set_xticks([])
        ax_line.set_yticks([])
    else:
        draw_monthly_line(ax_line, monthly, show_peak=False, rolling=False)
        ax_line.set_title("Monthly AQI")
    return fig


def plot_comparison(df, canvas):
    if df.empty:
        return plot_empty(canvas, "No cities to rank")

    fig, (ax_bar, ax_heat) = new_figure(canvas, 2)
    style_axes(fig, ax_bar)
    style_axes(fig, ax_heat)

    city_ranking = df.groupby("City")["AQI"].mean()
    n_cities = len(city_ranking)
    city_ranking = city_ranking.nlargest(10).sort_values(ascending=True)
    colors = [get_bucket_color(get_aqi_bucket(val)) for val in city_ranking.values]
    bars = ax_bar.barh(city_ranking.index, city_ranking.values, color=colors, edgecolor=COLOR_BG, height=0.62)
    for bar in bars:
        w = bar.get_width()
        ax_bar.text(w + 3, bar.get_y() + bar.get_height() / 2, f"{w:.1f}",
                    ha="left", va="center", fontsize=8, fontweight="bold", color=COLOR_TEXT)
    ax_bar.set_title(f"Top 10 of {n_cities} by average AQI")
    ax_bar.set_xlabel("Average AQI")
    ax_bar.set_xlim(0, city_ranking.max() * 1.22)
    fig._bar_cities = list(city_ranking.index)
    fig._bar_ax = ax_bar

    cols = [p for p in POLLUTANTS if p in df.columns]
    if cols:
        means = df.groupby("City")[cols].mean()
        std = means.std(ddof=0).replace(0, np.nan)
        z = (means - means.mean()) / std
        z = z.replace([np.inf, -np.inf], 0).fillna(0)
        sns.heatmap(
            z,
            ax=ax_heat,
            cmap=HEAT_CMAP,
            annot=True,
            fmt=".1f",
            linewidths=0.4,
            linecolor=COLOR_BG,
            cbar_kws={"label": "z-score"},
            annot_kws={"color": COLOR_TEXT, "size": 7}
        )
        ax_heat.set_title("Cities vs pollutants (scaled)")
        ax_heat.set_xlabel("")
        ax_heat.set_ylabel("")
        ax_heat.tick_params(colors=COLOR_MUTED, labelsize=8)
        ax_heat.collections[0].colorbar.ax.yaxis.label.set_color(COLOR_MUTED)
        ax_heat.collections[0].colorbar.ax.tick_params(colors=COLOR_MUTED)
    else:
        ax_heat.text(0.5, 0.5, "No pollutant columns", ha="center", va="center",
                     color=COLOR_MUTED, transform=ax_heat.transAxes)
    return fig


def plot_trends(df, city, canvas):
    monthly_agg = monthly_aqi(df, city)
    if monthly_agg.empty:
        return plot_empty(canvas, f"No monthly AQI data for {city}")

    fig, ax = new_figure(canvas, 1)
    style_axes(fig, ax)
    draw_monthly_line(ax, monthly_agg, show_peak=True, rolling=True)
    ax.set_title(f"Monthly AQI · {city}")
    return fig


def nearest_city(lon, lat, max_deg=3.0):
    best = None
    best_d = 1e9
    for city, (clat, clon) in CITY_COORDS.items():
        d = ((clon - lon) ** 2 + (clat - lat) ** 2) ** 0.5
        if d < best_d:
            best = city
            best_d = d
    if best_d > max_deg:
        return None
    return best


def plot_map(df, canvas, selected=None, click_pt=None):
    fig, ax = new_figure(canvas, 1)
    style_axes(fig, ax)
    avgs = df.groupby("City")["AQI"].mean() if not df.empty else pd.Series(dtype=float)
    xs, ys, colors, names = [], [], [], []
    for city, (lat, lon) in CITY_COORDS.items():
        if city not in avgs.index:
            continue
        xs.append(lon)
        ys.append(lat)
        colors.append(get_bucket_color(get_aqi_bucket(avgs[city])))
        names.append(city)
    if xs:
        ax.scatter(xs, ys, c=colors, s=110, zorder=3, edgecolors=COLOR_BG, linewidths=0.9)
        for x, y, name in zip(xs, ys, names):
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(8, 6), fontsize=8, color=COLOR_TEXT)
    if selected and selected in CITY_COORDS:
        lat, lon = CITY_COORDS[selected]
        ax.scatter([lon], [lat], s=420, facecolors="#f2d08a", edgecolors="none", alpha=0.18, zorder=2)
        ax.scatter([lon], [lat], s=280, facecolors="none", edgecolors="#fff4c8", linewidths=2.6, zorder=4)
    if click_pt is not None:
        cx, cy = click_pt
        ax.scatter([cx], [cy], s=520, c="#f2d08a", alpha=0.32, zorder=4, linewidths=0)
        ax.scatter([cx], [cy], s=140, c="#fff4c8", marker="x", linewidths=2.4, zorder=6)
        hit = nearest_city(cx, cy)
        if hit and hit in CITY_COORDS:
            hlat, hlon = CITY_COORDS[hit]
            ax.plot([cx, hlon], [cy, hlat], color="#f2d08a", lw=1.1, ls=":", zorder=4, alpha=0.85)
        if hit and hit in avgs.index:
            mean_aqi = float(avgs[hit])
            bucket = get_aqi_bucket(mean_aqi)
            latest = city_latest_row(df, hit)
            latest_txt = ""
            if latest is not None and pd.notna(latest.get("Date")):
                latest_txt = f"\nLatest {latest['Date'].strftime('%d %b %Y')}  {float(latest['AQI']):.0f}"
            box = f"{hit}\n{cx:.2f}°E   {cy:.2f}°N\nMean AQI {mean_aqi:.0f}  {bucket}{latest_txt}"
        else:
            box = f"{cx:.2f}°E   {cy:.2f}°N\nNo city nearby"
        ha = "left" if cx < 83 else "right"
        ax.annotate(
            box,
            (cx, cy),
            textcoords="offset points",
            xytext=(16, 16) if ha == "left" else (-16, 16),
            fontsize=8,
            color=COLOR_TEXT,
            ha=ha,
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": COLOR_SURFACE,
                "edgecolor": "#f2d08a",
                "linewidth": 1.15,
            },
            zorder=7,
        )
    ax.set_xlim(68, 98)
    ax.set_ylim(6, 37)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Click the map · yellow mark is your click")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color=COLOR_HAIRLINE, alpha=0.28, linewidth=0.6)
    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=col, markeredgecolor=COLOR_BG,
                    markersize=8, label=name)
        for name, col in AQI_COLORS.items()
    ]
    leg = ax.legend(
        handles=handles,
        loc="lower left",
        fontsize=7,
        frameon=True,
        title="Mean AQI",
        title_fontsize=7,
        labelcolor=COLOR_TEXT,
        facecolor=COLOR_SURFACE,
        edgecolor=COLOR_HAIRLINE,
        borderpad=0.6,
    )
    if leg is not None:
        leg.get_title().set_color(COLOR_MUTED)
        for txt in leg.get_texts():
            txt.set_color(COLOR_TEXT)
    return fig


def city_latest_row(df, city):
    city_df = df[df["City"] == city]
    if city_df.empty:
        return None
    return city_df.loc[city_df["Date"].idxmax()]


def nav_button(label, key, active=False):
    colors = (COLOR_TEXT, COLOR_ACCENT) if active else (COLOR_MUTED, COLOR_BG)
    return sg.Button(
        label,
        key=key,
        size=(20, 2),
        button_color=colors,
        font=(FONT_UI, 13),
        border_width=0,
        pad=((12, 12), (5, 5))
    )


def main():
    df, is_demo = load_data()
    if is_demo:
        sg.popup(
            "data/city_day.csv was missing or could not be read.\nShowing demo data so the dashboard still runs.",
            title="AirLens",
            font=(FONT_UI, 10)
        )

    cities = sorted(df["City"].dropna().unique().tolist())
    latest_date = df["Date"].max().strftime("%b %d, %Y") if not df.empty else "N/A"

    total_records = len(df)
    total_cities = df["City"].nunique()
    overall_avg_aqi = round(df["AQI"].mean(), 1) if not df.empty else 0
    overall_bucket = get_aqi_bucket(overall_avg_aqi)
    bucket_color = get_bucket_color(overall_bucket)

    city_avg = df.groupby("City")["AQI"].mean()
    most_polluted = city_avg.idxmax() if not city_avg.empty else "N/A"
    most_polluted_val = round(city_avg.max(), 1) if not city_avg.empty else 0
    cleanest = city_avg.idxmin() if not city_avg.empty else "N/A"
    cleanest_val = round(city_avg.min(), 1) if not city_avg.empty else 0

    stamp = "DEMO" if is_demo else "CSV"
    stamp_color = AQI_COLORS["Moderate"] if is_demo else AQI_COLORS["Good"]
    default_city = cities[0] if cities else "Delhi"
    aqi_display = f"{overall_avg_aqi:.0f}" if float(overall_avg_aqi).is_integer() else str(overall_avg_aqi)

    sidebar_col = [
        [sg.Text("AirLens", font=(FONT_DISPLAY, 26), text_color=COLOR_TEXT, background_color=COLOR_BG, pad=((14, 14), (22, 4)))],
        [sg.Text("India air quality", font=(FONT_UI, 11), text_color=COLOR_MUTED, background_color=COLOR_BG, pad=((14, 14), (0, 20)))],
        [nav_button("  01    Overview", "-NAV-OVERVIEW-", active=True)],
        [nav_button("  02    City explorer", "-NAV-EXPLORER-")],
        [nav_button("  03    Comparison", "-NAV-COMPARE-")],
        [nav_button("  04    Trends", "-NAV-TRENDS-")],
        [nav_button("  05    Map", "-NAV-MAP-")],
        [sg.VPush(background_color=COLOR_BG)],
        [sg.Text(stamp, font=(FONT_DISPLAY, 14), text_color=stamp_color, background_color=COLOR_BG, pad=((14, 14), (0, 2)))],
        [sg.Text(f"{total_records:,} rows", font=(FONT_MONO, 10), text_color=COLOR_MUTED, background_color=COLOR_BG, pad=((14, 14), (0, 8)))],
        [sg.Text("Now · checking Open-Meteo…", font=(FONT_UI, 9), text_color=COLOR_MUTED, background_color=COLOR_BG, key="-NOW-LINE-", pad=((14, 14), (0, 8)))],
        [sg.Button("Refresh live", key="-LIVE-REFRESH-", size=(16, 1), button_color=(COLOR_TEXT, COLOR_SURFACE), font=(FONT_UI, 10), border_width=0, pad=((14, 14), (0, 18)))],
    ]

    hero_col = [
        [sg.Text("Average AQI", font=(FONT_UI, 9), text_color=COLOR_MUTED, background_color=COLOR_BG)],
        [sg.Text(aqi_display, font=(FONT_DISPLAY, 64), text_color=bucket_color, background_color=COLOR_BG)],
        [sg.Text(overall_bucket, font=(FONT_DISPLAY, 16), text_color=bucket_color, background_color=COLOR_BG, pad=((0, 0), (4, 10)))],
        [sg.Text(
            f"{total_cities} cities    ·    {total_records:,} days    ·    through {latest_date}",
            font=(FONT_UI, 9), text_color=COLOR_MUTED, background_color=COLOR_BG
        )],
    ]

    pair_col = [
        [sg.Text("Most polluted", font=(FONT_UI, 9), text_color=COLOR_MUTED, background_color=COLOR_BG)],
        [sg.Text(most_polluted, font=(FONT_DISPLAY, 18), text_color=COLOR_TEXT, background_color=COLOR_BG)],
        [sg.Text(str(most_polluted_val), font=(FONT_MONO, 14), text_color=AQI_COLORS["Very Poor"], background_color=COLOR_BG, pad=((0, 0), (0, 18)))],
        [sg.Text("Cleanest", font=(FONT_UI, 9), text_color=COLOR_MUTED, background_color=COLOR_BG)],
        [sg.Text(cleanest, font=(FONT_DISPLAY, 18), text_color=COLOR_TEXT, background_color=COLOR_BG)],
        [sg.Text(str(cleanest_val), font=(FONT_MONO, 14), text_color=AQI_COLORS["Good"], background_color=COLOR_BG)],
    ]

    kpi_frame = [[
        sg.Column(hero_col, background_color=COLOR_BG, pad=(0, 0)),
        sg.Push(),
        sg.Column(pair_col, background_color=COLOR_BG, pad=((32, 8), (18, 0))),
    ]]

    city_controls = [
        [
            sg.Text("City", font=(FONT_UI, 9), text_color=COLOR_MUTED, key="-CITY-LBL-", visible=False, background_color=COLOR_BG),
            sg.Combo(
                cities, default_value=default_city, key="-CITY-COMBO-", enable_events=True,
                font=(FONT_UI, 10), size=(18, 1), readonly=True, visible=False,
                background_color=COLOR_SURFACE, text_color=COLOR_TEXT, button_arrow_color=COLOR_ACCENT
            ),
        ],
        [
            sg.Text("", font=(FONT_DISPLAY, 28), key="-CITY-HERO-NAME-", visible=False, text_color=COLOR_TEXT, background_color=COLOR_BG),
            sg.Push(),
            sg.Text("", font=(FONT_DISPLAY, 48), key="-CITY-HERO-AQI-", visible=False, text_color=COLOR_TEXT, background_color=COLOR_BG),
            sg.Text("", font=(FONT_DISPLAY, 14), key="-CITY-HERO-BUCKET-", visible=False, text_color=COLOR_MUTED, background_color=COLOR_BG, pad=((12, 0), (18, 0))),
        ],
        [sg.Text("", font=(FONT_UI, 9), key="-CITY-STATS-", visible=False, text_color=COLOR_MUTED, background_color=COLOR_BG)],
    ]

    main_col = [
        [
            sg.Text("Overview", font=(FONT_DISPLAY, 16), key="-HEADER-TITLE-", text_color=COLOR_MUTED, background_color=COLOR_BG),
            sg.Push(),
            sg.Text(latest_date, font=(FONT_MONO, 9), text_color=COLOR_MUTED, background_color=COLOR_BG)
        ],
        [sg.HSeparator(color=COLOR_HAIRLINE, pad=((0, 0), (6, 14)))],
        [sg.Column(kpi_frame, key="-KPI-ROW-", background_color=COLOR_BG, pad=(0, 0), expand_x=True)],
        [sg.Column(city_controls, key="-CITY-ROW-", background_color=COLOR_BG, pad=((0, 0), (0, 8)), expand_x=True)],
        [sg.Canvas(key="-CANVAS-", background_color=COLOR_BG, expand_x=True, expand_y=True)]
    ]

    layout = [[
        sg.Column(sidebar_col, background_color=COLOR_BG, size=(268, None), expand_y=True, pad=((0, 20), (0, 0))),
        sg.Column(main_col, background_color=COLOR_BG, expand_x=True, expand_y=True, pad=(0, 0)),
    ]]

    window = sg.Window(
        "AirLens",
        layout,
        finalize=True,
        resizable=True,
        margins=(20, 18),
        background_color=COLOR_BG
    )

    window["-CANVAS-"].expand(True, True)
    window.maximize()
    window.refresh()
    try:
        window["-CANVAS-"].Widget.update_idletasks()
    except Exception:
        pass

    canvas = window["-CANVAS-"].TKCanvas
    current_screen = "overview"
    current_fig_agg = None
    last_canvas_size = (0, 0)
    last_resize_at = 0.0
    map_click = [None, None]

    def selected_city():
        city = window["-CITY-COMBO-"].get()
        return city if city else default_city

    def live_city():
        if current_screen in ("explorer", "trends", "map"):
            return selected_city()
        if "Delhi" in cities:
            return "Delhi"
        return default_city

    def figure_for_screen():
        if current_screen == "overview":
            return plot_overview(df, canvas)
        if current_screen == "explorer":
            return plot_city_explorer(df, selected_city(), canvas)
        if current_screen == "compare":
            return plot_comparison(df, canvas)
        if current_screen == "map":
            click = None if map_click[0] is None else (map_click[0], map_click[1])
            return plot_map(df, canvas, selected_city(), click)
        return plot_trends(df, selected_city(), canvas)

    def on_chart_click(event):
        if event.inaxes is None or event.xdata is None or event.button != 1:
            return
        if current_screen == "compare":
            bar_ax = getattr(getattr(current_fig_agg, "figure", None), "_bar_ax", None)
            if event.inaxes is not bar_ax:
                return
        window.write_event_value("-CHART-CLICK-", (float(event.xdata), float(event.ydata)))

    def redraw():
        nonlocal current_fig_agg, last_canvas_size
        delete_figure_agg(current_fig_agg)
        current_fig_agg = draw_figure(canvas, figure_for_screen())
        if current_screen in ("map", "compare"):
            current_fig_agg.mpl_connect("button_press_event", on_chart_click)
        last_canvas_size = canvas_wh(canvas)

    def update_nav_buttons(active_key):
        for k in ("-NAV-OVERVIEW-", "-NAV-EXPLORER-", "-NAV-COMPARE-", "-NAV-TRENDS-", "-NAV-MAP-"):
            if k == active_key:
                window[k].update(button_color=(COLOR_TEXT, COLOR_ACCENT))
            else:
                window[k].update(button_color=(COLOR_MUTED, COLOR_BG))

    def refresh_live_line(force=False):
        city = live_city()
        live = fetch_live_air(city, force=force)
        window["-NOW-LINE-"].update(format_live_line(city, live))

    def set_city_controls(show):
        for k in ("-CITY-LBL-", "-CITY-COMBO-", "-CITY-HERO-NAME-", "-CITY-HERO-AQI-", "-CITY-HERO-BUCKET-", "-CITY-STATS-"):
            window[k].update(visible=show)

    def refresh_explorer_chrome(city):
        city_df = df[df["City"] == city]
        latest = city_latest_row(df, city)
        if city_df.empty or latest is None:
            window["-CITY-HERO-NAME-"].update(city, visible=True)
            window["-CITY-HERO-AQI-"].update("—", visible=True)
            window["-CITY-HERO-BUCKET-"].update("No data", visible=True)
            window["-CITY-STATS-"].update("", visible=True)
            return

        current_aqi = round(float(latest["AQI"]), 1)
        bucket = get_aqi_bucket(current_aqi)
        avg_aqi = round(city_df["AQI"].mean(), 1)
        max_aqi = round(city_df["AQI"].max(), 1)
        min_aqi = round(city_df["AQI"].min(), 1)
        latest_str = latest["Date"].strftime("%b %d, %Y") if pd.notna(latest["Date"]) else "N/A"
        aqi_txt = f"{current_aqi:.0f}" if float(current_aqi).is_integer() else str(current_aqi)
        window["-CITY-HERO-NAME-"].update(city, visible=True)
        window["-CITY-HERO-AQI-"].update(aqi_txt, text_color=get_bucket_color(bucket), visible=True)
        window["-CITY-HERO-BUCKET-"].update(bucket, text_color=get_bucket_color(bucket), visible=True)
        window["-CITY-STATS-"].update(
            f"Latest {latest_str}    ·    avg {avg_aqi}    ·    range {min_aqi}–{max_aqi}    ·    {len(city_df):,} days",
            visible=True
        )

    def refresh_trends_chrome(city):
        monthly = monthly_aqi(df, city)
        window["-CITY-HERO-NAME-"].update(city, visible=True)
        if monthly.empty:
            window["-CITY-HERO-AQI-"].update("—", visible=True)
            window["-CITY-HERO-BUCKET-"].update("No months", visible=True)
            window["-CITY-STATS-"].update("No monthly data for this city", visible=True)
            return
        peak = monthly.loc[monthly["AQI"].idxmax()]
        window["-CITY-HERO-AQI-"].update(f"{peak['AQI']:.0f}", text_color=COLOR_ACCENT, visible=True)
        window["-CITY-HERO-BUCKET-"].update(str(peak["DateStr"]), text_color=COLOR_ACCENT, visible=True)
        window["-CITY-STATS-"].update("Worst month · monthly average AQI", visible=True)

    def show_screen(screen, title, need_city):
        nonlocal current_screen
        current_screen = screen
        nav = {
            "overview": "-NAV-OVERVIEW-",
            "explorer": "-NAV-EXPLORER-",
            "compare": "-NAV-COMPARE-",
            "trends": "-NAV-TRENDS-",
            "map": "-NAV-MAP-",
        }
        update_nav_buttons(nav[screen])
        window["-HEADER-TITLE-"].update(title)
        window["-KPI-ROW-"].update(visible=(screen == "overview"))
        set_city_controls(need_city)
        city = selected_city()
        if screen in ("explorer", "map"):
            refresh_explorer_chrome(city)
        elif screen == "trends":
            refresh_trends_chrome(city)
        redraw()
        refresh_live_line()

    window.bind("<Configure>", "-RESIZE-")
    redraw()
    refresh_live_line()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == "-RESIZE-":
            w, h = canvas_wh(canvas)
            if abs(w - last_canvas_size[0]) < 24 and abs(h - last_canvas_size[1]) < 24:
                continue
            now = time.monotonic()
            if now - last_resize_at < 0.18:
                continue
            last_resize_at = now
            redraw()
            continue

        if event == "-NAV-OVERVIEW-":
            show_screen("overview", "Overview", False)
        elif event == "-NAV-EXPLORER-":
            show_screen("explorer", "City explorer", True)
        elif event == "-NAV-COMPARE-":
            show_screen("compare", "Comparison", False)
        elif event == "-NAV-TRENDS-":
            show_screen("trends", "Trends", True)
        elif event == "-NAV-MAP-":
            show_screen("map", "Map", True)
        elif event == "-CITY-COMBO-":
            city = selected_city()
            if current_screen == "explorer":
                refresh_explorer_chrome(city)
                redraw()
            elif current_screen == "trends":
                refresh_trends_chrome(city)
                redraw()
            elif current_screen == "map":
                map_click[0] = None
                map_click[1] = None
                window["-HEADER-TITLE-"].update("Map")
                refresh_explorer_chrome(city)
                redraw()
            refresh_live_line()
        elif event == "-CHART-CLICK-":
            x, y = values["-CHART-CLICK-"]
            if current_screen == "map":
                map_click[0] = x
                map_click[1] = y
                city = nearest_city(x, y)
                if city:
                    window["-CITY-COMBO-"].update(city)
                    refresh_explorer_chrome(city)
                    window["-HEADER-TITLE-"].update(f"Map · {city} · {x:.2f}°E, {y:.2f}°N")
                else:
                    window["-HEADER-TITLE-"].update(f"Map · {x:.2f}°E, {y:.2f}°N")
                redraw()
                refresh_live_line()
            elif current_screen == "compare" and current_fig_agg is not None:
                names = getattr(current_fig_agg.figure, "_bar_cities", None)
                if names:
                    idx = int(round(y))
                    if 0 <= idx < len(names):
                        city = names[idx]
                        window["-CITY-COMBO-"].update(city)
                        map_click[0] = CITY_COORDS[city][1] if city in CITY_COORDS else None
                        map_click[1] = CITY_COORDS[city][0] if city in CITY_COORDS else None
                        show_screen("map", f"Map · {city}", True)
        elif event == "-LIVE-REFRESH-":
            refresh_live_line(force=True)

    delete_figure_agg(current_fig_agg)
    window.close()


if __name__ == "__main__":
    main()
