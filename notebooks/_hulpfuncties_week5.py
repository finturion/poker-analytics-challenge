"""
Hulpfuncties specifiek voor Week 5 (Werkcollege 7 en 8).

Los van _hulpfuncties.py en _hulpfuncties_week3.py, om dezelfde reden als
toen: studenten hebben die bestanden al gedownload, en een update ervan zou
hen niet bereiken.

Bevat:
- laad_bot(): een kies_actie() uit een .py-bestand halen, met een leesbare
  foutmelding als dat bestand er nog niet is.
- speel_duel() (Werkcollege 7, Deel 7): laat twee van je eigen bots een echt
  heads-up-duel spelen met PyPokerEngine, zodat je thuis al ziet of je nieuwe
  versie daadwerkelijk chips wint van je vorige -- in plaats van te wachten op
  het toernooi van woensdag.

De regels hieronder zijn dezelfde als in het toernooi: elke bot krijgt alleen
de parameters die hij zelf in zijn functie opschrijft, hoogstens twee raises
per straat, en "grote_raise" / "all_in" worden naar een echt bedrag vertaald.
Een duel is daarmee een eerlijke voorspelling -- alleen met twee spelers in
plaats van zes, dus de winkansen liggen hoger dan aan een volle tafel.
"""
import importlib.util
import inspect
import os
import random

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

from _hulpfuncties_week3 import schat_winkans

# PyPokerEngine gebruikt "T" voor Tien; wij gebruiken overal "10" (zie Week 1).
_RANG_VERTALING = {"T": "10"}

MAX_RAISES_PER_STRAAT = 2
GROTE_RAISE_CHIPS = 200
START_STACK = 1000
SMALL_BLIND = 10


def laad_bot(bestandsnaam, functienaam="kies_actie"):
    """
    Haalt kies_actie() uit een .py-bestand naast je notebook.

        bot_v2 = laad_bot("mijn_bot_week3.py")

    Handiger dan `from mijn_bot_week3 import kies_actie`, want Python onthoudt
    een module na de eerste import: pas je het bestand aan, dan blijf je zonder
    kernel-herstart de oude versie gebruiken. Deze functie leest elke keer
    opnieuw van schijf.
    """
    if not os.path.exists(bestandsnaam):
        raise FileNotFoundError(
            f"'{bestandsnaam}' staat niet naast dit notebook. Zet de kies_actie() "
            f"die je zoekt in een bestand met precies die naam, in dezelfde map als "
            f"dit notebook, en draai deze cel opnieuw."
        )
    naam = os.path.splitext(os.path.basename(bestandsnaam))[0]
    spec = importlib.util.spec_from_file_location(naam, bestandsnaam)
    module = importlib.util.module_from_spec(spec)
    # schat_winkans staat klaar VOORDAT het botbestand draait, precies zoals de
    # server het doet (api/winkans.py). Daar mag een bot hem gewoon aanroepen
    # zonder import -- sterker nog, importeren MOET daar niet, want op de server
    # bestaat _hulpfuncties_week3 niet. Zonder deze regel zou een bot die
    # schat_winkans gebruikt hier stukgaan en in het toernooi werken.
    module.__dict__.setdefault("schat_winkans", schat_winkans)
    spec.loader.exec_module(module)
    if not hasattr(module, functienaam):
        raise AttributeError(
            f"'{bestandsnaam}' heeft geen functie {functienaam}(). Wat er wel in "
            f"staat: {', '.join(n for n in dir(module) if not n.startswith('_')) or 'niets'}."
        )
    return getattr(module, functienaam)


def _naar_onze_hand(hole_card):
    return [_RANG_VERTALING.get(kaart[1], kaart[1]) for kaart in hole_card]


