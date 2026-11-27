# PROJECT WORK FRANCESCO GUARINO
# File: src/FrancescoGuarino_DBProjectWork.py
# Ruolo: lettura settings, connessione PostgreSQL (DB4) e operazioni CRUD/esportazione CSV in data/
# (aggiungi, cerca, elenco, aggiorna stipendi 2020, esporta)

import csv
from pathlib import Path
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "DB4"
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PW = "Bcsoftqwerty"
DEFAULT_INPUT_FILE = "nuovi_dipendenti.csv"
TABELLE_CONSENTITE = {"dipartimento", "dipendente", "prodotto", "vendite"}


def carica_settings_etl(percorso_settings=None, indice_riga=0):
    file_settings = Path(percorso_settings) if percorso_settings else (DATA_DIR / "ETL_settings.csv")
    df_settings = pd.read_csv(file_settings)

    if df_settings.empty:
        raise ValueError(f"Il file di configurazione '{file_settings}' è vuoto.")

    riga = df_settings.iloc[indice_riga]
    return {
        "db_url": str(riga["DB_CONNECTION_URL"]).strip(),
        "db_host": str(riga["DB_HOST"]).strip(),
        "db_port": str(riga["DB_PORT"]).strip(),
        "db_name": str(riga["DB_NAME"]).strip(),
        "db_user": str(riga["DB_USER"]).strip(),
        "db_password": str(riga["DB_PASSWORD"]).strip(),
        "input_file_path": str(riga["INPUT_FILE_PATH"]).strip(),
        "output_file_path": str(riga["OUTPUT_FILE_PATH"]).strip(),
        "input_file_name": str(riga["INPUT_FILE_NAME"]).strip(),
        "output_file_name": str(riga["OUTPUT_FILE_NAME"]).strip(),
    }


def _get_settings_sicuri():
    try:
        return carica_settings_etl()
    except (FileNotFoundError, pd.errors.EmptyDataError, KeyError, IndexError, ValueError):
        return {
            "db_url": f"postgresql://{DEFAULT_DB_HOST}:{DEFAULT_DB_PORT}",
            "db_host": DEFAULT_DB_HOST,
            "db_port": DEFAULT_DB_PORT,
            "db_name": DEFAULT_DB_NAME,
            "db_user": DEFAULT_DB_USER,
            "db_password": DEFAULT_DB_PW,
            "input_file_path": "data",
            "output_file_path": "output",
            "input_file_name": DEFAULT_INPUT_FILE,
            "output_file_name": "grafici",
        }


# Crea e restituisce la connessione al database PostgreSQL
def get_conn():
    cfg = _get_settings_sicuri()
    return psycopg2.connect(
        host=cfg["db_host"],
        database=cfg["db_name"],
        user=cfg["db_user"],
        password=cfg["db_password"],
        port=cfg["db_port"],
    )


# Restituisce l'engine SQLAlchemy per il database PostgreSQL
def get_engine():
    cfg = _get_settings_sicuri()
    url_db = (
        f"postgresql+psycopg2://{cfg['db_user']}:{cfg['db_password']}"
        f"@{cfg['db_host']}:{cfg['db_port']}/{cfg['db_name']}"
    )
    return create_engine(url_db)


# Risolve il percorso di un file CSV cercando prima in data/ se non è già un percorso completo
def _risolvi_percorso_csv(nome_o_percorso, nome_predefinito):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    testo = (nome_o_percorso or "").strip()
    if not testo:
        testo = nome_predefinito
    percorso = Path(testo)
    if percorso.is_absolute() or len(percorso.parts) > 1:
        return percorso
    return DATA_DIR / percorso


# Aggiungiamo un dipendente sul DB (INSERT e commit)
def aggiungi_dipendente():
    print("AGGIUNGI DIPENDENTE")
    nome = input("Nome: ").strip().capitalize()
    cognome = input("Cognome: ").strip().capitalize()
    email = input("Email: ").strip()
    data_assunzione = input("Data assunzione (YYYY-MM-DD): ").strip()
    stipendio = float(input("Stipendio: ").strip())
    dipartimento_id = int(input("ID dipartimento: ").strip())

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dipendente (nome, cognome, email, data_assunzione, stipendio, dipartimento_id)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (nome, cognome, email, data_assunzione, stipendio, dipartimento_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Dipendente salvato nel database.")


# Cerca dipendente per cognome sul DB
def cerca_dipendente():
    print("CERCA DIPENDENTE")
    cognome_cercato = input("Cognome da cercare: ").strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.nome, d.cognome, dip.nome, d.stipendio
        FROM dipendente d
        LEFT JOIN dipartimento dip ON d.dipartimento_id = dip.id
        WHERE d.cognome ILIKE %s;
        """,
        (cognome_cercato,),
    )
    righe = cur.fetchall()
    cur.close()
    conn.close()

    if not righe:
        print("Nessun dipendente trovato.")
        return

    for nome, cognome, dipartimento, stipendio in righe:
        dip_txt = dipartimento if dipartimento else "Nessun dipartimento"
        print(
            f"Trovato: {nome} {cognome} | Dipartimento: {dip_txt} | Stipendio: {stipendio}€"
        )


# Elenco completo ordinato per dipartimento
def visualizza_elenco():
    print("ELENCO DIPENDENTI")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.nome, d.cognome, dip.nome, d.stipendio
        FROM dipendente d
        LEFT JOIN dipartimento dip ON d.dipartimento_id = dip.id
        ORDER BY dip.nome, d.cognome, d.nome;
        """
    )
    righe = cur.fetchall()
    cur.close()
    conn.close()

    if not righe:
        print("L'archivio è vuoto.")
        return

    for nome, cognome, dipartimento, stipendio in righe:
        dip_txt = dipartimento if dipartimento else "Nessun dipartimento"
        print(
            f"Dipendente: {nome} {cognome} | Dipartimento: {dip_txt} | Stipendio: {stipendio}€"
        )


# Aggiorna stipendio assunti nel 2020 (UPDATE e commit)
def aggiorna_stipendi_2020():
    print("AGGIORNA STIPENDI ASSUNTI 2020")
    aumento = float(input("Aumento in euro da aggiungere: ").strip())

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dipendente
        SET stipendio = stipendio + %s
        WHERE EXTRACT(YEAR FROM data_assunzione) = 2020;
        """,
        (aumento,),
    )
    aggiornati = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Stipendi aggiornati per {aggiornati} dipendenti del 2020.")


# Funzione per esportare una tabella in CSV
def esporta_tabella_csv(tabella=None, nome_file=None):
    print("ESPORTA TABELLA IN CSV")

    if tabella is None:
        tabella = input(
            "Nome tabella da esportare (dipartimento, dipendente, prodotto, vendite): "
        ).strip()

    if tabella not in TABELLE_CONSENTITE:
        print(f"Tabella '{tabella}' non valida o non consentita.")
        return None

    percorso_file = _risolvi_percorso_csv(nome_file, f"{tabella}.csv")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {tabella};")
    righe = cur.fetchall()
    colonne = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    with open(percorso_file, mode="w", newline="", encoding="utf-8") as file_csv:
        writer = csv.writer(file_csv)
        writer.writerow(colonne)
        writer.writerows(righe)

    print(f"Esportate {len(righe)} righe in '{percorso_file}'.")
    return percorso_file