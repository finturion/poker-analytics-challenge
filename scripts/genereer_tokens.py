"""
Genereert per studentnummer een uniek, willekeurig token voor de Poker
Analytics Challenge API.

Gebruik:
    python genereer_tokens.py studentnummers.txt

studentnummers.txt: een gewoon tekstbestand, één studentnummer per regel.

Output (beide in dezelfde map als dit script, niet in de repo committen):
- tokens.json                    -> plak de inhoud in de POKER_TOKENS_JSON env var op Render
- tokens_voor_verspreiding.csv   -> studentnummer,token — stuur elke rij individueel door

Elke student krijgt een eigen token. Dat is geen willekeurige keuze: het
studentnummer in de URL (bv. /submit/12345678) wordt door de student zelf
opgegeven — de token is het enige dat controleert of iemand ook echt is wie
hij zegt te zijn. Bij één gedeeld token kan elke student zich voordoen als
een klasgenoot.
"""
import csv
import json
import secrets
import sys


def genereer(studentnummers):
    if len(studentnummers) != len(set(studentnummers)):
        dubbel = {n for n in studentnummers if studentnummers.count(n) > 1}
        print(f"Let op: dubbele studentnummers in het bestand: {sorted(dubbel)}")

    return {nummer: secrets.token_urlsafe(12) for nummer in studentnummers}


def main():
    if len(sys.argv) != 2:
        print("Gebruik: python genereer_tokens.py studentnummers.txt")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        studentnummers = [regel.strip() for regel in f if regel.strip()]

    tokens = genereer(studentnummers)

    with open("tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)

    with open("tokens_voor_verspreiding.csv", "w", newline="") as f:
        schrijver = csv.writer(f)
        schrijver.writerow(["studentnummer", "token"])
        for nummer, token in tokens.items():
            schrijver.writerow([nummer, token])

    print(f"{len(tokens)} tokens gegenereerd.")
    print("- tokens.json: plak de inhoud in de POKER_TOKENS_JSON env var op Render.")
    print("- tokens_voor_verspreiding.csv: stuur elke rij individueel door (bv. via Canvas/Brightspace), nooit klassikaal delen.")


if __name__ == "__main__":
    main()
