# Announcement: extra oefenronde + een tweede logboek

_Concepttekst voor Brightspace. Rondenummer 6, geen bonuspunten._

---

## Er staat een extra toernooi klaar

Ik heb vandaag een **extra oefenronde** gedraaid met de bots die op dit moment
zijn ingeleverd. Die telt **niet** mee voor de bonus — alleen het toernooi van
woensdag en dat van donderdag doen dat. Deze is er puur om mee te oefenen: je
kunt zien wat je laatste aanpassing heeft gedaan, zonder dat er iets van afhangt.

**Hoe je hem binnenhaalt:** je hoeft niets te veranderen. Draai de cel in
Werkcollege 8 waarin je het toernooi ophaalt gewoon opnieuw:

```python
response = requests.get(
    f"{API_URL}/toernooi/5",
    params={"student_id": STUDENT_ID},
    headers={"Authorization": f"Bearer {TOKEN}"},
)
resultaat = response.json()
```

Je krijgt automatisch het nieuwste toernooi. Wil je juist dat van woensdag
terugzien — het toernooi waarop de bonus is gebaseerd — zet er dan `"ronde": 1`
bij in `params`.

---

## En er is een tweede logboek bijgekomen

`hand_log` heeft **één regel per hand**: welke kaarten je kreeg, en wat je ermee
deed. Daar kun je veel mee, maar niet alles. Deze vragen kon je er niet mee
beantwoorden:

- Foldde ik op de flop, of pas op de river?
- Wat **lag** er eigenlijk op tafel toen ik raisete?
- Hoeveel kostte het me om te callen — en was dat de pot waard?

Vanaf deze ronde wordt er daarom een tweede logboek bewaard, met **één regel per
beslissing**. Speel je een hand tot het einde uit, dan zijn dat er vier.

```python
respons = requests.get(
    f"{API_URL}/toernooi/5/uitgebreid",
    params={"student_id": STUDENT_ID},
    headers={"Authorization": f"Bearer {TOKEN}"},
)
uitgebreid = respons.json()

beslissingen = pd.DataFrame(uitgebreid["regels"])
print(len(beslissingen), "beslissingen")
```

Wat erin staat:

| kolom | wat het is |
|---|---|
| `ronde` | `preflop`, `flop`, `turn` of `river` |
| `bord` | de kaarten op tafel op dat moment (leeg bij preflop) |
| `pot` | wat er in de pot zat toen jij moest kiezen |
| `inzet_om_te_callen` | wat meedoen je zou kosten |
| `stack` | wat je op dat moment nog had |
| `tegenstanders_actief` | hoeveel spelers er nog in de hand zaten |
| `gekozen` | wat jouw functie teruggaf |

Je krijgt **alleen je eigen regels**. Niet uit geheimzinnigheid: voor de hele
klas zijn het er ruim honderdduizend, en dat wil je niet in je notebook laden.

**Let op bij `gekozen`.** Dat is wat jouw functie zei, *vóór* de raise-cap van de
engine. Staat daar `raise` terwijl `hand_log` `call` zegt, dan is je raise
tegengehouden omdat er in die straat al genoeg verhoogd was — niet omdat je eigen
logica iets anders koos. Hoe vaak dat gebeurt, is op zichzelf al interessant.

Dit logboek bestaat **alleen voor deze oefenronde en alles daarna**. Vraag je het
op voor het toernooi van woensdag, dan krijg je `beschikbaar: false` terug — toen
werd het nog niet bewaard.

---

## Wat je ermee kunt

In Werkcollege 8 staat hier nu **3.6** over, met een opzetje. Twee vragen om mee
te beginnen:

**Hoe ver kom je per hand?** Tel je beslissingen per ronde. Staan er bijna geen
regels op `turn` en `river`, dan fold je vroeg — veilig, maar je wint ook nooit
een grote pot. Staan er juist véél, dan betaal je vaak door op handen die je
misschien eerder had moeten laten gaan.

**Wat kostte callen je?** `inzet_om_te_callen / (pot + inzet_om_te_callen)` is het
deel van de pot dat je moet betalen om mee te doen. Moet je 20 betalen in een pot
van 180, dan is dat 10% — en dan hoeft je hand maar in 10% van de gevallen de
beste te zijn om dat lonend te maken. Reken die kolom uit en kijk per ronde naar
het gemiddelde van de keren dat je callde. Betaal je op de river gemiddeld een
veel groter deel van de pot dan preflop? Dat is precies het soort hand waar geld
weglekt.
