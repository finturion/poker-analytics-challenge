"""
Haalt elke gedraaide ronde van een week op en bewaart ze als JSON.

    export POKER_DOCENT_TOKEN='...'
    python3 scripts/haal_rondes_op.py --week 3

Gebruikt /toernooi/{week}/resultaat, dat NOOIT een toernooi start -- je kunt dit
dus veilig draaien zonder dat je per ongeluk een uitslag overschrijft die de klas
al gezien heeft. Rondes die nog niet gedraaid zijn meldt hij en slaat hij over.

Per ronde print hij of de bots schoon op 1000 begonnen of met chips uit de vorige
ronde. Dat laatste hoort alleen in de bonusweek; zie je het in week 3, dan is die
ronde niet te vergelijken met ronde 1.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("POKER_API_URL", "https://poker-analytics-api.onrender.com")


def haal(week, ronde, token):
    verzoek = urllib.request.Request(
        f"{API_URL}/toernooi/{week}/resultaat?ronde={ronde}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(verzoek, timeout=120) as antwoord:
            return json.load(antwoord)
    except urllib.error.HTTPError as fout:
        if fout.code in (401, 403):
            sys.exit("Token afgekeurd. Staat POKER_DOCENT_TOKEN goed in je omgeving?")
        return None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week", type=int, default=3)
    p.add_argument("--tot", type=int, default=8, help="hoogste ronde om te proberen")
    p.add_argument("--map", default=".", help="waar de bestanden komen")
    args = p.parse_args()

    token = os.environ.get("POKER_DOCENT_TOKEN")
    if not token:
        sys.exit("Zet POKER_DOCENT_TOKEN in je omgeving.")

    gevonden = []
    for ronde in range(1, args.tot + 1):
        uitslag = haal(args.week, ronde, token)
        if not uitslag or not uitslag.get("gedraaid", True) or not uitslag.get("hand_log"):
            print(f"  ronde {ronde}: niet gedraaid")
            continue
        pad = os.path.join(args.map, f"toernooi_w{args.week}r{ronde}.json")
        with open(pad, "w", encoding="utf-8") as bestand:
            json.dump(uitslag, bestand, ensure_ascii=False)
        stacks = uitslag.get("startstacks")
        start = "schoon op 1000" if not stacks else (
            f"doorgespeeld, van {min(stacks.values())} tot {max(stacks.values())}")
        print(f"  ronde {ronde}: {uitslag.get('n_bots')} bots · "
              f"{len(uitslag['hand_log'])} logregels · {start} -> {pad}")
        gevonden.append(ronde)

    if not gevonden:
        sys.exit("Geen enkele ronde gedraaid in deze week.")
    print(f"\nHoogste gedraaide ronde: {max(gevonden)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
