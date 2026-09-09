# Zeven pokerbots met zeven verschillende ideeën

Zeven losse bots, elk met één beslissings-*driver*. Niet dezelfde bot met een
andere drempel: de vraag is niet welke drempel het beste werkt, maar waar een
bot naar moet kijken.

| bestand | waar de beslissing op hangt | wat hij bewust niet doet |
|---|---|---|
| `bot_handsterkte.py` | alleen de winkans van zijn eigen twee kaarten | pot, inzet, tegenstanders, bluffen |
| `bot_potodds.py` | de prijs: `inzet / (pot + inzet)` tegen zijn winkans | tegenstanders lezen, inzetgrootte |
| `bot_tafellezer.py` | wat de tegenstanders deze hand deden | prijs berekenen, inzetgrootte |
| `bot_inzetgrootte.py` | hoeveel hij inzet: 40, 200 of alles | ronde/straat, tegenstanders lezen |
| `bot_bluffer.py` | de bluf-odds: welke foldkans heeft deze bluf nodig? | ingewikkeld waarde-spel |
| `bot_allrounder.py` | alle vier bovenstaande, opgeteld tot één `voordeel` | niets — en dat is zijn probleem |
| `bot_uitbuiter.py` | de gemeten zwakte van dit soort bots | zelf goed pokeren |

Alle zeven zijn door `valideer_bot_code(week=5)` gehaald, geen enkele is een
`constante_bot`, geen enkele crasht of duurt langer dan 0,1 ms per beslissing.
De knoppen staan bovenaan elk bestand als constanten.

De winkans-tabel (91 handen, kaartwaarden zonder kleur) is gemeten met
`schat_winkans()` uit `notebooks/_hulpfuncties_week3.py`, 30.000 simulaties per
hand. Hij staat in elk bot-bestand herhaald omdat `_hulpfuncties_week3` op de
server niet bestaat: een bot die dat importeert wordt afgekeurd.

## Draaien

```bash
python3 scripts/vergelijk_mijn_bots.py     # volle tafel + gedragsanalyse
python3 scripts/kop_op_kop_mijn_bots.py    # alle 21 paren één-tegen-één
```

12 seeds x 20 simulaties x 50 handen = 240 onafhankelijke tafels per bot.

> **Let op bij zeven bots.** `TAFEL_GROOTTE_MAX` is 6, maar
> `_verdeel_in_tafels()` plakt een rest-tafel met minder dan 2 bots bij de
> vorige. Bij 7 bots komt daar dus één tafel van **7** uit — ruimer dan de
> engine bedoelt. Het draait en de chips kloppen, maar 7-handed poker is
> tighter dan de 6-max van het echte toernooi. Het script waarschuwt hiervoor.

## Aan een volle tafel (240 tafels per bot)

| bot | gem. eindstack | ruis (sd) | onzekerheid | gem. plek | % tafels 1e | % tafels op 0 |
|---|---|---|---|---|---|---|
| inzetgrootte | 1512 | 1537 | 99 | 1,8 | 27% | 31% |
| bluffer | 1362 | 1285 | 83 | 2,0 | 25% | 23% |
| handsterkte | 973 | 1306 | 84 | 3,9 | 18% | 50% |
| allrounder | 943 | 774 | 50 | 4,2 | 5% | 17% |
| uitbuiter | 894 | 985 | 64 | 4,5 | 11% | 32% |
| tafellezer | 729 | 635 | 41 | 5,5 | 1% | 14% |
| potodds | 587 | 1241 | 80 | 6,2 | 14% | 73% |

Gepaard per tafel (chips zijn zero-sum, dus ongepaard overschat je de ruis).
Met 21 vergelijkingen tegelijk is |t| > 3,0 pas overtuigend:

- **Twee koplopers, niet van elkaar te onderscheiden.** `inzetgrootte` vs
  `bluffer`: −150, t = −1,1. Beide verslaan de rest hard.
- **Een middengroep van drie die volledig samenvalt.** `handsterkte`,
  `allrounder` en `uitbuiter` liggen binnen 80 chips van elkaar (t = −0,3 tot
  0,7). Daar is geen rangorde in.
- `bluffer` vs `handsterkte` is een grensgeval (+389, t = 2,9).
- `potodds` is de duidelijke laatste, `tafellezer` niet van hem te
  onderscheiden (−141, t = −1,6).

## Kop-op-kop (21 paren, 120 tafels per paar, 1000 = gelijkspel)

Gemiddeld over al zijn tegenstanders:

