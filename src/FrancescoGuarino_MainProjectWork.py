# PROJECT WORK FRANCESCO GUARINO

# File: src/FrancescoGuarino_MainProjectWork.py
# Ruolo: entry point con menu interattivo (opzioni 0-10) che delega le operazioni 
# a FrancescoGuarino_ETLProjectWork.py, FrancescoGuarino_AnalyticsProjectWork.py e FrancescoGuarino_DBProjectWork.py

from FrancescoGuarino_AnalyticsProjectWork import (
    genera_tutti_grafici,
    media_stipendi_dipartimento,
    numero_dipendenti_dipartimento,
    report_analisi_reparti,
    report_trend_assunzioni,
)
from FrancescoGuarino_DBProjectWork import (
    aggiorna_stipendi_2020,
    aggiungi_dipendente,
    cerca_dipendente,
    esporta_tabella_csv,
    visualizza_elenco,
)
from FrancescoGuarino_ETLProjectWork import esegui_etl


# Mostra il menu testuale e gestisce le scelte dell'utente
def menu():
    while True:
        print("\nGESTIONALE DIPENDENTI")
        print("1. Aggiungi un nuovo dipendente")
        print("2. Cerca un dipendente per cognome")
        print("3. Visualizza l'elenco completo ordinato per dipartimento")
        print("4. Calcola media stipendi per dipartimento")
        print("5. Aggiorna stipendi dipendenti assunti nel 2020")
        print("6. Esporta una tabella in CSV")
        print("7. Numero dipendenti per dipartimento")
        print("8. Importa nuovi dipendenti da CSV (ETL)")
        print("9. Visualizza report VIEW (reparti e trend assunzioni)")
        print("10. Genera grafici dalle VIEW in output/")
        print("0. Esci")

        scelta = input("Scegli un'opzione 0-10: ").strip()

        if scelta == "1":
            aggiungi_dipendente()
        elif scelta == "2":
            cerca_dipendente()
        elif scelta == "3":
            visualizza_elenco()
        elif scelta == "4":
            media_stipendi_dipartimento()
        elif scelta == "5":
            aggiorna_stipendi_2020()
        elif scelta == "6":
            esporta_tabella_csv()
        elif scelta == "7":
            numero_dipendenti_dipartimento()
        elif scelta == "8":
            esegui_etl()
        elif scelta == "9":
            report_analisi_reparti()
            print()
            report_trend_assunzioni()
        elif scelta == "10":
            genera_tutti_grafici()
        elif scelta == "0":
            print("Esco dal programma.")
            break
        else:
            print("Scelta non valida.")


if __name__ == "__main__":
    menu()