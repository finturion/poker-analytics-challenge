# -*- coding: utf-8 -*-
"""
De uitwerkingen van week 1.

Per notebook een lijst van {zoek, vervang}: `zoek` moet in precies één cel
van het studentnotebook voorkomen, `vervang` is de hele nieuwe celinhoud.
Komt `zoek` er niet meer in voor, dan stopt de generator -- dan is het
notebook veranderd en moet de uitwerking mee.
"""

WERKCOLLEGE1 = [
    {
        "zoek": '# A. jouw variabelen',
        "vervang": '# A. jouw variabelen\nnaam = "Jerome"\naantal_chips = 1000\ninzet = 12.50\nspeelt_mee = True',
    },
    {
        "zoek": '# B. check de types',
        "vervang": '# B. check de types\nfor waarde in (naam, aantal_chips, inzet, speelt_mee):\n    print(f"{str(waarde):<10s} {type(waarde).__name__}")',
    },
    {
        "zoek": '# A. kaartwaarden',
        "vervang": '# A. kaartwaarden\nkaartwaarden = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]\n\n# B. kleuren\nkleuren = ["harten", "ruiten", "klaveren", "schoppen"]\n\nprint(len(kaartwaarden), "waarden en", len(kleuren), "kleuren ->",\n      len(kaartwaarden) * len(kleuren), "kaarten")',
    },
    {
        "zoek": '# A. eerste en laatste waarde',
        "vervang": '# A. eerste en laatste waarde\nprint("eerste:", kaartwaarden[0])\nprint("laatste:", kaartwaarden[-1])\n\n# B. slice van prentkaarten\n# J, Q en K staan achteraan, vlak voor de aas.\nprentkaarten = kaartwaarden[-4:-1]\nprint("prentkaarten:", prentkaarten)',
    },
    {
        "zoek": 'kaart1 = "A"',
        "vervang": 'kaart1 = "A"\nkaart2 = "A"\n\nif kaart1 == kaart2:\n    print("Een paar!")\nelif kaart1 in prentkaarten or kaart2 in prentkaarten:\n    print("Een prentkaart erbij.")\nelse:\n    print("Niets bijzonders.")',
    },
    {
        "zoek": '# A. enumerate over kaartwaarden',
        "vervang": '# A. enumerate over kaartwaarden\n# enumerate geeft de plek én de waarde, dus je hoeft geen eigen teller bij te houden.\nfor plek, waarde in enumerate(kaartwaarden):\n    print(plek, waarde)',
    },
    {
        "zoek": 'voorbeeld_kaarten = ',
        "vervang": 'voorbeeld_kaarten = ["A", "K", "A", "7", "A", "2", "J", "A", "9", "A"]\n\n# B. tel de azen met een for-loop\naantal_azen = 0\nfor kaart in voorbeeld_kaarten:\n    if kaart == "A":\n        aantal_azen += 1\n\nprint("azen:", aantal_azen)',
    },
    {
        "zoek": '# for-loop + if door voorbeeld_kaarten',
        "vervang": '# for-loop + if door voorbeeld_kaarten\nfor kaart in voorbeeld_kaarten:\n    if kaart == "A":\n        print(kaart, "-> aas")\n    elif kaart in prentkaarten:\n        print(kaart, "-> prentkaart")\n    else:\n        print(kaart, "-> gewone kaart")',
    },
    {
        "zoek": '# jouw if/elif/else hier\n    pass',
        "vervang": 'def kies_actie(hand):\n    """hand: lijst met 2 kaartwaarden, bv. [\'A\', \'K\']. Geeft \'raise\', \'call\' of \'fold\' terug."""\n    # De regel uit Stap 2, in dezelfde volgorde als daar beschreven. De volgorde\n    # is niet vrijblijvend: A-A en K-K worden al door de eerste tak gevangen, dus\n    # de call-tak ziet alleen de láágere paren.\n    if "A" in hand or "K" in hand:\n        return "raise"\n    if hand[0] == hand[1]:\n        return "call"\n    return "fold"\n\n\nkies_actie([\'A\', \'K\'])  # test',
    },
    {
        "zoek": '# TODO: schrijf kies_actie_streng(hand)',
        "vervang": '# Verdieping: twee bots naast elkaar.\n#\n# "Strenger" betekent hier: minder handen spelen. Alleen een paar azen is sterk\n# genoeg om te verhogen, één hoge kaart mag meedoen, en de rest gaat weg.\n\n\ndef kies_actie_streng(hand):\n    """Voorzichtiger dan kies_actie: alleen azen verhogen, hoge kaart callen."""\n    if hand[0] == hand[1] == "A":\n        return "raise"\n    if "A" in hand or "K" in hand:\n        return "call"\n    return "fold"\n\n\ndef tel_acties(bot, handen):\n    """Hoe vaak kiest deze bot elke actie? Geeft percentages terug."""\n    aantallen = {"raise": 0, "call": 0, "fold": 0}\n    for hand in handen:\n        aantallen[bot(hand)] += 1\n    return {actie: aantal / len(handen) * 100 for actie, aantal in aantallen.items()}\n\n\nmijn = tel_acties(kies_actie, alle_handen)\nstreng = tel_acties(kies_actie_streng, alle_handen)\n\nprint(f"{\'\':8s}{\'jouw bot\':>12s}{\'streng\':>12s}")\nfor actie in ("raise", "call", "fold"):\n    print(f"{actie:8s}{mijn[actie]:>11.1f}%{streng[actie]:>11.1f}%")',
    },
    {
        "zoek": '# kopieer hier exact de logica',
        "vervang": '%%writefile mijn_bot_week1.py\ndef kies_actie(hand):\n    """hand: lijst met 2 kaartwaarden, bv. [\'A\', \'K\']. Geeft \'raise\', \'call\' of \'fold\' terug."""\n    if "A" in hand or "K" in hand:\n        return "raise"\n    if hand[0] == hand[1]:\n        return "call"\n    return "fold"',
    },
    {
        "zoek": 'titel="vul hier een echte actietitel in"',
        "vervang": 'with open("mijn_bot_week1.py") as f:\n    bot_code = f.read()\n\nchart_info = export_chart_info(\n    fig,\n    # Een actietitel noemt het inzicht, niet de variabelen. "Kaartwaarden" zegt\n    # alleen wat er op de as staat; dit zegt wat je in de grafiek ziet.\n    titel="Elke kaartwaarde komt even vaak voor — precies wat je van 10.000 trekkingen verwacht",\n    x_label="Kaartwaarde",\n    y_label="Aantal keer getrokken",\n    library="matplotlib",\n)',
    },
]

