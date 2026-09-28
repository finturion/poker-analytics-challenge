# Wat je bot binnenkrijgt, en wat niet

Uitgelezen uit `api/poker_adapter.py` (`roep_student_bot_aan`) en
`api/bot_validator.py`. Verandert daar iets, dan hoort dit mee te veranderen.

## De parameters

Je krijgt een parameter **alleen als je hem zelf in je functie opschrijft**, en
de naam moet exact kloppen. De engine kijkt naar je handtekening en geeft je wat
hij herkent. Spel je er een verkeerd, dan krijg je hem niet — zonder foutmelding.

| parameter | vanaf | wat erin zit | voorbeeld |
|---|---|---|---|
| `hand` | week 1 | je twee kaarten, **zonder kleur** | `['A', 'K']` |
| `stack` | week 3 | je eigen chips | `1000` |
| `ronde` | week 3 | welke straat | `'preflop'` `'flop'` `'turn'` `'river'` |
| `pot` | week 3 | wat er in de pot zit | `120` |
| `inzet_om_te_callen` | week 3 | wat meedoen kost; `0` is gratis | `200` |
| `tegenstander_acties_deze_hand` | week 3 | wat anderen deden, deze hand | zie hieronder |
| `bord` | week 5 | de kaarten op tafel, **met kleur** | `['D4', 'C9', 'HT']` |
| `hand_met_kleur` | week 5 | je eigen twee, **met kleur** | `['SA', 'HK']` |
| `bluf_kans` | week 5 | je eigen getal, 0 tot 1 | `0.15` |

`strategie` is er in september 2026 uit gehaald: je koos je eigen label en kreeg
het daarna zelf weer terug, en niets anders las het. Een bot die hem nog in zijn
handtekening heeft krijgt hem nog steeds, dus er breekt niets.

`hand` blijft in week 5 wat hij was: twee rangen zonder kleur. De kleuren komen
apart binnen, in `hand_met_kleur`. Dat is met opzet — anders zou elke bot uit
week 1 en 3 breken die `hand[0] == hand[1]` doet of een rang opzoekt in een lijst.

Preflop is `bord` een **lege lijst**, niet `None`. Je hoeft dus geen onderscheid
te maken tussen "nog geen bord" en "geen bord gekregen".

Een regel uit `tegenstander_acties_deze_hand`:

```python
{'bot_naam': 'TestBot', 'actie': 'raise', 'bedrag': 200, 'ronde': 'flop'}
```

De lijst loopt over de **hele hand**, niet over deze straat. Filter op `ronde`
als je wilt weten of er op dít moment geraised is; zonder dat filter zag 35% van
de beslissingen een raise die op een eerdere straat viel.

## Wat je teruggeeft

Eén string: `"fold"`, `"call"`, `"raise"`, `"grote_raise"` of `"all_in"`.

- `all_in` en `grote_raise` werken **alleen** als je bot `stack` in zijn
  handtekening heeft. Zonder stack kun je niet afwegen hoeveel je riskeert, dus
  dan doet de engine er niets mee.
- Maximaal **twee raises per straat**. Daarboven wordt je raise een call.
- Crasht je bot of duurt hij langer dan **2 seconden**, dan foldt hij die hand.
  Geen foutmelding, geen uitslag die het verraadt — behalve een fold-percentage
  dat te hoog is.

## Wat je bot NIET weet

- **Hoeveel tegenstanders er nog in de hand zitten.** Je kunt de folds tellen in
  `tegenstander_acties_deze_hand`, maar je weet niet met hoeveel je begon: tafels
  zijn maximaal zes, niet altijd zes.
- De kaarten van anderen.
- De stacks van anderen.
- Wat er in eerdere handen gebeurde. Elke hand begint schoon.

## schat_winkans

```python
schat_winkans(hand, simulaties=1000, seed=None, tegenstanders=1, bord=None)
```

- `tegenstanders` staat standaard op **1**. Aan een tafel van zes moet je 5
  meegeven, anders reken je met een getal dat veel te hoog is.
- Met een `bord` moet je `hand` kleuren hebben. `schat_winkans(['A','K'],
  bord=[...])` weigert: zonder kleur is een flush niet te zien.
- Zonder `seed` krijg je elke aanroep een iets ander getal. Dat is geen fout,
  dat is een Monte Carlo-schatting.

## Het speelveld

50 handen per zitting · 5 zittingen · startstack 1000 · tafels van maximaal 6 ·
big blind 20, small blind 10.
