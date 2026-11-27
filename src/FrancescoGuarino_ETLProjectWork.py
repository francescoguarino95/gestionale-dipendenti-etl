# PROJECT WORK FRANCESCO GUARINO
# File: src/FrancescoGuarino_ETLProjectWork.py
# Ruolo: pipeline ETL multi-fonte su 'dipendente' (raccolta CSV/Excel da data/etl_input/,
# esportazione opzionale dal DB, trasformazione/pulizia, caricamento/sync su PostgreSQL e archiviazione in data/processati/)

from pathlib import Path
import shutil
import pandas as pd
from FrancescoGuarino_DBProjectWork import (
    BASE_DIR,
    DATA_DIR,
    _get_settings_sicuri,
    _risolvi_percorso_csv,
    esporta_tabella_csv,
    get_conn,
    get_engine,
)

ETL_INPUT_DIR = DATA_DIR / "etl_input"
PROCESSATI_DIR = DATA_DIR / "processati"
TABELLA_DESTINAZIONE = "dipendente"
ESTENSIONI_SUPPORTATE = {".csv", ".xlsx", ".xls"}


# Legge un singolo file CSV o Excel in un DataFrame pandas
def _leggi_singolo_file(percorso):
    estensione = percorso.suffix.lower()
    if estensione == ".csv":
        return pd.read_csv(percorso)
    if estensione in {".xlsx", ".xls"}:
        return pd.read_excel(percorso)
    raise ValueError(f"Formato file non supportato: '{percorso.name}'")


# Raccoglie i DataFrame da data/etl_input/ (e opzionalmente dalla tabella DB esportata in CSV)
def raccogli_fonti_etl(includi_db=False, nome_tabella_db=TABELLA_DESTINAZIONE):
    ETL_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("RACCOLTA FONTI")

    dataframe_list = []
    file_trovati = []

    for elemento in sorted(ETL_INPUT_DIR.iterdir()):
        if elemento.is_file() and elemento.suffix.lower() in ESTENSIONI_SUPPORTATE:
            df_file = _leggi_singolo_file(elemento)
            print(f"Letto file '{elemento.name}' ({len(df_file)} righe).")
            dataframe_list.append(df_file)
            file_trovati.append(elemento)

    if includi_db:
        csv_db = esporta_tabella_csv(nome_tabella_db, f"{nome_tabella_db}_etl_staging.csv")
        if csv_db and Path(csv_db).exists():
            df_db = pd.read_csv(csv_db)
            print(f"Inclusi {len(df_db)} record esportati dalla tabella '{nome_tabella_db}'.")
            dataframe_list.append(df_db)

    if not dataframe_list:
        return pd.DataFrame(), file_trovati

    df_unito = pd.concat(dataframe_list, ignore_index=True)
    print(f"Totale righe unite prima della pulizia: {len(df_unito)}")
    return df_unito, file_trovati


# Sposta in data/processati/ i file lavorati con successo
def _archivia_file_processati(file_list):
    if not file_list:
        return
    PROCESSATI_DIR.mkdir(parents=True, exist_ok=True)
    for percorso_file in file_list:
        if percorso_file.exists():
            destinazione = PROCESSATI_DIR / percorso_file.name
            if destinazione.exists():
                destinazione.unlink()
            shutil.move(str(percorso_file), str(destinazione))
    print(f"Spostati {len(file_list)} file in '{PROCESSATI_DIR}'.")


# Funzione per leggere i dati grezzi dal file CSV in un DataFrame pandas
def estrai_csv(percorso_file):
    cfg = _get_settings_sicuri()
    print("ESTRAZIONE")
    percorso = _risolvi_percorso_csv(percorso_file, cfg["input_file_name"])
    df = pd.read_csv(percorso)
    print("Righe lette:", len(df))
    return df


