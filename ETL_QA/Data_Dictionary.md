# Data Dictionary
## code
- Descrizione: Codice materiale univoco (alfanumerico).
- Tipo: string
- Unità: 
- Cardinalità: 77
- Null (n): 1  –  Null (%): 0.31%
- Regole/Controlli: Solo A–Z e 0–9; maiuscolo; non vuoto nei record validi.
- Note: 

## description
- Descrizione: Descrizione testuale del materiale.
- Tipo: string
- Unità: 
- Cardinalità: 99
- Null (n): 0  –  Null (%): 0.0%
- Regole/Controlli: Testo libero; evitare nulli per record attivi.
- Note: 

## uom
- Descrizione: Unità di misura standardizzata per le quantità.
- Tipo: string
- Unità: —
- Cardinalità: 2
- Null (n): 0  –  Null (%): 0.0%
- Valori ammessi: KG, PZ
- Regole/Controlli: Valori ammessi: KG (default).
- Note: 

## stock
- Descrizione: Giacenza a fine periodo (quantità fisica/contabile).
- Tipo: float
- Unità: pezzi o unità coerenti con uom
- Cardinalità: 142
- Null (n): 0  –  Null (%): 0.0%
- Range numerico: min=0.0 – max=26627.0
- Regole/Controlli: Valore numerico, non negativo.
- Note: 

## real
- Descrizione: Giacenza reale (conteggio fisico o stock effettivo).
- Tipo: float
- Unità: pezzi o unità coerenti con uom
- Cardinalità: 31
- Null (n): 0  –  Null (%): 0.0%
- Range numerico: min=0.0 – max=11519.16
- Regole/Controlli: Valore numerico, non negativo.
- Note: 

## outgoing
- Descrizione: Quantità in uscita (prelievi/spedizioni) nel periodo.
- Tipo: float
- Unità: pezzi o unità coerenti con uom
- Cardinalità: 132
- Null (n): 0  –  Null (%): 0.0%
- Range numerico: min=0.0 – max=26627.0
- Regole/Controlli: Valore numerico, non negativo.
- Note: 

## mese_rif
- Descrizione: Mese di riferimento del record (GENNAIO…AGOSTO).
- Tipo: string
- Unità: 
- Cardinalità: 7
- Null (n): 0  –  Null (%): 0.0%
- Valori ammessi: GENNAIO, FEBBRAIO, APRILE, MAGGIO, GIUGNO, LUGLIO, AGOSTO
- Regole/Controlli: Valori ammessi: GENNAIO, FEBBRAIO, APRILE, MAGGIO, GIUGNO, LUGLIO, AGOSTO.
- Note: 
