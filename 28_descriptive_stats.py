"""
28_descriptive_stats.py
=======================
Computes Table 2 (Descriptive Statistics) on the REGRESSION SAMPLE
- the same N = 21,741 rows that enter the main regression in 20_regression.py.

This script is intentionally standalone and only needs data/panel_data.csv.

Output:
  - Prints a Markdown-style table with Mean, Std, Min, Max, N for each variable.
  - Saves the same table to outputs/table2_descriptive_stats.csv.

The regression sample is defined as: all firm-week rows for which every regressor
that enters the main specification is non-missing. This matches the implicit
.dropna() inside 20_regression.py and ensures that Table 2 and Table 3 describe
exactly the same set of observations.

Notes on conventions:
  - Statistics are computed BEFORE 1%/99% winsorization, so the table shows
    the actual sample distribution (winsorization is an estimation choice, not
    a property of the data). If you prefer post-winsorization stats, set
    WINSORIZE = True below.
  - Log Amihud is computed as log(1 + Amihud * 1e9), same as in 20_regression.py.
"""

import os
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
DATA_PATH = "data/panel_data.csv"
OUT_DIR   = "outputs"
OUT_FILE  = "table2_descriptive_stats.csv"
WINSORIZE = False   # set True to report stats after 1%/99% winsorization

# Variables that go into the regression. Must match 20_regression.py exactly.
REGRESSORS = ["ret", "size", "bm", "log_amihud", "momentum", "leverage"]

# Display labels and formatting for the output table.
DISPLAY = [
    ("Return",            "ret",        4),
    ("Size (log assets)", "size",       2),
    ("Leverage",          "leverage",   3),
    ("Book-to-market",    "bm",         3),
    ("Momentum",          "momentum",   3),
    ("Log Amihud",        "log_amihud", 2),
]


def winsorize(s: pd.Series, lo: float = 0.01, hi: float = 0.99) -> pd.Series:
    """Symmetric percentile winsorization. Used only if WINSORIZE = True."""
    return s.clip(s.quantile(lo), s.quantile(hi))


def main() -> None:
    # 1. Load panel
    df = pd.read_csv(DATA_PATH, parse_dates=["begin"])

    # 2. Construct log Amihud the same way as the main regression script.
    df["log_amihud"] = np.log1p(df["amihud"] * 1e9)

    # 3. Restrict to the regression sample (drop rows with any missing regressor).
    reg = df.dropna(subset=REGRESSORS).copy()
    n_obs = len(reg)
    print(f"Regression sample: N = {n_obs:,} firm-week observations")
    print()

    # 4. Optional winsorization (off by default).
    if WINSORIZE:
        for c in REGRESSORS:
            reg[c] = winsorize(reg[c])

    # 5. Build the table.
    rows = []
    for label, col, _decimals in DISPLAY:
        s = reg[col]
        rows.append({
            "Variable":  label,
            "Mean":      s.mean(),
            "Std. Dev.": s.std(),
            "Min":       s.min(),
            "Max":       s.max(),
            "Obs.":      int(s.count()),
        })
    tbl = pd.DataFrame(rows)

    # 6. Pretty-print to console (Markdown-friendly).
    header = f"{'Variable':<20}{'Mean':>10}{'Std. Dev.':>12}{'Min':>10}{'Max':>10}{'Obs.':>10}"
    print(header)
    print("-" * len(header))
    for r, (_, _, decimals) in zip(rows, DISPLAY):
        fmt = f".{decimals}f"
        print(
            f"{r['Variable']:<20}"
            f"{r['Mean']:>10{fmt}}"
            f"{r['Std. Dev.']:>12{fmt}}"
            f"{r['Min']:>10{fmt}}"
            f"{r['Max']:>10{fmt}}"
            f"{r['Obs.']:>10,}"
        )

    # 7. Persist to disk for the thesis appendix / reproducibility.
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_FILE)
    tbl.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()