| bot | gemiddeld | bot | gemiddeld |
|---|---|---|---|
| bluffer | +192 | tafellezer | −29 |
| inzetgrootte | +167 | handsterkte | −228 |
| uitbuiter | +152 | allrounder | −300 |
| potodds | +46 | | |

De rangorde verandert dus wél tussen de twee opzetten, en op een manier die
klopt: `allrounder` en `handsterkte` zijn te tight om kop-op-kop elke hand te
spelen, terwijl `uitbuiter` van de derde plaats aan een volle tafel naar bijna
de top schuift. Het grootste enkele verschil in de hele matrix is
`uitbuiter` − `handsterkte` = **+617**.

## Wat de drie nieuwe bots opleverden

**`bot_bluffer` is tweede geworden door bijna niet te bluffen.** Zijn bluf-tak
is bereikbaar in 2% van zijn beslissingen en hij vuurt bij maar 3,5% van zijn
verhogingen. Dat is geen bug: zijn eigen rekensom weigert de bluf zodra die te
vaak zou moeten lukken (gemeten: van de 10,2% beslissingen met bluf-materiaal
wordt 5,5 procentpunt door precies die eis geblokkeerd). Waar hij het van
wint, is discipline: hij foldt maar 17% van al zijn beslissingen, checkt 24%,
en zijn `grote_raise` levert **+473 chips per hand** op — de hoogste van het
veld, omdat hij die alleen met zijn top gebruikt.

**`bot_allrounder` laat zien dat vier correcties samen te veel zijn.** Elk
ingrediënt is los verdedigbaar, maar opgeteld speelt hij nog 25% van zijn
handen en foldt hij 90% van de klasse 45-55. Hij is de enige bot die geld
verliest op zijn eigen `raise` (−2,2 per hand over 1373 raises). Zijn
`grote_raise` is uitstekend (+244) maar komt 170 keer voor. Aan een volle tafel
levert die tightness nog een middenpositie op; kop-op-kop is hij laatste.
Knoppen om te draaien: `KLEIN_VOORDEEL` (nu 8) en `MINIMUM_TEGENSTANDERS`.

**`bot_uitbuiter` werkt, maar alleen één-tegen-één.** Zijn hele opzet hangt aan
één gemeten getal, en dat getal had ik eerst fout:

| | foldkans tegen een raise van 200 |
|---|---|
| over alle 91 handen | 76% |
| **alleen over de handen waarmee een bot preflop meedoet** | **60%** |

Je steelt niet van alle handen — je steelt van iemand die al in de pot zit, en
dat is een selectie van zijn *sterkere* handen. Met 0,82 stal deze bot in
potten waar het niet loonde; met de conditionele 0,60 gaat de drempel van pot
44 naar pot 133 heads-up, naar 356 tegen twee spelers, en tegen drie loont het
vrijwel nooit. Die correctie was aan de volle tafel +188 chips waard en tilde
zijn `grote_raise` van +31 naar +106 per hand. Bluffen is een heads-up wapen,
en dat is precies wat de kop-op-kop-matrix laat zien.

En de mooiste uitkomst van die meting: **`bot_handsterkte` foldt 0% van zijn
meespeel-handen tegen een grote raise.** Niet uit moed, maar omdat
`inzet_om_te_callen` niet in zijn signatuur staat. Wie je inzet niet kán zien,
kan er niet door weggeduwd worden — de simpelste bot van het veld is immuun
voor de hele opzet van de uitbuiter. Zijn tegengif is `potodds`: een bot die
te veel callt, verslaat een bot die van folds leeft (`uitbuiter` verliest 344
chips per tafel van hem).

## Vier dingen die je uit de kolommen alleen niet ziet

1. **"fold" in het hand-log betekent ook "kon niets kiezen".** Het log schrijft
   `eerste_actie or "fold"`. Een bot op 0 chips blijft elke hand een regel
   schrijven, en wie niet aan de beurt kwam (iedereen foldde naar zijn blind)
   krijgt ook "fold" — terwijl hij die hand juist won. Bij `potodds` is 46% van
   zijn regels een hand waarin hij al uitgespeeld was. Ongecorrigeerd meet je
   hem als tight terwijl hij losgespeeld en afgebrand is.
2. **`tegenstander_acties_deze_hand` loopt over alle straten van een hand** en
   wordt niet per straat leeggemaakt. Gemeten: in **35%** van de beslissingen
   staat er een raise in de lijst terwijl niemand *net* verhoogde. Wie alleen
   op "is er geraised?" test, foldt vanaf de flop bijna alles. Dit heeft drie
   van deze zeven bots geraakt voordat het gerepareerd was; ze kijken nu allemaal
   naar de laatste actie. Restprobleem: de acties hebben geen straat-label, dus
   welke raise van *deze* straat is, is uit de data niet te halen.
