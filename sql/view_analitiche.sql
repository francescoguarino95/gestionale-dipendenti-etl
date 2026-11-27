-- Fotografia analitica per reparto
CREATE OR REPLACE VIEW vista_analisi_reparti AS
SELECT
    COALESCE(dip.nome, 'Non assegnato') AS reparto,
    COUNT(d.id) AS num_dipendenti,
    ROUND(AVG(d.stipendio)::numeric, 2) AS stipendio_medio,
    ROUND(AVG((CURRENT_DATE - d.data_assunzione) / 365.25)::numeric, 1) AS anzianita_media_anni
FROM dipendente d
LEFT JOIN dipartimento dip
    ON d.dipartimento_id = dip.id
GROUP BY COALESCE(dip.nome, 'Non assegnato')
ORDER BY reparto;


-- Trend assunzioni per anno
CREATE OR REPLACE VIEW vista_trend_assunzioni_anno AS
SELECT
    EXTRACT(YEAR FROM data_assunzione)::int AS anno_assunzione,
    COUNT(id) AS numero_assunzioni
FROM dipendente
WHERE data_assunzione IS NOT NULL
GROUP BY EXTRACT(YEAR FROM data_assunzione)
ORDER BY anno_assunzione;


-- Dettaglio dipendenti con reparto e fascia di stipendio
CREATE OR REPLACE VIEW vista_dettaglio_dipendenti AS
SELECT
    d.id,
    d.nome,
    d.cognome,
    COALESCE(dip.nome, 'Non assegnato') AS reparto,
    d.stipendio,
    CASE
        WHEN d.stipendio < 2000 THEN 'Bassa'
        WHEN d.stipendio < 3000 THEN 'Media'
        ELSE 'Alta'
    END AS fascia_stipendio
FROM dipendente d
LEFT JOIN dipartimento dip
    ON d.dipartimento_id = dip.id;