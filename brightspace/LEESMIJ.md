# Brightspace-pagina's

Gegenereerd door `scripts/genereer_brightspace_paginas.py`. **Niet met de hand
aanpassen** — de volgende run overschrijft je wijziging. Inhoud aanpassen doe je
in de `WEKEN`-lijst in dat script, en dan opnieuw genereren.

```bash
python3 scripts/genereer_brightspace_paginas.py
```

## Wat kan Brightspace wel en niet verbergen?

**Niet:** een stuk *binnen* één HTML-pagina. Availability dates en release
conditions hangen in Brightspace aan een topic of een module in Content, niet
aan een element in de HTML. Er is geen manier om in één bestand week 1 te
tonen en week 5 te verbergen.

**Wel:** een topic per week, elk met zijn eigen datum. Daarom is er per week een
eigen bestand. Zet elk bestand als los HTML-topic in Content en geef het de
availability date van de maandag van die week; het script print die datums.

| Bestand | Topic | Availability date |
|---|---|---|
| `00_overzicht.html` | Pokerbot Analytics Challenge — overzicht | geen (altijd zichtbaar) |
| `week1.html` | Week 1 — De eerste deal | ma 31 augustus 2026 |
| `week2.html` | Week 2 — Visual Maandag | ma 7 september 2026 |
| `week3.html` | Week 3 — Bot v2 | ma 14 september 2026 |
| `week4.html` | Week 4 — Visual Maandag | ma 21 september 2026 |
| `week5.html` | Week 5 — Bot v3 & bonuspunten | ma 28 september 2026 |
| `week6.html` | Week 6 — Visual Maandag | ma 5 oktober 2026 |

Zet de zes weekpagina's in één module, dan kun je de hele challenge in één keer
verbergen zonder de datums per week weg te gooien.

## Twee dingen om te weten voordat je hierop vertrouwt

**Verbergen met CSS of JavaScript is cosmetisch.** De tekst staat in de
paginabron en is met "view source" of de developer tools te lezen. Voor "niet
afleiden" is dat genoeg; voor antwoorden of iets wat echt niet vroeg gelezen mag
worden niet.

**Een verborgen topic haalt de link weg, niet het bestand.** De notebooks en
slides staan onder `/content/enforced/764257-FT-6100DASC23-T--ALG-2627/` en
houden daar hun eigen URL. Een student die zo'n URL uit een eerdere periode nog
heeft, kan die mogelijk blijven openen. Test dat met een studentaccount voordat
je een bestand er alvast neerzet.

## Wat het script controleert

Na het schrijven controleert het script de zeven bestanden:

- elke tag die opengaat gaat ook dicht (`div`, `main`, `ul`, `table`, `tbody`,
  `li`, `tr`, `td`, `p`), en `<body>` komt precies één keer voor;
- elke link naar `/content/enforced/...` wijst naar een bestand dat in deze repo
  bestaat. Heet een bestand op Brightspace anders dan hier, dan hoort dat in
  `ANDERE_NAAM_OP_BRIGHTSPACE` te staan, anders faalt de controle.

De DataCamp-deadlines komen uit `api/datacamp_rooster.py`, dus die kunnen niet
uit de pas lopen met wat de hub laat zien.
