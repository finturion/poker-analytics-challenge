# Notebooks voor semester 2

Gegenereerd door `scripts/maak_sem2_notebooks.py` uit `notebooks/`. **Niet met de
hand aanpassen** — de volgende run overschrijft je wijziging. Inhoud veranderen
doe je in het bronnotebook, de bewerking in dat script.

```bash
python3 scripts/maak_sem2_notebooks.py
```

## Het verschil met semester 1

De API komt pas in week 3. In semester 1 zat hij vanaf werkcollege 1 in de stof:
inleveren in WC1, en in WC2 een deel over wat een API is (20 min), het toernooi
ophalen (15) en peer review (10). Dat is 45 van de 85 minuten van WC2, in dezelfde
week waarin tien programmeerconcepten binnenkomen — en het bracht een categorie
fouten mee die niets met programmeren te maken heeft: tokens, 401's, netwerk.

| | semester 1 | semester 2 |
|---|---|---|
| WC1 | schrijft de bot én levert in | schrijft de bot, bewaart hem lokaal |
| WC2 | API-les, toernooi ophalen, peer review | toernooi uit een bestand |
| WC3 | toernooi ophalen | toernooi uit een bestand |
| WC4 | — | hier komt de API, mét de eerste inzending |

## De data

`data/voorbeeldtoernooi.json` is een toernooi dat werkelijk gespeeld is: 28 bots,
2.800 logregels, eindstanden van 118 tot 1.835 chips, 62% fold. Alleen de
studentnummers zijn vervangen door namen, met een vaste seed zodat ze niet elk
jaar verschuiven. Gemaakt met `scripts/maak_voorbeeldtoernooi.py`, dat achteraf
controleert of er geen studentnummer in is blijven staan.

Echte data en geen verzinsel, en dat is hier geen detail: een verzonnen dataset
heeft geen rare uitschieters, en juist die maken een grafiek de moeite waard.

In werkcollege 2 volgt de student één bot uit die uitslag — `mijn_bot = "Ravi"`,
die net onder het midden staat. Vanaf week 3 is dat zijn eigen bot.

## Wat nog niet af is

Werkcollege 4 moet het API-deel nog krijgen dat uit WC2 is gehaald, plus de eerste
`lever_in()`. Dat staat nog niet in het generatiescript.

## Getest

Werkcollege 1 en 2 draaien van boven tot onder zonder netwerk, met de uitwerkingen
uit `scripts/uitwerkingen/week1.py` erop. Werkcollege 3 is omgezet maar nog niet
end-to-end gedraaid.
