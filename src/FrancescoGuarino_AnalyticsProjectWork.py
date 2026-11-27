# PROJECT WORK FRANCESCO GUARINO
# File: src/FrancescoGuarino_AnalyticsProjectWork.py
# Ruolo: lettura VIEW SQL (vista_analisi_reparti, vista_trend_assunzioni_anno) con pandas.read_sql(),
# report testuali e salvataggio grafici matplotlib (bar, pie, line) in output/

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from FrancescoGuarino_DBProjectWork import (
    _get_settings_sicuri,
    esporta_tabella_csv,
    get_engine,
)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


# Risolve la cartella di output leggendo output_file_path dai settings se disponibile
def _get_output_dir():
    cfg = _get_settings_sicuri()
    out_raw = (cfg.get("output_file_path") or "").strip()
    if not out_raw:
        return OUTPUT_DIR
    percorso = Path(out_raw)
    if percorso.is_absolute():
        return percorso
    return BASE_DIR / percorso


# Legge i dati di una VIEW dal database SQL tramite pandas.read_sql()
def leggi_vista(nome_vista):
    engine = get_engine()
    query = f"SELECT * FROM {nome_vista};"
    return pd.read_sql(query, con=engine)


# Media stipendi per dipartimento
def media_stipendi_dipartimento():
    print("MEDIA STIPENDI PER DIPARTIMENTO")
    file_dip = esporta_tabella_csv("dipendente", "dipendente.csv")
    file_rep = esporta_tabella_csv("dipartimento", "dipartimento.csv")
    df1 = pd.read_csv(file_dip)
    df2 = pd.read_csv(file_rep)

    df1["stipendio"] = pd.to_numeric(df1["stipendio"], errors="coerce")

    df_unito = pd.merge(
        df1,
        df2,
        left_on="dipartimento_id",
        right_on="id",
        how="left",
        suffixes=("_dipendente", "_reparto"),
    )

    df_unito["nome_reparto"] = df_unito["nome_reparto"].fillna("Nessun reparto")

    risultato = (
        df_unito.groupby("nome_reparto", dropna=False)["stipendio"]
        .mean()
        .round(2)
        .reset_index(name="stipendio_medio")
    )

    for _, riga in risultato.iterrows():
        media = 0 if pd.isna(riga["stipendio_medio"]) else riga["stipendio_medio"]
        print(f"Reparto: {riga['nome_reparto']} | Stipendio medio: {media}€")


# Numero dipendenti per dipartimento
def numero_dipendenti_dipartimento():
    print("NUMERO DIPENDENTI PER REPARTO")
    file_dip = esporta_tabella_csv("dipendente", "dipendente.csv")
    file_rep = esporta_tabella_csv("dipartimento", "dipartimento.csv")

    df1 = pd.read_csv(file_dip)
    df2 = pd.read_csv(file_rep)

    df_unito = pd.merge(
        df1,
        df2,
        left_on="dipartimento_id",
        right_on="id",
        how="left",
        suffixes=("_dipendente", "_reparto"),
    )

    df_unito["nome_reparto"] = df_unito["nome_reparto"].fillna("Nessun reparto")

    risultato = (
        df_unito.groupby("nome_reparto", dropna=False)["id_dipendente"]
        .count()
        .reset_index(name="num_dipendenti")
    )

    for _, riga in risultato.iterrows():
        print(f"Reparto: {riga['nome_reparto']} | Dipendenti: {riga['num_dipendenti']}")


# Visualizza la fotografia analitica per reparto da vista_analisi_reparti
def report_analisi_reparti():
    print("FOTOGRAFIA ANALITICA REPARTI (VIEW)")
    df_vista = leggi_vista("vista_analisi_reparti")
    print(df_vista.to_string(index=False))
    return df_vista


# Visualizza il trend assunzioni per anno da vista_trend_assunzioni_anno
def report_trend_assunzioni():
    print("TREND ASSUNZIONI PER ANNO (VIEW)")
    df_vista = leggi_vista("vista_trend_assunzioni_anno")
    print(df_vista.to_string(index=False))
    return df_vista


# Genera il bar chart dello stipendio medio per reparto in output/
def grafico_stipendio_medio_reparto(df_reparti=None):
    out_dir = _get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    if df_reparti is None:
        df_reparti = leggi_vista("vista_analisi_reparti")

    df_plot = df_reparti.sort_values("stipendio_medio", ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(df_plot["reparto"], df_plot["stipendio_medio"], color="#2b6cb0")
    plt.title("Stipendio medio per reparto")
    plt.xlabel("Stipendio medio (€)")
    plt.ylabel("Reparto")
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()

    destinazione = out_dir / "stipendio_medio_reparto.png"
    plt.savefig(destinazione, dpi=300)
    plt.close()
    print(f"Salvato grafico: {destinazione}")


# Genera il pie chart della distribuzione dipendenti per reparto in output/
def grafico_distribuzione_reparto(df_reparti=None):
    out_dir = _get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    if df_reparti is None:
        df_reparti = leggi_vista("vista_analisi_reparti")

    df_plot = df_reparti[df_reparti["num_dipendenti"] > 0]

    plt.figure(figsize=(8, 8))
    plt.pie(
        df_plot["num_dipendenti"],
        labels=df_plot["reparto"],
        autopct="%1.1f%%",
        startangle=140,
    )
    plt.title("Distribuzione dipendenti per reparto")
    plt.tight_layout()

    destinazione = out_dir / "distribuzione_dipendenti_reparto.png"
    plt.savefig(destinazione, dpi=300)
    plt.close()
    print(f"Salvato grafico: {destinazione}")


# Genera il line chart delle assunzioni per anno in output/
def grafico_trend_assunzioni_anno(df_trend=None):
    out_dir = _get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    if df_trend is None:
        df_trend = leggi_vista("vista_trend_assunzioni_anno")

    df_plot = df_trend.sort_values("anno_assunzione")

    plt.figure(figsize=(10, 5))
    plt.plot(
        df_plot["anno_assunzione"].astype(str),
        df_plot["numero_assunzioni"],
        marker="o",
        linewidth=2,
        color="#2f855a",
    )
    plt.title("Trend assunzioni per anno")
    plt.xlabel("Anno di assunzione")
    plt.ylabel("Numero assunzioni")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    destinazione = out_dir / "trend_assunzioni_anno.png"
    plt.savefig(destinazione, dpi=300)
    plt.close()
    print(f"Salvato grafico: {destinazione}")


# Genera tutti e 3 i grafici a partire dalle VIEW SQL
def genera_tutti_grafici():
    out_dir = _get_output_dir()
    print("GENERAZIONE GRAFICI DA VIEW SQL")
    df_reparti = leggi_vista("vista_analisi_reparti")
    df_trend = leggi_vista("vista_trend_assunzioni_anno")

    grafico_stipendio_medio_reparto(df_reparti)
    grafico_distribuzione_reparto(df_reparti)
    grafico_trend_assunzioni_anno(df_trend)
    print(f"Tutti i grafici sono stati salvati nella cartella {out_dir.name}/.")