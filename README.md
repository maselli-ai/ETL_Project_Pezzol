ETL PROJECT FOR PEZZOL INDUSTRIES:  

Repository contenente la pipeline ETL completa per l’integrazione, pulizia,
validazione e analisi diagnostica dei dati di magazzino.

STRUTTURA:

 ➤ dati_puliti/
File Excel mensili già sottoposti a data cleaning.

 ➤ ETL_QA/
Output della fase di Quality Assurance, tra cui:
- Data Dictionary (HTML, MD, XLSX)
- Grafici di confronto pre/post qualità
  - nulli
  - duplicati
  - righe mancanti
- KPI report (rotazione, DIO, over/understock)
- Tabelle riepilogative QA
- Confronto pre/post pulizia

 ➤ Script Python
- make_quality_report.py
  Genera il report QA e le metriche di qualità.

- make_data_dictionary.py
  Crea il Data Dictionary a partire dal dataset consolidato.

- make_graphs_report.py  
  Produce i grafici di Quality Assurance e diagnostici.

- make_kpi_report.py  
  Calcola gli indicatori chiave di performance e genera il report KPI.

 ➤ Output principali
- dataset_finale_ETL_QA.xlsx
  Dataset integrato e pulito utilizzato come base per le analisi successive.

- QA_summary.xlsx / QA_summary.csv
  File di riepilogo con le metriche di qualità dei dati.

- data_quality_report.html
  Report QA completo in formato HTML.