# Funzione per rimuovere i duplicati, sistemare i campi vuoti, normalizzare date e stipendi e converte i tipi
def trasforma_dati(df):
    print("TRASFORMAZIONE")
    df = df.copy()

    # Rimuove eventuali righe identiche
    df = df.drop_duplicates()

    # Pulisce gli spazi dai testi e gestisce le email mancanti
    for col in ["nome", "cognome", "email"]:
        df[col] = df[col].astype(str).str.strip()

    df["email"] = df["email"].replace({"": pd.NA, "nan": pd.NA})
    email_mancanti = df["email"].isna()
    df.loc[email_mancanti, "email"] = (
        "da.assegnare." + df.loc[email_mancanti, "id"].astype(str) + "@azienda.it"
    )

    # Uniforma le date in formato YYYY-MM-DD
    df["data_assunzione"] = pd.to_datetime(
        df["data_assunzione"],
        format="mixed",
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    # Pulisce la colonna stipendio rimuovendo '€' e spazi e convertendo in numero
    stipendio_pulito = (
        df["stipendio"]
        .astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )
    df["stipendio"] = pd.to_numeric(stipendio_pulito, errors="coerce")

    # Converte dipartimento_id in numerico per allinearlo alla tabella dipendente
    if "dipartimento_id" in df.columns:
        df["dipartimento_id"] = pd.to_numeric(df["dipartimento_id"], errors="coerce")

    # Elimina le righe senza id o senza stipendio valido
    df = df.dropna(subset=["id", "stipendio"])

    # Converte i tipi di dato finali
    df["id"] = df["id"].astype(int)
    df["stipendio"] = df["stipendio"].astype(float).round(2)
    if "dipartimento_id" in df.columns:
        df["dipartimento_id"] = df["dipartimento_id"].astype("Int64")

    # Mantiene solo le colonne presenti nella tabella dipendente
    colonne_tabella = [
        c
        for c in [
            "id",
            "nome",
            "cognome",
            "email",
            "data_assunzione",
            "stipendio",
            "dipartimento_id",
        ]
        if c in df.columns
    ]
    df = df[colonne_tabella]

    print("Righe pulite pronte:", len(df))
    return df


# Carica i dati puliti su PostgreSQL (append standard oppure sync mirato se incluso il DB)
def carica_su_db(df, nome_tabella, sync_con_db=False):
    cfg = _get_settings_sicuri()
    print("CARICAMENTO")

    if df.empty:
        print("Nessuna riga valida da caricare.")
        return

    if not sync_con_db:
        engine = get_engine()
        df.to_sql(
            name=nome_tabella,
            con=engine,
            if_exists="append",
            index=False,
        )
        print(f"Dati caricati nella tabella '{nome_tabella}' su '{cfg['db_name']}'.")
        return

    df_dedup = df.drop_duplicates(subset=["id"], keep="last").copy()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM {nome_tabella};")
    id_esistenti = {riga[0] for riga in cur.fetchall()}

    righe_da_aggiornare = df_dedup[df_dedup["id"].isin(id_esistenti)]
    righe_nuove = df_dedup[~df_dedup["id"].isin(id_esistenti)]

    for _, riga in righe_da_aggiornare.iterrows():
        dip_id = None if pd.isna(riga.get("dipartimento_id")) else int(riga["dipartimento_id"])
        data_ass = None if pd.isna(riga.get("data_assunzione")) else str(riga["data_assunzione"])
        cur.execute(
            f"""
            UPDATE {nome_tabella}
            SET nome = %s,
                cognome = %s,
                email = %s,
                data_assunzione = %s,
                stipendio = %s,
                dipartimento_id = %s
            WHERE id = %s;
            """,
            (
                riga["nome"],
                riga["cognome"],
                riga["email"],
                data_ass,
                float(riga["stipendio"]),
                dip_id,
                int(riga["id"]),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()

    if not righe_nuove.empty:
        engine = get_engine()
        righe_nuove.to_sql(
            name=nome_tabella,
            con=engine,
            if_exists="append",
            index=False,
        )

    print(
        f"Sincronizzazione su '{nome_tabella}' ({cfg['db_name']}): "
        f"{len(righe_da_aggiornare)} aggiornate, {len(righe_nuove)} inserite."
    )


# Funzione per coordinare l'esecuzione completa della mini-pipeline ETL multi-fonte
def esegui_etl(percorso_file=None):
    ETL_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSATI_DIR.mkdir(parents=True, exist_ok=True)

    # Modalità diretta se viene passato esplicitamente un singolo file
    if percorso_file is not None:
        df_grezzo = estrai_csv(percorso_file)
        df_pulito = trasforma_dati(df_grezzo)
        print("\nAnteprima dati puliti:")
        print(df_pulito.to_string(index=False))
        carica_su_db(df_pulito, TABELLA_DESTINAZIONE, sync_con_db=False)
        return

    risposta_db = input(
        "Vuoi includere anche i dati della tabella 'dipendente' dal DB per ripulirli insieme? (s/N): "
    ).strip().lower()
    includi_db = risposta_db in {"s", "si", "sì", "y", "yes"}

    df_grezzo, file_trovati = raccogli_fonti_etl(
        includi_db=includi_db,
        nome_tabella_db=TABELLA_DESTINAZIONE,
    )

    if df_grezzo.empty:
        print(
            f"Nessun dato trovato in '{ETL_INPUT_DIR}' e nessuna fonte DB selezionata."
        )
        return

    df_pulito = trasforma_dati(df_grezzo)
    print("\nAnteprima dati puliti:")
    print(df_pulito.to_string(index=False))

    carica_su_db(df_pulito, TABELLA_DESTINAZIONE, sync_con_db=includi_db)
    _archivia_file_processati(file_trovati)