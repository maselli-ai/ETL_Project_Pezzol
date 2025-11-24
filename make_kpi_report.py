from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset_finale_ETL_QA.xlsx"
OUT_DIR = HERE / "ETL_QA"
OUT_DIR.mkdir(exist_ok=True)

MONTH_ORDER = ["GENNAIO","FEBBRAIO","APRILE","MAGGIO","GIUGNO","LUGLIO","AGOSTO"]
MONTH_NUM = {m:i+1 for i,m in enumerate(MONTH_ORDER)}

df = pd.read_excel(DATASET)
df = df.copy()

for c in ["stock","real","outgoing"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

df["mese_rif"] = df["mese_rif"].astype(str).str.upper().str.strip()
df = df[df["mese_rif"].isin(MONTH_ORDER)]
df["mese_n"] = df["mese_rif"].map(MONTH_NUM)

df["stock_avg"] = (df.get("stock",0) + df.get("real",0)) / 2.0
df["consumo"] = df.get("outgoing",0)

# KPI 1: Rotazione (Inventory Turnover) 
# Per mese: turnover_m = somma(consumo) / media(stock_avg)
turn_by_month = (
    df.groupby("mese_rif")
      .agg(consumo_tot=("consumo","sum"), stock_med=("stock_avg","mean"))
      .reset_index()
)
turn_by_month["turnover_m"] = np.where(turn_by_month["stock_med"]>0,
                                       turn_by_month["consumo_tot"]/turn_by_month["stock_med"], 0.0)
turn_by_month["mese_n"] = turn_by_month["mese_rif"].map(MONTH_NUM)
turn_by_month = turn_by_month.sort_values("mese_n")

# Annualizzazione: turnover_annuo ≈ turnover_mensile * 12
turn_by_month["turnover_annuo"] = turn_by_month["turnover_m"] * 12

# Valore medio periodo (annuo)
months = turn_by_month.shape[0]
consumo_totale = df["consumo"].sum()
stock_med_periodo = df["stock_avg"].mean()
turnover_periodo_annuo = (consumo_totale / stock_med_periodo) * (12 / months) if stock_med_periodo>0 else 0.0

# KPI 2: DIO 
dio_by_month = turn_by_month.copy()
dio_by_month["DIO"] = np.where(dio_by_month["turnover_annuo"]>0, 365.0/dio_by_month["turnover_annuo"], np.nan)
DIO_medio = np.nanmean(dio_by_month["DIO"])

# KPI 3: Overstock / Sottoscorta 
# domanda media mensile per articolo (Di)
demand_mean = (df.groupby(["code"])
                 .agg(domanda_media=("consumo","mean"),
                      giacenza_media=("stock_avg","mean"))
                 .reset_index())
demand_mean["safety"] = 0.5 * demand_mean["domanda_media"]
demand_mean["target"] = 1.5 * demand_mean["domanda_media"]

def classify_level(row):
    G, S, T = row["giacenza_media"], row["safety"], row["target"]
    if G < S: return "SOTTO-SCORTA"
    if G > T: return "OVERSTOCK"
    return "SCORTA OTTIMALE"

demand_mean["classe"] = demand_mean.apply(classify_level, axis=1)
over_under_dist = demand_mean["classe"].value_counts().reset_index()
over_under_dist.columns = ["classe","conteggio"]
over_under_dist["percentuale"] = (over_under_dist["conteggio"] / over_under_dist["conteggio"].sum() * 100).round(2)

# KPI 4: Bassa / Nulla rotazione 
# tasso mensile per articolo = consumo medio mensile / giacenza media
rot = demand_mean.copy()
rot["tasso_mensile"] = np.where(rot["giacenza_media"]>0, rot["domanda_media"]/rot["giacenza_media"], 0.0)

def classify_rotation(x):
    if x == 0: return "NULLA"
    if 0 < x <= 0.2: return "BASSA"
    if x > 1: return "ALTA"
    return "MEDIA"

rot["classe_rot"] = rot["tasso_mensile"].apply(classify_rotation)
rot_dist = rot["classe_rot"].value_counts().reindex(["ALTA","MEDIA","BASSA","NULLA"]).fillna(0).astype(int).reset_index()
rot_dist.columns = ["classe_rot","conteggio"]
rot_dist["percentuale"] = (rot_dist["conteggio"] / rot_dist["conteggio"].sum() * 100).round(2)

# ---- Salvataggi tabelle ----
with pd.ExcelWriter(OUT_DIR / "kpi_summary.xlsx", engine="openpyxl") as w:
    turn_by_month[["mese_rif","turnover_m","turnover_annuo"]].to_excel(w, sheet_name="turnover", index=False)
    dio_by_month[["mese_rif","DIO"]].to_excel(w, sheet_name="DIO", index=False)
    over_under_dist.to_excel(w, sheet_name="over_understock", index=False)
    rot_dist.to_excel(w, sheet_name="rotazione_classi", index=False)

#  Grafici (matplotlib) 
# 1) Turnover annuo per mese
plt.figure(figsize=(9,5))
plt.plot(turn_by_month["mese_rif"], turn_by_month["turnover_annuo"], marker="o")
plt.title("Indice di rotazione (annualizzato)")
plt.xlabel("Mese")
plt.ylabel("Rotazioni/anno")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(OUT_DIR / "kpi_turnover_trend.png")
plt.close()

# 2) DIO per mese
plt.figure(figsize=(9,5))
plt.plot(dio_by_month["mese_rif"], dio_by_month["DIO"], marker="o")
plt.title("Days Inventory Outstanding (DIO)")
plt.xlabel("Mese")
plt.ylabel("Giorni")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(OUT_DIR / "kpi_dio_trend.png")
plt.close()

# 3) Overstock / Sottoscorta
plt.figure(figsize=(7,5))
plt.bar(over_under_dist["classe"], over_under_dist["conteggio"])
plt.title("Distribuzione livelli di scorta")
plt.xlabel("Classe")
plt.ylabel("Numero articoli")
plt.tight_layout()
plt.savefig(OUT_DIR / "kpi_over_under_bar.png")
plt.close()

# 4) Classi di rotazione
plt.figure(figsize=(7,5))
plt.bar(rot_dist["classe_rot"], rot_dist["conteggio"])
plt.title("Classi di rotazione articoli")
plt.xlabel("Classe")
plt.ylabel("Numero articoli")
plt.tight_layout()
plt.savefig(OUT_DIR / "kpi_rotation_classes.png")
plt.close()

# Report HTML sintetico 
html = f"""
<!doctype html><html><head><meta charset="utf-8">
<title>KPI logistici (gen–ago 2025)</title>
<style>body{{font-family:Arial;margin:24px}} img{{max-width:100%;height:auto;margin:10px 0}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:6px}} th{{background:#eee}}
.info{{margin:8px 0;color:#444}}</style></head><body>
<h1>KPI logistici (gen–ago 2025)</h1>
<div class="info">Rotazione media annualizzata: {turnover_periodo_annuo:.2f} – DIO medio: {DIO_medio:.0f} giorni</div>

<h2>Indice di rotazione (annualizzato)</h2>
<img src="kpi_turnover_trend.png"/>

<h2>DIO per mese</h2>
<img src="kpi_dio_trend.png"/>

<h2>Overstock / Sottoscorta</h2>
<img src="kpi_over_under_bar.png"/>
{over_under_dist.to_html(index=False)}

<h2>Classi di rotazione</h2>
<img src="kpi_rotation_classes.png"/>
{rot_dist.to_html(index=False)}

<hr><p>Fonte dati: ETL_QA/dataset_finale_ETL_QA.xlsx</p>
</body></html>
"""
(OUT_DIR / "kpi_report.html").write_text(html, encoding="utf-8")

print("Creati:")
print(" -", OUT_DIR / "kpi_summary.xlsx")
print(" -", OUT_DIR / "kpi_turnover_trend.png")
print(" -", OUT_DIR / "kpi_dio_trend.png")
print(" -", OUT_DIR / "kpi_over_under_bar.png")
print(" -", OUT_DIR / "kpi_rotation_classes.png")
print(" -", OUT_DIR / "kpi_report.html")

