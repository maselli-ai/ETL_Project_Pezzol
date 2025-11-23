from pathlib import Path
import pandas as pd
import numpy as np


HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE / "dataset_finale_ETL_QA.xlsx"
OUT_XLSX = HERE / "ETL_QA" / "Data_Dictionary.xlsx"
OUT_HTML = HERE / "ETL_QA" / "Data_Dictionary.html"
OUT_MD = HERE / "ETL_QA" / "Data_Dictionary.md"

DESCR = {
    "code": "Codice materiale univoco (alfanumerico).",
    "description": "Descrizione testuale del materiale.",
    "uom": "Unità di misura standardizzata per le quantità.",
    "stock": "Giacenza a fine periodo (quantità fisica/contabile).",
    "real": "Giacenza reale (conteggio fisico o stock effettivo).",
    "outgoing": "Quantità in uscita (prelievi/spedizioni) nel periodo.",
    "mese_rif": "Mese di riferimento del record (GENNAIO…AGOSTO)."
}

RULES = {
    "code": "Solo A–Z e 0–9; maiuscolo; non vuoto nei record validi.",
    "description": "Testo libero; evitare nulli per record attivi.",
    "uom": "Valori ammessi: KG (default).",
    "stock": "Valore numerico, non negativo.",
    "real": "Valore numerico, non negativo.",
    "outgoing": "Valore numerico, non negativo.",
    "mese_rif": "Valori ammessi: GENNAIO, FEBBRAIO, APRILE, MAGGIO, GIUGNO, LUGLIO, AGOSTO."
}

UNITS = {
    "uom": "—",
    "stock": "pezzi o unità coerenti con uom",
    "real": "pezzi o unità coerenti con uom",
    "outgoing": "pezzi o unità coerenti con uom"
}

def dtype_human(series):
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string"

def summarize_column(df, col):
    s = df[col]
    d = {
        "Colonna": col,
        "Descrizione": DESCR.get(col, ""),
        "Tipo": dtype_human(s),
        "Unità": UNITS.get(col, ""),
        "Cardinalità": int(s.nunique(dropna=True)),
        "Null (n)": int(s.isna().sum()),
        "Null (%)": round(100 * s.isna().mean(), 2),
        "Esempi": ", ".join(map(lambda x: str(x)[:25], s.dropna().astype(str).unique()[:5])),
        "Regole/Controlli": RULES.get(col, ""),
        "Note": ""
    }

    if pd.api.types.is_numeric_dtype(s):
        s_num = pd.to_numeric(s, errors="coerce")
        d["Min"] = float(np.nanmin(s_num)) if s_num.notna().any() else ""
        d["Max"] = float(np.nanmax(s_num)) if s_num.notna().any() else ""
    else:
        d["Min"], d["Max"] = "", ""

    if col == "uom":
        vals = s.dropna().astype(str).str.upper().value_counts().head(10)
        d["Valori ammessi (top10)"] = ", ".join(vals.index.tolist())
    elif col == "mese_rif":
        vals = s.dropna().astype(str).str.upper().value_counts()
        order = ["GENNAIO", "FEBBRAIO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO"]
        d["Valori ammessi (ordine)"] = ", ".join([m for m in order if m in vals.index])

    return d

def main():
    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset non trovato: {DATASET_PATH}")

    df = pd.read_excel(DATASET_PATH)
    ordered = [c for c in ["code", "description", "uom", "stock", "real", "outgoing", "mese_rif"] if c in df.columns]
    for c in df.columns:
        if c not in ordered:
            ordered.append(c)
    df = df[ordered]

    rows = [summarize_column(df, c) for c in df.columns]
    dd = pd.DataFrame(rows)
    dd.to_excel(OUT_XLSX, index=False)

    
    style = """
    <style>
    body{font-family:Arial,Helvetica,sans-serif;margin:24px}
    table{border-collapse:collapse;width:100%}
    td,th{border:1px solid #ddd;padding:6px} th{background:#eee}
    </style>
    """
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Data Dictionary</title>{style}</head>
    <body>
    <h1>Data Dictionary</h1>
    {dd.to_html(index=False)}
    <hr>
    <p>Fonte: ETL_QA/dataset_finale_ETL_QA.xlsx</p>
    </body></html>"""
    OUT_HTML.write_text(html, encoding="utf-8")

    md_lines = ["# Data Dictionary"]
    for _, r in dd.iterrows():
        md_lines += [
            f"## {r['Colonna']}",
            f"- Descrizione: {r['Descrizione']}",
            f"- Tipo: {r['Tipo']}",
            f"- Unità: {r['Unità']}",
            f"- Cardinalità: {r['Cardinalità']}",
            f"- Null (n): {r['Null (n)']}  –  Null (%): {r['Null (%)']}%"
        ]
        if r.get("Min","") != "" or r.get("Max","") != "":
            md_lines.append(f"- Range numerico: min={r['Min']} – max={r['Max']}")
        if pd.notna(r.get("Valori ammessi (top10)", "")) and r["Valori ammessi (top10)"] != "":
            md_lines.append(f"- Valori ammessi: {r['Valori ammessi (top10)']}")
        if pd.notna(r.get("Valori ammessi (ordine)", "")) and r["Valori ammessi (ordine)"] != "":
            md_lines.append(f"- Valori ammessi: {r['Valori ammessi (ordine)']}")
        md_lines += [
            f"- Regole/Controlli: {r['Regole/Controlli']}",
            f"- Note: {r['Note']}",
            ""
        ]
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print("Creati:")
    print(" -", OUT_XLSX)
    print(" -", OUT_HTML)
    print(" -", OUT_MD)

if __name__ == "__main__":
    main()
