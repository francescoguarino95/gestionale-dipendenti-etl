# Gestionale Dipendenti & Pipeline ETL (Project Work)

Applicazione CLI in Python collegata a un database PostgreSQL (`DB4`) per la gestione operativa dei dipendenti, l'importazione e pulizia dei dati tramite pipeline ETL multi-fonte e l'analisi tramite VIEW SQL e grafici in `matplotlib`.

## Struttura del progetto

- `src/FrancescoGuarino_MainProjectWork.py`: entry point con menu interattivo (opzioni `0-10`).
- `src/FrancescoGuarino_DBProjectWork.py`: gestione configurazioni (`ETL_settings.csv`), connessione PostgreSQL (`psycopg2` e `SQLAlchemy`), operazioni CRUD ed esportazione tabelle in CSV.
- `src/FrancescoGuarino_ETLProjectWork.py`: pipeline ETL multi-fonte su `dipendente` (raccolta CSV/Excel da `data/etl_input/`, opzione estrazione/sincronizzazione dal DB, pulizia e normalizzazione dati, archiviazione in `data/processati/` e log JSON).
- `src/FrancescoGuarino_AnalyticsProjectWork.py`: lettura delle VIEW SQL (`vista_analisi_reparti`, `vista_trend_assunzioni_anno`), report testuali e salvataggio grafici in `output/`.
- `sql/`: script SQL per creazione tabelle e `VIEW` analitiche.
- `data/`: file di configurazione, input ETL (`data/etl_input/`) e archivio file già lavorati (`data/processati/`).
- `output/`: grafici e log generati dall'applicazione.

## Prerequisiti

1. Python 3.x e ambiente virtuale (es. `.venv`) configurato.
2. PostgreSQL attivo con database `DB4` e tabelle/VIEW inizializzate tramite gli script in `sql/`.
3. Librerie Python installate nel `.venv`: `pandas`, `psycopg2` (o `psycopg2-binary`), `sqlalchemy`, `matplotlib`, `openpyxl`.

## Configurazione

1. Verifica o crea `data/ETL_settings.csv` con i parametri di connessione al DB e i percorsi di lavoro (evita di committare password reali su Git).
2. Assicurati che il servizio PostgreSQL sia avviato e che esistano i reparti (`dipartimento`) referenziati dai record in ingresso.

## Istruzioni all'uso

Avvia il programma dalla cartella radice del progetto (con l'ambiente virtuale attivo):

```bash
python src/FrancescoGuarino_MainProjectWork.py
```

Dal menu interattivo puoi scegliere tra:
- **1–3, 5, 7**: operazioni CRUD su `dipendente` (inserimento, ricerca per cognome, elenco ordinato per reparto, aumento stipendi assunti nel 2020, conteggio dipendenti per reparto).
- **4, 6**: calcolo media stipendi per reparto ed esportazione delle tabelle consentite in CSV.
- **8 (Pipeline ETL)**: raccoglie tutti i file `.csv`, `.xlsx` e `.xls` presenti in `data/etl_input/` (con possibilità di includere anche la tabella `dipendente` dal DB), normalizza testi, email mancanti, date (`YYYY-MM-DD`) e stipendi, carica o sincronizza i record su PostgreSQL (`UPDATE` sugli `id` esistenti e `INSERT` sui nuovi) e sposta i file elaborati in `data/processati/`.
- **9–10 (Analytics & Grafici)**: interroga le `VIEW` SQL (`vista_analisi_reparti` e `vista_trend_assunzioni_anno`), stampa i report a terminale e salva i grafici `.png` in `output/`.
- **0**: esce dall'applicazione.

## Flusso end-to-end consigliato per il test

1. Inserisci uno o più file di prova (`.csv` o `.xlsx`) in `data/etl_input/`.
2. Lancia il programma e scegli l'opzione `8` per eseguire l'ETL e verificare l'archiviazione dei file in `data/processati/`.
3. Scegli l'opzione `9` per verificare che le VIEW SQL riflettano i nuovi dati caricati.
4. Scegli l'opzione `10` per generare i grafici aggiornati nella cartella `output/`.