class _Duelspeler(BasePokerPlayer):
    """Eén bot aan de duel-tafel. Zelfde argumentregels als het toernooi."""

    def __init__(self, naam, kies_actie, bluf_kans):
        super().__init__()
        self.naam = naam
        self._kies_actie = kies_actie
        self._bluf_kans = bluf_kans
        try:
            self._parameters = set(inspect.signature(kies_actie).parameters)
        except (TypeError, ValueError):
            self._parameters = set()
        self._acties_deze_hand = []
        self._raises_deze_straat = 0
        self._straat = None
        self._namen = {}
        self.acties = []
        self.fouten = []
        self.handen_gespeeld = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        beschikbaar = {
            "hand": _naar_onze_hand(hole_card),
            "stack": self._eigen_stack(round_state),
            "bluf_kans": self._bluf_kans,
            "ronde": round_state.get("street"),
            "pot": round_state.get("pot", {}).get("main", {}).get("amount"),
            "inzet_om_te_callen": next(
                (a["amount"] for a in valid_actions if a["action"] == "call"), None),
            "tegenstander_acties_deze_hand": list(self._acties_deze_hand),
            "bord": list(round_state.get("community_card") or []),
            "hand_met_kleur": list(hole_card),
        }
        argumenten = {n: w for n, w in beschikbaar.items() if n in self._parameters}
        try:
            gekozen = self._kies_actie(**argumenten)
        except Exception as fout:
            # Precies wat het toernooi doet: een crash is een fold, en de rest
            # van het duel gaat door. Maar hier onthouden we hem ook, want thuis
            # wil je juist wél weten dat je bot omvalt.
            melding = f"{type(fout).__name__}: {fout}"
            if melding not in self.fouten:
                self.fouten.append(melding)
            gekozen = "fold"
        if not isinstance(gekozen, str):
            melding = f"gaf {gekozen!r} terug in plaats van een tekst"
            if melding not in self.fouten:
                self.fouten.append(melding)
            gekozen = "fold"
        gekozen = gekozen.lower()

        kent_stack = "stack" in self._parameters
        if kent_stack and gekozen in ("raise", "grote_raise"):
            if self._raises_deze_straat >= MAX_RAISES_PER_STRAAT:
                gekozen = "call"
            else:
                self._raises_deze_straat += 1
        self.acties.append(gekozen)
        return self._naar_geldige_actie(gekozen, valid_actions, kent_stack)

    def _eigen_stack(self, round_state):
        for stoel in round_state["seats"]:
            if stoel["uuid"] == self.uuid:
                return stoel["stack"]
        return None

    @staticmethod
    def _mag_raisen(info):
        bedrag = info["amount"]
        return not (isinstance(bedrag, dict) and bedrag["min"] == -1)

    @classmethod
    def _naar_geldige_actie(cls, gekozen, valid_actions, kent_stack):
        toegestaan = {a["action"]: a for a in valid_actions}

        if kent_stack and gekozen in ("grote_raise", "all_in"):
            info = toegestaan.get("raise")
            if info and cls._mag_raisen(info):
                minimum, maximum = info["amount"]["min"], info["amount"]["max"]
                if gekozen == "all_in":
                    return "raise", maximum
                return "raise", max(minimum, min(GROTE_RAISE_CHIPS, maximum))
            gekozen = "call"

        for optie in (gekozen, "call", "fold"):
            info = toegestaan.get(optie)
            if info is None:
                continue
            if kent_stack and optie == "raise" and not cls._mag_raisen(info):
                continue
            bedrag = info["amount"]
            return optie, bedrag["min"] if isinstance(bedrag, dict) else bedrag

        eerste = valid_actions[0]
        bedrag = eerste["amount"]
        return eerste["action"], bedrag["min"] if isinstance(bedrag, dict) else bedrag

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self._acties_deze_hand = []
        self._namen = {stoel["uuid"]: stoel["name"] for stoel in seats}
        self.handen_gespeeld = round_count

    def receive_street_start_message(self, street, round_state):
        self._raises_deze_straat = 0
        self._straat = street

    def receive_game_update_message(self, new_action, round_state):
        if new_action["player_uuid"] == self.uuid:
            return
        self._acties_deze_hand.append({
            "bot_naam": self._namen.get(new_action["player_uuid"], "onbekend"),
            "actie": new_action["action"],
            "bedrag": new_action["amount"],
            "ronde": self._straat,
        })

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def speel_duel(bot_nieuw, bot_oud, handen=100, seed=1,
               naam_nieuw="Bot v3", naam_oud="Bot week 3",
               bluf_kans_nieuw=0.3, bluf_kans_oud=0.0, stil=False):
    """
    Laat twee van je eigen bots `handen` handen tegen elkaar spelen en print
    de uitslag. Beide beginnen met 1000 chips.

        from _hulpfuncties_week5 import laad_bot, speel_duel

        v3 = laad_bot("mijn_bot_week5.py")
        v2 = laad_bot("mijn_bot_week3.py")
        speel_duel(v3, v2, handen=200)

    `handen` is een bovengrens: is een van de twee door zijn chips heen, dan
    stopt het duel daar. Dat staat ook in de uitslag.

    `seed` maakt het duel herhaalbaar: dezelfde seed geeft dezelfde kaarten.
    Verander je iets aan je bot en draai je opnieuw met dezelfde seed, dan komt
    het verschil in uitslag door je verandering en niet door de kaarten.

    Let op wat dit wel en niet zegt. Twee spelers is geen tafel van zes: je
    winkansen liggen hier veel hoger, en een bot die aan een volle tafel te los
    speelt kan hier prima winnen. En 100 handen is weinig -- draai het een paar
    keer met verschillende seeds voor je concludeert dat je nieuwe versie beter
    is. In Werkcollege 8, Deel 7 reken je uit hoe groot dat toeval precies is.

    Geeft een dict terug met de eindstacks, zodat je er ook zelf mee kunt rekenen.
    """
    spelers = [
        _Duelspeler(naam_nieuw, bot_nieuw, bluf_kans_nieuw),
        _Duelspeler(naam_oud, bot_oud, bluf_kans_oud),
    ]
    random.seed(seed)
    config = setup_config(max_round=handen, initial_stack=START_STACK,
                          small_blind_amount=SMALL_BLIND)
    for speler in spelers:
        config.register_player(name=speler.naam, algorithm=speler)
    uitslag = start_poker(config, verbose=0)

    stacks = {p["name"]: p["stack"] for p in uitslag["players"]}
    gespeeld = max(speler.handen_gespeeld for speler in spelers)
    resultaat = {"handen": gespeeld, "handen_gevraagd": handen,
                 "seed": seed, "stacks": stacks, "bots": {}}
    for speler in spelers:
        verdeling = {}
        for actie in speler.acties:
            verdeling[actie] = verdeling.get(actie, 0) + 1
        resultaat["bots"][speler.naam] = {
            "stack": stacks.get(speler.naam),
            "winst": stacks.get(speler.naam, 0) - START_STACK,
            "beslissingen": len(speler.acties),
            "acties": verdeling,
            "fouten": speler.fouten[:5],
        }

    if not stil:
        _print_uitslag(resultaat)
    return resultaat


