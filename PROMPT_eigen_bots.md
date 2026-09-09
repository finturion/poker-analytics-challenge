# Prompt: vier eigen pokerbots bouwen en vergelijken

Kopieer alles onder de streep naar een nieuwe chat.

---

Ik wil vier verschillende pokerbots bouwen voor de Poker Analytics Challenge en
zien hoe ze tegen elkaar spelen. Het project staat hier:

```
/Users/jerome/Library/Mobile Documents/com~apple~CloudDocs/Full_Stack_dev/HvA_voorbereidingen/IDS_2026_2027_SEM1/Poker_Analytics_2026
```

## Lees eerst de contracten na

Vertrouw onderstaande samenvatting niet blind — lees `api/poker_adapter.py` en
`api/bot_validator.py` en corrigeer me als iets niet klopt. In
`notebooks/_docent_voorbeeldbots.ipynb` en `notebooks/_docent_bot_v2.py` /
`_docent_bot_v3.py` staan uitgewerkte voorbeelden.

## Hoe een bot eruitziet

Een bot is één functie. **De engine kiest zijn argumenten op parameternaam**, dus
de namen moeten exact kloppen — noem je ze anders, dan wordt de functie zonder
argumenten aangeroepen, crasht hij, en foldt je bot stil elke hand. Je zet alleen
de parameters in je signatuur die je echt gebruikt:

| parameter | wat erin zit |
|---|---|
| `hand` | twee kaartwaarden als strings: `["A", "10"]`. Waarden: `A K Q J 10 9 8 7 6 5 4 3 2` — let op, **`"10"` en niet `"T"`** |
| `stack` | je eigen chips op dit moment |
| `ronde` | `"preflop"`, `"flop"`, `"turn"` of `"river"` |
| `pot` | wat er in de pot zit |
| `inzet_om_te_callen` | wat je moet bijleggen om mee te doen |
| `tegenstander_acties_deze_hand` | lijst van `{"bot_naam", "actie", "bedrag"}` van wat anderen deze hand deden |
| `strategie` | `"tight"`, `"loose"`, `"balanced"` of `"aggressive"` |
| `bluf_kans` | getal tussen 0.0 en 1.0 |

Je geeft een string terug. Vanaf Bot v3 (week 5) mag je kiezen uit:

| actie | wat de engine doet |
|---|---|
| `"fold"` | passen |
| `"call"` / `"check"` | meegaan |
| `"raise"` | verhogen met het **wettelijke minimum** — mediaan 40 chips, twee big blinds |
| `"grote_raise"` | verhogen naar **200 chips** (tien big blinds), teruggetrokken naar het toegestane bereik als dat niet past |
| `"all_in"` | alles inzetten |

Spelregels die je moet weten:

- **Maximaal 2 raises per straat** per bot. Een derde poging wordt stil een `call`.
  `grote_raise` telt daarvoor even zwaar als `raise`.
- `"grote_raise"` en `"all_in"` werken alleen als je respectievelijk `strategie`
  en `stack` in je signatuur hebt staan. Dat is de gate.
- Crasht je functie of duurt hij langer dan 2 seconden, dan foldt de bot die hand
  en draait het toernooi door. Je merkt er dus niets van behalve slechte resultaten.
- Tafels van maximaal 6 bots, iedereen begint op 1000 chips, small blind 10.

## Wat ik van je wil

**1. Vier bots met een duidelijk verschillend idee.** Niet vier keer dezelfde bot
met een andere drempel — vier verschillende *ideeën*. Denk aan: puur op
handsterkte, pot-odds-gedreven, reagerend op wat tegenstanders deden, of eentje
die bewust met inzetgrootte speelt. Zet ze in losse bestanden met een korte
comment bovenaan die het idee uitlegt.

**2. Laat ze tegen elkaar spelen** met `speel_toernooi` uit `api/poker_adapter.py`:

```python
import sys; sys.path.insert(0, "api")
from poker_adapter import speel_toernooi

bots = {
    "naam": {"kies_actie": mijn_functie, "strategie": "tight", "bluf_kans": 0.2},
    ...
}
uitslag = speel_toernooi(bots, n_simulaties=20, n_handen=50, seed=51)
uitslag["eindstand_per_bot"]   # gemiddelde eindstack per bot
uitslag["hand_log"]            # elke hand van elke bot
```

**Gebruik minstens 20 simulaties.** De ruis op één bot is 500 tot 800 chips
gemeten; met 5 simulaties meet je vooral toeval. Draai het ook met **meerdere
seeds** en laat me zien hoe stabiel de uitslag is — niet één run met een winnaar.
`scripts/meet_toernooi_variantie.py` doet dat al voor een testveld; kijk daar hoe.

**3. Laat zien hoe ze spelen, niet alleen wie won.** Uit `hand_log` (kolommen
`bot_naam`, `hand_nummer`, `hand`, `actie`, `stack`, `tafel`, `simulatie`) kun je
per bot halen:

- de verdeling van zijn acties (hoe vaak foldt hij, hoe vaak zet hij groot in)
- met wélke handen hij meedeed — de kolom `hand` maakt zijn drempel leesbaar
- wat elke actie hem gemiddeld opleverde (`groupby("simulatie")["stack"].diff()`
  geeft de winst per hand; let op die groupby, anders rekent `diff` over de grens
  van een simulatie door)

**4. Zeg me eerlijk wat je ziet.** Als het verschil tussen twee bots kleiner is
dan de ruis, zeg dat dan in plaats van een winnaar aan te wijzen. En als een bot
onbedoeld iets doet — altijd folden, nooit bluffen omdat zijn drempel dat
uitsluit — wil ik dat weten.

**5. Check ze door de echte validator** met `valideer_bot_code` uit
`api/bot_validator.py`, week 5, zodat ik weet dat ze ook echt ingeleverd zouden
kunnen worden.

Daarna wil ik zelf aan de knoppen kunnen draaien, dus houd de bots kort en
leesbaar en zet de getallen die iets doen bovenaan als constanten.
