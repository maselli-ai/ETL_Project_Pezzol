# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RAW_DIR = (HERE / "dati_originali").resolve()   # può anche essere vuota
CLEAN_DIR = (HERE / "dati_puliti").resolve()
OUT_DIR = (HERE / "ETL_QA").resolve()
OUT_DIR.mkdir(exist_ok=True)

def summarize(df: pd.DataFrame, name: str) -> dict:
    num_neg = 0
    num_dup = int(df.duplicated().sum())
    if not df.select_dtypes(include="number").empty:
        num_neg = int((df.select_dtypes(include="number") < 0).sum().sum())
    return {
        "file": name,
        "righe": int(len(df)),
        "valori_nulli": int(df.isna().sum().sum()),
        "duplicati": num_dup,
        "negativi": num_neg,
    }

def load_stats(folder: Path):
    stats = []
    for f in sorted(folder.glob("*.xlsx")):
        df = pd.read_excel(f)
        stats.append(summarize(df, f.stem))
    return pd.DataFrame(stats)

raw_df = load_stats(RAW_DIR) if RAW_DIR.exists() else pd.DataFrame()
clean_df = load_stats(CLEAN_DIR)

# Se non ci sono i grezzi, crea un confronto “vuoto → pulito”
if raw_df.empty:
    raw_df = clean_df.copy()
    raw_df[["righe","valori_nulli","duplicati","negativi"]] = 0

# allinea per nome file (outer nel caso i set non coincidano)
compare = pd.merge(raw_df, clean_df, on="file", how="outer",
                   suffixes=("_raw", "_clean")).fillna(0)

# ---------- Grafico 1: righe ----------
plt.figure(figsize=(10,6))
x = range(len(compare))
plt.bar(x, compare["righe_raw"], label="Prima")
plt.bar(x, compare["righe_clean"], bottom=None, alpha=0.6, label="Dopo")
plt.title("Righe prima/dopo pulizia")
plt.xlabel("File")
plt.ylabel("Numero di righe")
plt.xticks(x, compare["file"], rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig(OUT_DIR / "confronto_righe.png")
plt.close()

# ---------- Grafico 2: valori nulli ----------
plt.figure(figsize=(10,6))
x = range(len(compare))
plt.bar(x, compare["valori_nulli_raw"], label="Nulli prima")
plt.bar(x, compare["valori_nulli_clean"], alpha=0.6, label="Nulli dopo")
plt.title("Valori nulli prima e dopo")
plt.xlabel("File")
plt.ylabel("Conteggio")
plt.xticks(x, compare["file"], rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig(OUT_DIR / "confronto_nulli.png")
plt.close()

# ---------- Grafico 3: duplicati e negativi ----------
plt.figure(figsize=(10,6))
width = 0.2
x = range(len(compare))
x1 = [i - 1.5*width for i in x]
x2 = [i - 0.5*width for i in x]
x3 = [i + 0.5*width for i in x]
x4 = [i + 1.5*width for i in x]
plt.bar(x1, compare["duplicati_raw"], width=width, label="Duplicati prima")
plt.bar(x2, compare["duplicati_clean"], width=width, label="Duplicati dopo")
plt.bar(x3, compare["negativi_raw"], width=width, label="Negativi prima")
plt.bar(x4, compare["negativi_clean"], width=width, label="Negativi dopo")
plt.title("Duplicati e valori negativi (pre/post)")
plt.xlabel("File")
plt.ylabel("Conteggio")
plt.xticks(x, compare["file"], rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig(OUT_DIR / "confronto_duplicati_negativi.png")
plt.close()

# salva anche una tabella di confronto
compare.to_excel(OUT_DIR / "confronto_pre_post.xlsx", index=False)
print("Grafici e confronto salvati in:", OUT_DIR)