def _print_uitslag(resultaat):
    breedte = max(len(naam) for naam in resultaat["bots"])
    gevraagd = resultaat["handen_gevraagd"]
    vroeg = "" if resultaat["handen"] >= gevraagd else \
        f" (van de {gevraagd} -- een van de twee was door zijn chips heen)"
    print(f"{resultaat['handen']} handen gespeeld{vroeg}, seed {resultaat['seed']}")
    print("-" * (breedte + 46))
    for naam, cijfers in sorted(resultaat["bots"].items(),
                                key=lambda paar: -paar[1]["stack"]):
        winst = cijfers["winst"]
        acties = " ".join(f"{a}:{n}" for a, n in sorted(cijfers["acties"].items()))
        print(f"{naam:<{breedte}}  {cijfers['stack']:>5} chips  "
              f"({winst:+5})  {cijfers['beslissingen']:>4} beslissingen")
        print(f"{'':<{breedte}}  {acties}")
    verschil = [c["winst"] for c in resultaat["bots"].values()]
    if all(w == 0 for w in verschil):
        print("\nGeen van beide won iets -- speelden ze allebei elke hand fold?")

    fouten = {n: c["fouten"] for n, c in resultaat["bots"].items() if c["fouten"]}
    if fouten:
        print("\nLET OP -- een bot crashte tijdens het duel en foldde die handen:")
        for naam, meldingen in fouten.items():
            for melding in meldingen:
                print(f"  {naam}: {melding}")
        print("  In het toernooi gebeurt precies dit, alleen zie je het daar niet.")


# PyPokerEngine geeft Tien als "T"; `hand` gebruikt overal "10" (zie Week 1).
_NAAR_ENGINE_RANG = {"10": "T"}


def vraag_eigen_bot(kies_actie, hand, stack, ronde="preflop", pot=30,
                    inzet_om_te_callen=10, bluf_kans=0.3, bord=None,
                    hand_met_kleur=None, tegenstander_acties_deze_hand=None):
    """
    Roept JOUW kies_actie aan met precies de argumenten die hij accepteert.

        vraag_eigen_bot(mijn_bot, ["A", "A"], 1000, ronde="preflop")

    Dat is hoe het toernooi het ook doet (api/poker_adapter.roep_student_bot_aan):
    de engine kijkt naar je handtekening en geeft je alleen wat hij daarin
    tegenkomt. Roep je je eigen functie met vaste posities aan, dan breekt die
    aanroep zodra je een parameter toevoegt of weghaalt -- en dat is precies
    wat je deze week doet.

    Geef je geen `hand_met_kleur` mee, dan wordt er een plausibele gekozen
    (schoppen en harten), zodat een bot die hem gebruikt gewoon kan rekenen.
    """
    if hand_met_kleur is None:
        kleuren = ["S", "H"]
        hand_met_kleur = [kleur + _NAAR_ENGINE_RANG.get(str(rang), str(rang))
                          for kleur, rang in zip(kleuren, hand)]
    beschikbaar = {
        "hand": hand,
        "stack": stack,
        "ronde": ronde,
        "pot": pot,
        "inzet_om_te_callen": inzet_om_te_callen,
        "bluf_kans": bluf_kans,
        "bord": list(bord or []),
        "hand_met_kleur": hand_met_kleur,
        "tegenstander_acties_deze_hand": list(tegenstander_acties_deze_hand or []),
    }
    try:
        parameters = set(inspect.signature(kies_actie).parameters)
    except (TypeError, ValueError):
        parameters = set()
    return kies_actie(**{n: w for n, w in beschikbaar.items() if n in parameters})