WERKCOLLEGE2 = [
    {
        "zoek": 'volgorde = []',
        "vervang": """# B, E, D, G, F, H, A, C
#
# Eerst de kaarten (B) en de 10.000 handen (E), want zonder data valt er niets
# te kiezen. Dan de bot (D), dan de grafiek (G). Pas daarna het inleverspoor:
# de bot in een los bestand (F), de hulpfuncties en je token (H), chart_info (A),
# en als laatste lever_in (C) -- die heeft alle drie de vorige nodig.
volgorde = ["B", "E", "D", "G", "F", "H", "A", "C"]
print(volgorde)""",
    },
    {
        "zoek": '# jouw gefixte versie hier',
        "vervang": """def kies_actie_gefixt(hand):
    # De bug zat in de volgorde, niet in de regels zelf. Een paar azen voldoet
    # aan allebei de voorwaarden, dus wie het eerst staat wint -- en de bedoeling
    # was dat een hoge kaart voorrang krijgt.
    if "A" in hand or "K" in hand:
        return "raise"
    if hand[0] == hand[1]:
        return "call"
    return "fold"


kies_actie_gefixt(["A", "A"])  # moet nu "raise" geven""",
    },
    {
        "zoek": '# TODO: geef "twee_hoog" terug bij 2 hoge kaarten',
        "vervang": '# Deze uitwerking moet op zichzelf draaien, ook als je Werkcollege 1 niet net\n# hebt uitgevoerd. Vandaar dat alle_handen hier opnieuw wordt gemaakt; in je\n# eigen notebook staat hij al van maandag.\nimport random\n\nkaartwaarden = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]\nalle_handen = [random.sample(kaartwaarden, 2) for _ in range(10_000)]\n\nHOOG = ["A", "K", "Q", "J", "10"]\n\ndef hand_soort(hand):\n    """Geeft \'paar\', \'twee_hoog\', \'een_hoog\' of \'laag\' terug."""\n    if hand[0] == hand[1]:\n        return "paar"\n\n    aantal_hoog = 0\n    for kaart in hand:\n        if kaart in HOOG:\n            aantal_hoog += 1\n\n    # Drie gevallen, dus drie takken. De volgorde maakt hier niet uit, want\n    # aantal_hoog is precies 0, 1 of 2.\n    if aantal_hoog == 2:\n        return "twee_hoog"\n    if aantal_hoog == 1:\n        return "een_hoog"\n    return "laag"\n\n\nfor hand in [["A", "A"], ["A", "K"], ["K", "7"], ["7", "2"]]:\n    print(hand, "->", hand_soort(hand))',
    },
    {
        "zoek": '# TODO: beslis per handsoort. Denk aan de telling uit Stap 1',
        "vervang": 'def kies_actie(hand):\n    """hand: lijst met 2 kaartwaarden. Geeft \'raise\', \'call\' of \'fold\' terug."""\n    soort = hand_soort(hand)\n    # De telling uit Stap 1 liet zien dat de bot twee van de drie handen weggooit.\n    # Dat is een keuze, geen natuurwet. Hieronder spelen paren en twee hoge\n    # kaarten stevig, één hoge kaart voorzichtig, en de rest gaat weg.\n    if soort == "paar":\n        return "raise"\n    if soort == "twee_hoog":\n        return "raise"\n    if soort == "een_hoog":\n        return "call"\n    return "fold"\n\n\n# tel opnieuw over je 10.000 handen -- is de verdeling nu zoals je wil?\naantal_raise = aantal_call = aantal_fold = 0\nfor hand in alle_handen:\n    actie = kies_actie(hand)\n    if actie == "raise":\n        aantal_raise += 1\n    elif actie == "call":\n        aantal_call += 1\n    else:\n        aantal_fold += 1\n\nprint("raise:", round(aantal_raise / len(alle_handen) * 100, 1), "%")\nprint("call: ", round(aantal_call / len(alle_handen) * 100, 1), "%")\nprint("fold: ", round(aantal_fold / len(alle_handen) * 100, 1), "%")',
    },
    {
        "zoek": '"focal_point_opmerking": "vul hier je toelichting in"',
        "vervang": 'review = {\n    "week": 1,\n    "anon_id": gekozen["anon_id"],\n    "focal_point_score": 4,\n    "focal_point_opmerking": (\n        "Mijn oog gaat eerst naar de hoogste staaf, en daar zit het verhaal ook. "\n        "Wel staan alle staven in dezelfde kleur, dus die ene springt er niet uit."\n    ),\n    "kleur_contrast_score": 3,\n    "kleur_contrast_opmerking": (\n        "De kleuren zijn goed te onderscheiden, maar ze dragen geen betekenis: "\n        "de volgorde blijkt al uit de as. Een kleur met een accent op wat je wil "\n        "laten zien is rustiger."\n    ),\n    "actietitel_score": 2,\n    "actietitel_opmerking": (\n        "De titel noemt de variabelen en niet het inzicht. Met een titel die de "\n        "conclusie noemt weet de lezer meteen waar hij naar kijkt."\n    ),\n}\n\nresponse = requests.post(\n    f"{API_URL}/peer-review/{STUDENT_ID}",\n    json=review,\n    headers={"Authorization": f"Bearer {TOKEN}"},\n)\nprint(response.status_code, response.json())',
    },
]

NOTEBOOKS = {
    "Week1_Werkcollege1.ipynb": WERKCOLLEGE1,
    "Week1_Werkcollege2.ipynb": WERKCOLLEGE2,
}