3. **`ronde` krijg je alleen als je het vraagt.** Vier van deze zeven hebben
   `ronde` niet in hun signatuur en kunnen preflop dus niet van river
   onderscheiden — terwijl de winkans-tabel *preflop*-informatie is.
4. **De tabel is kop-op-kop.** Aan tafel moet je van iedereen winnen, en dat
   scheelt enorm: A-A is tegen 1 speler 85%, tegen 3 spelers 64% en tegen 5
   spelers 50%. 7-2 gaat van 34% naar 14% naar 9%. Zes van de zeven bots
   vergelijken die kop-op-kop-getallen met absolute drempels en met pot-odds in
   procenten. Alleen `bot_allrounder` rekent om, en alleen voor de call-vraag.

## Bekende zwaktes, gemeten en niet weggepoetst

- **`bot_potodds` is de zwakste bot, en je ziet precies waarom.** Hij doet met
  77% van zijn handen mee en verliest **34 chips per call** over 2846 calls.
  Dat is de naïeve-pot-odds-val: bij een kleine inzet zegt de rekensom bijna
  altijd "call", omdat 7-2 met "34% winkans" een prijs van 17% lijkt te
  verslaan — terwijl die hand tegen drie spelers 14% waard is. Hij brandt op
  73% van de tafels af.
- **`bot_potodds`: `bluf_kans` is bijna dode code**, bereikbaar in ~1% van zijn
  beslissingen. Oorzaak is `BLUF_POT_MIN = 120`; de sprong zit tussen 40 en 30,
  want de preflop-pot is precies 30 chips (blind 10 + 20):

  | `BLUF_POT_MIN` | 120 | 60 | 40 | 30 | 20 | 0 |
  |---|---|---|---|---|---|---|
  | bluf-tak bereikbaar | 0,9% | 1,1% | 2,0% | 8,2% | 8,2% | 8,2% |

- **`bot_handsterkte` bluft nooit en checkt nooit.** Dat is het idee (hij kent
  `inzet_om_te_callen` niet), maar zijn spel is daardoor volledig uit de kolom
  `hand` af te lezen: 100% fold onder winkans 45, 0% fold boven 55. Hij eindigt
  op 50% van de tafels op nul.
- **`bot_inzetgrootte` zet 200 in op de river op basis van een starthand-tabel.**
  Hij kent `ronde` niet. Dat hij bovenaan staat komt van zijn preflop-agressie
  (`grote_raise` levert +135 per hand op), niet van zijn river-spel.
- **`bot_tafellezer` raist 25% van zijn handen voor +6 chips per raise.** Zijn
  agressie betaalt zich niet: hij min-raist zijn goede handen (geen
  sizing-begrip) en haalt uit top-handen 51 chips waar `inzetgrootte` er 255
  uithaalt. Laagste ruis van het veld op één na — hij verliest zelden groot,
  maar wint ook nooit (1% van de tafels eerste).
- Kleinigheid: 7 van 240 tafels tellen op tot 6990 in plaats van 7000. Tien
  chips verdwijnen ergens in PyPokerEngine. Irrelevant voor de uitslag, maar de
  chip-controle laat het zien.

## Over de meet-tooling zelf

`scripts/vergelijk_mijn_bots.py` bevat een diagnose die per bot uitrekent of
zijn bluf-tak bereikbaar is: dezelfde situatie ook doorrekenen met
`bluf_kans = 0.0` en met `bluf_kans = 1.0`. Twee dingen daaraan zijn zelf een
les geweest:

1. Die extra aanroepen trekken `random()` leeg, en de bots delen één globale
   generator met de engine. Zonder `random.getstate()`/`setstate()` meet je een
   ánder spel dan er zonder diagnose gespeeld zou zijn — dat scheelde een factor
   4 in het aantal bereikbare bluf-momenten.
2. `bluf_kans = 1.0` betekent niet "bluft altijd" als de bot die kans intern
   opschaalt (`bot_bluffer` maal `STRAAT_FACTOR`, preflop 0,3). Daarom wordt
   `random()` tijdens die ene meting op 0 vastgezet.

De diagnose controleert bovendien of een bot op `bluf_kans = 0` écht
deterministisch is. Dat vond een echte bug: `bot_uitbuiter` stond op
`0.55 + bluf_kans` en stal op nul dus nog 55% van de tijd. Een knop die op nul
niet uit staat, is geen knop.
