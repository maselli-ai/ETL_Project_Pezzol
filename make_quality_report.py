import os
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Cartelle e file di input (ordine cronologico GEN → AGO)

HERE = Path(__file__).resolve().parent
INPUT_DIR = (HERE / "dati_puliti").resolve()

INPUT_FILES = [
    INPUT_DIR / "cleaned_dataG.xlsx",          # GENNAIO
    INPUT_DIR / "cleaned_dataF.xlsx",          # FEBBRAIO
    INPUT_DIR / "Copia di cleaned_dataA.xlsx", # APRILE
    INPUT_DIR / "cleaned_dataM.xlsx",          # MAGGIO
    INPUT_DIR / "cleaned_dataGIU.xlsx",        # GIUGNO
    INPUT_DIR / "cleaned_dataL.xlsx",          # LUGLIO
    INPUT_DIR / "cleaned_dataAGO.xlsx",        # AGOSTO
]

OUT_DATASET    = "dataset_finale_ETL_QA.xlsx"
OUT_QA_SUMMARY = "QA_summary.csv"
OUT_HTML       = "data_quality_report.html"

MONTH_LABEL = {
    "cleaned_dataG.xlsx": "GENNAIO",
    "cleaned_dataF.xlsx": "FEBBRAIO",
    "Copia di cleaned_dataA.xlsx": "APRILE",
    "cleaned_dataM.xlsx": "MAGGIO",
    "cleaned_dataGIU.xlsx": "GIUGNO",
    "cleaned_dataL.xlsx": "LUGLIO",
    "cleaned_dataAGO.xlsx": "AGOSTO",
}
MONTH_ORDER = ["GENNAIO","FEBBRAIO","APRILE","MAGGIO","GIUGNO","LUGLIO","AGOSTO"]

# Funzioni di supporto

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower = {c.lower().strip(): c for c in df.columns}

    def pick(*cands):
        for c in cands:
            if c in lower:
                return lower[c]
        for key, orig in lower.items():
            if any(c in key for c in cands):
                return orig
        return None

    mapping = {
        "code":        pick("code", "codice", "item_code"),
        "description": pick("description", "descrizione"),
        "uom":         pick("um", "uom", "unit_of_measure", "unit measure", "unit_measure"),
        "stock":       pick("giacenza", "stock_quantity", "stock_level", "total_quantity", "total_stock"),
        "real":        pick("reale", "real", "real_stock", "actual_quantity"),
        "outgoing":    pick("scaricare", "to_download", "withdrawal_quantity", "ship_outgoing", "stock_scarico"),
    }

    out = pd.DataFrame(index=df.index)
    for new, old in mapping.items():
        out[new] = df[old] if (old is not None and old in df.columns) else np.nan
    return out

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def normalize_code(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
    return s.replace({"NAN": np.nan})

def normalize_uom(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.upper().str.strip()
    s = s.replace({"PAGINA": "KG", "PAGES": "KG", "": "KG", "NAN": "KG"}).fillna("KG")
    return s

def clamp_non_negative(s: pd.Series) -> pd.Series:
    s = to_num(s)
    return s.mask(s < 0, 0)

def metrics(df: pd.DataFrame, tag: str) -> dict:
    m = {f"{tag}_rows": len(df)}
    for col in ["stock", "real", "outgoing"]:
        if col in df.columns:
            s = to_num(df[col])
            m[f"{tag}_null_{col}"] = int(s.isna().sum())
            m[f"{tag}_neg_{col}"]  = int((s < 0).sum())
    if all(c in df.columns for c in ["code", "description", "mese_rif"]):
        m[f"{tag}_dups"] = int(df.duplicated(subset=["code", "description", "mese_rif"]).sum())
    return m

# Caricamento, standardizzazione e integrazione (ordine fissato)

frames = []
for path in INPUT_FILES:
    if not path.exists():
        raise SystemExit(f"File non trovato: {path}")
    df = pd.read_excel(path)
    std = standardize_columns(df)
    std["mese_rif"] = MONTH_LABEL[path.name]
    frames.append(std)
    print(f"File elaborato: {path.name} ({len(df)} righe)")

raw_integrated = pd.concat(frames, ignore_index=True)


# QA prima del cleaning
m_before = metrics(raw_integrated, "before")


# Cleaning
clean = raw_integrated.copy()

clean["code"] = normalize_code(clean["code"])
clean["uom"]  = normalize_uom(clean["uom"])

for col in ["stock", "real", "outgoing"]:
    clean[col] = clamp_non_negative(clean[col]).fillna(0)

clean = clean.drop_duplicates(subset=["code", "description", "mese_rif"])


# QA dopo il cleaning

m_after = metrics(clean, "after")

# Salvataggi

clean.to_excel(OUT_DATASET, index=False)

qa_rows = []
for k in sorted(set(m_before) | set(m_after)):
    qa_rows.append({
        "metric": k.replace("before_", "").replace("after_", ""),
        "before": m_before.get(k, ""),
        "after":  m_after.get(k,  ""),
        "delta":  (m_after.get(k, 0) - m_before.get(k, 0)) if isinstance(m_after.get(k, 0), (int, float)) else ""
    })
qa_df = pd.DataFrame(qa_rows)
qa_df.to_csv(OUT_QA_SUMMARY, index=False)

# --- Tabelle di riepilogo per mese (per mostrare che ci sono tutti i mesi) ---
by_month = (
    clean.groupby("mese_rif")
         .agg(righe=("code","size"), codici_unici=("code","nunique"))
)
# ordina i mesi in modo cronologico
by_month = by_month.reindex(MONTH_ORDER).reset_index().rename(columns={"mese_rif":"mese"})

# --- HTML senza data di generazione ---
html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Data Cleaning & QA Summary</title>
<style>
body{{font-family:Arial;margin:24px}}
table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ddd;padding:6px}} th{{background:#eee}}
h2{{margin-top:28px}}
</style></head>
<body>
<h1>Data Cleaning & QA Summary</h1>
<p>Righe finali nel dataset integrato: {len(clean)}</p>

<h2>Distribuzione per mese (righe e codici unici)</h2>
{by_month.to_html(index=False)}

<h2>QA Summary (prima/dopo)</h2>
{qa_df.to_html(index=False)}

<h2>Null per colonna (post-cleaning)</h2>
{clean.isna().sum().reset_index().rename(columns={"index":"colonna",0:"null_count"}).to_html(index=False)}
<h2>Esempio dati finali (prime 15 righe)</h2>
{clean.head(15).to_html(index=False)}
</body></html>
"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("Creati:")
print(f" - {OUT_DATASET}")
print(f" - {OUT_QA_SUMMARY}")
print(f" - {OUT_HTML}")
