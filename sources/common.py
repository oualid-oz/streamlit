"""Helpers shared by the build_<cas>.py scripts: download, save, figure, summary.json."""

import gzip
import io
import json
import textwrap
from pathlib import Path

import kaleido
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "projets"
RENDER = Path(__file__).resolve().parent / "figures"  # aperçus PNG, non versionnés
SUMMARY = DATA / "summary.json"

# Okabe-Ito colour-blind safe palette
BLUE, ORANGE, GREEN, VERMILLION = "#0072B2", "#E69F00", "#009E73", "#D55E00"
COLORS = [BLUE, ORANGE, GREEN, VERMILLION]


def fr(n):
    """1234567 -> '1 234 567' (narrow no-break space), for figure titles."""
    return f"{n:,}".replace(",", " ")


def download(url, **params):
    """GET a URL and return the raw bytes (nothing is cached on disk)."""
    resp = requests.get(url, params=params, timeout=300)
    resp.raise_for_status()
    return resp.content


def read_csv(url, **kwargs):
    """Download a CSV (plain or .gz) and read it with pandas."""
    content = download(url)
    if content[:2] == b"\x1f\x8b":  # gzip magic number
        content = gzip.decompress(content)
    return pd.read_csv(io.BytesIO(content), **kwargs)


def save_parquet(df, name):
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / f"{name}.parquet"
    df.to_parquet(path, index=False)
    return path


def style(fig, title):
    fig.update_layout(
        title={
            "text": "<br>".join(textwrap.wrap(title, 62)),
            "font": {"size": 20},
            "x": 0.01,
            "xanchor": "left",
        },
        template="simple_white",
        font={"size": 18},
        colorway=COLORS,
        margin={"l": 80, "r": 30, "t": 145, "b": 70},
    )
    return fig


def save_figure(fig, name):
    """PNG 900x560 through kaleido (mathjax off: the CDN copy breaks plotly 7 + kaleido 1.5)."""
    RENDER.mkdir(parents=True, exist_ok=True)
    path = RENDER / f"{name}.png"
    kaleido.write_fig_sync(
        fig,
        path=path,
        opts={"format": "png", "width": 900, "height": 560, "scale": 2},
        kopts={"mathjax": False},
    )
    return path


def record(name, df, path, date_col, source_url, licence, figure_title, **extra):
    """Add (or replace) this case in data/projets/summary.json."""
    summary = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    dates = pd.to_datetime(df[date_col]) if date_col else None
    one_row = json.loads(df.head(1).to_json(orient="records", date_format="iso"))[0]
    summary[name] = dict(
        status="ok",
        rows=len(df),
        columns=list(df.columns),
        period=[str(dates.min())[:10], str(dates.max())[:10]] if date_col else None,
        size_mb=round(Path(path).stat().st_size / 1e6, 2),
        one_real_row=one_row,
        figure_title=figure_title,
        source_url=source_url,
        licence=licence,
        **extra,
    )
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2))


def record_skipped(name, reason, source_url=None):
    """Record a case that could not be built, with the reason."""
    DATA.mkdir(parents=True, exist_ok=True)
    summary = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    summary[name] = {"status": "skipped", "reason": reason, "source_url": source_url}
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
