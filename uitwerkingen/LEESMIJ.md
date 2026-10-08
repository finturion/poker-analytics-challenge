# Uitwerkingen

Gegenereerd door `scripts/maak_uitwerkingen.py`. **Niet met de hand aanpassen** —
de volgende run overschrijft je wijziging. De ingevulde cellen staan in
`scripts/uitwerkingen/week*.py`.

```bash
python3 scripts/maak_uitwerkingen.py            # alles
python3 scripts/maak_uitwerkingen.py --week 1   # één week
```

## Een andere API, zonder een cel aan te raken

De uitwerkingen halen het adres uit de omgeving:

```bash
export POKER_API_URL=https://jouw-datalab-adres
export POKER_STUDENT_ID=500123456
export POKER_TOKEN=...
```

Zonder die variabelen gaan ze naar de productie-API.

**Let op bij `lever_in()`.** Die functie heeft het adres óók hard in
`_hulpfuncties.py` staan, als standaardwaarde. De generator geeft daarom
`api_url=API_URL` mee bij elke aanroep. Zonder dat lever je in bij productie
terwijl je denkt dat je het datalab test — gemeten op 8 oktober 2026, en dat
merk je niet aan een foutmelding maar aan een inzending in de verkeerde database.

## Zelf een API draaien om tegenaan te testen

```bash
POKER_TOKENS_JSON='{"500000001":"token1","500000002":"token2"}' \
POKER_DOCENT_TOKEN='docenttest' PYTHONPATH=api \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8777
```

Zonder `DATABASE_URL` schrijft hij JSON-bestanden in de map waar je hem start,
dus doe dat in een lege map.

Twee studenten is het minimum: de peer review laat je andermans grafieken
beoordelen, dus met één account is de galerij leeg en loopt Deel 5 stuk op een
`IndexError`. Dat is geen fout in het notebook maar in de testopstelling.

Draai na het inleveren het toernooi opnieuw, anders staat je bot nog niet in de
uitslag:

```bash
curl -X POST -H "Authorization: Bearer docenttest" \
  http://127.0.0.1:8777/toernooi/1/opnieuw
```

## Status

| Notebook | Uitwerking | Draait end-to-end |
|---|---|---|
| Week1_Werkcollege1 | ja | ja, inclusief inleveren |
| Week1_Werkcollege2 | ja | ja, inclusief toernooi en peer review |
| Week2 t/m Week6 | nog niet | — |
