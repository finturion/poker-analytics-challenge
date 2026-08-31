"""
Vertaalt de simpele kies_actie()-functies van studenten naar spelers die
PyPokerEngine daadwerkelijk tegen elkaar kan laten spelen.

Studenten schrijven een functie die door het blok heen groeit:
    Week 1:  kies_actie(hand)
    Week 3:  kies_actie(hand, stack, strategie)
    Week 5:  kies_actie(hand, stack, strategie, bluf_kans)

Deze module hoeft niet per week te weten welke vorm het is: met
inspect.signature() geven we een functie alleen de argumenten die hij zelf
accepteert. Zo kan dezelfde toernooi-engine vanaf Week 1 gebruikt worden,
en blijft hij werken als de bot-signatuur in Week 3 en 5 uitbreidt.
"""
import inspect
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

# PyPokerEngine gebruikt "T" voor Tien; wij gebruiken overal "10" (zie Week 1).
_RANG_VERTALING = {"T": "10"}

TAFEL_GROOTTE_MAX = 6
STANDAARD_N_HANDEN = 50
STANDAARD_INITIAL_STACK = 1000
STANDAARD_SMALL_BLIND = 10

# bot_validator.py test elke bot-functie al één keer in een subprocess met
# timeout, vóórdat een inzending wordt goedgekeurd. Tijdens het toernooi
# draait dezelfde functie duizenden keren met écht wisselende handen, in
# hetzelfde proces als de API zelf (een los subprocess per beslissing zou
# het toernooi onwerkbaar traag maken). Deze executor is het vangnet voor
# een hand die de student niet zelf getest had en die blijft hangen — zonder
# dit zou één bot de hele toernooi-run kunnen bevriezen.
_BESLISSING_EXECUTOR = ThreadPoolExecutor(max_workers=4)
BESLISSING_TIMEOUT_SECONDS = 2


def _naar_onze_hand(hole_card):
    """PyPokerEngine geeft bv. ['ST', 'HT'] -> wij willen ['10', '10']."""
    return [_RANG_VERTALING.get(kaart[1], kaart[1]) for kaart in hole_card]


def roep_student_bot_aan(kies_actie, hand, stack, strategie, bluf_kans):
    """
    Roept de functie van de student aan met alleen de argumenten die hij
    zelf in zijn eigen functie-signatuur accepteert.

    Crasht de studentcode (bv. een vergeten edge case), dan folded de bot
    die hand — één kapotte bot mag de rest van het toernooi niet verstoren.
    """
    beschikbaar = {"hand": hand, "stack": stack, "strategie": strategie, "bluf_kans": bluf_kans}
    try:
        parameters = inspect.signature(kies_actie).parameters
    except (TypeError, ValueError):
        return "fold"

    kwargs = {naam: waarde for naam, waarde in beschikbaar.items() if naam in parameters}
    try:
        future = _BESLISSING_EXECUTOR.submit(kies_actie, **kwargs)
        resultaat = future.result(timeout=BESLISSING_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        return "fold"
    except Exception:
        return "fold"

    if not isinstance(resultaat, str):
        return "fold"
    return resultaat.lower()


class StudentBotSpeler(BasePokerPlayer):
    """Eén student-bot, gespeeld door PyPokerEngine, met een hand-voor-hand logboek."""

    def __init__(self, bot_naam, kies_actie, strategie=None, bluf_kans=None):
        super().__init__()
        self.bot_naam = bot_naam
        self._kies_actie = kies_actie
        self._strategie = strategie
        self._bluf_kans = bluf_kans
        self._huidige_hand_nummer = 0
        self._eerste_actie_deze_hand = None
        self.hand_log = []

    def declare_action(self, valid_actions, hole_card, round_state):
        hand = _naar_onze_hand(hole_card)
        eigen_stack = self._vind_eigen_stack(round_state)
        gekozen = roep_student_bot_aan(
            self._kies_actie, hand, eigen_stack, self._strategie, self._bluf_kans
        )
        if self._eerste_actie_deze_hand is None:
            self._eerste_actie_deze_hand = gekozen
        return self._naar_geldige_actie(gekozen, valid_actions)

    def _vind_eigen_stack(self, round_state):
        for seat in round_state["seats"]:
            if seat["uuid"] == self.uuid:
                return seat["stack"]
        return None

    @staticmethod
    def _naar_geldige_actie(gekozen, valid_actions):
        """
        Valt terug op call, dan fold, als de gekozen actie nu niet mag
        (bv. een bot die altijd 'raise' kiest, terwijl all-in al gebeurd is).
        """
        toegestaan = {a["action"]: a for a in valid_actions}
        volgorde = [gekozen, "call", "fold"]
        for optie in volgorde:
            if optie in toegestaan:
                bedrag = toegestaan[optie]["amount"]
                if isinstance(bedrag, dict):
                    bedrag = bedrag["min"]
                return optie, bedrag

        eerste = valid_actions[0]
        bedrag = eerste["amount"]
        if isinstance(bedrag, dict):
            bedrag = bedrag["min"]
        return eerste["action"], bedrag

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self._huidige_hand_nummer = round_count
        self._eerste_actie_deze_hand = None

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, new_action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        eigen_stack = self._vind_eigen_stack(round_state)
        self.hand_log.append(
            {
                "bot_naam": self.bot_naam,
                "hand_nummer": self._huidige_hand_nummer,
                "actie": self._eerste_actie_deze_hand or "fold",
                "stack": eigen_stack,
            }
        )


def _normaliseer_bot_invoer(bot_invoer):
    """
    Een bot mag worden opgegeven als kale kies_actie-functie, of als dict
    {"kies_actie": fn, "strategie": ..., "bluf_kans": ...} als je (vanaf
    Week 3) ook de door de student opgegeven strategie/bluf_kans wilt
    meegeven aan de speler.
    """
    if callable(bot_invoer):
        return {"kies_actie": bot_invoer, "strategie": None, "bluf_kans": None}
    return {
        "kies_actie": bot_invoer["kies_actie"],
        "strategie": bot_invoer.get("strategie"),
        "bluf_kans": bot_invoer.get("bluf_kans"),
    }


def speel_tafel(bots, tafel_nummer, n_handen=STANDAARD_N_HANDEN, seed=None):
    """
    bots: dict {bot_naam: kies_actie-functie of {"kies_actie", "strategie", "bluf_kans"}},
    2 tot TAFEL_GROOTTE_MAX bots.
    Retourneert het hand-log van alle bots aan deze tafel samen, met
    tafel_nummer erbij zodat je resultaten van meerdere tafels kan combineren.
    """
    if len(bots) < 2:
        raise ValueError("Een tafel heeft minstens 2 bots nodig.")

    if seed is not None:
        random.seed(seed)

    config = setup_config(
        max_round=n_handen,
        initial_stack=STANDAARD_INITIAL_STACK,
        small_blind_amount=STANDAARD_SMALL_BLIND,
    )
    spelers = {}
    for bot_naam, bot_invoer in bots.items():
        info = _normaliseer_bot_invoer(bot_invoer)
        speler = StudentBotSpeler(bot_naam, info["kies_actie"], strategie=info["strategie"], bluf_kans=info["bluf_kans"])
        spelers[bot_naam] = speler
        config.register_player(name=bot_naam, algorithm=speler)

    start_poker(config, verbose=0)

    log = []
    for speler in spelers.values():
        for rij in speler.hand_log:
            log.append({**rij, "tafel": tafel_nummer})
    return log


def _verdeel_in_tafels(bot_namen, rng):
    """Verdeelt bot-namen willekeurig in groepen van max TAFEL_GROOTTE_MAX."""
    namen = list(bot_namen)
    rng.shuffle(namen)
    tafels = [namen[i : i + TAFEL_GROOTTE_MAX] for i in range(0, len(namen), TAFEL_GROOTTE_MAX)]

    # Een tafel met maar 1 bot kan niet spelen: voeg 'm bij de vorige tafel.
    if len(tafels) >= 2 and len(tafels[-1]) < 2:
        tafels[-2].extend(tafels[-1])
        tafels.pop()
    return tafels


def speel_toernooi(bots, n_simulaties=5, n_handen=STANDAARD_N_HANDEN, seed=0):
    """
    bots: dict {bot_naam: kies_actie-functie of {"kies_actie", "strategie", "bluf_kans"}}.

    Speelt meerdere simulaties, en verdeelt de bots binnen elke simulatie
    opnieuw willekeurig over tafels van maximaal TAFEL_GROOTTE_MAX bots. Zo
    weet je per bot hoe hij presteert over meerdere tafels en meerdere
    simulaties heen, niet slechts één toevallige zit.

    Retourneert {"hand_log": [...], "eindstand_per_bot": {...}}.
    """
    if len(bots) < 2:
        raise ValueError("Er zijn minstens 2 bots nodig om een toernooi te spelen.")

    rng = random.Random(seed)
    volledig_log = []

    for simulatie_nummer in range(n_simulaties):
        tafels = _verdeel_in_tafels(bots.keys(), rng)
        for tafel_index, namen_aan_tafel in enumerate(tafels):
            bots_aan_tafel = {naam: bots[naam] for naam in namen_aan_tafel}
            tafel_seed = seed * 10_000 + simulatie_nummer * 100 + tafel_index
            tafel_log = speel_tafel(bots_aan_tafel, tafel_index, n_handen=n_handen, seed=tafel_seed)
            for rij in tafel_log:
                volledig_log.append({**rij, "simulatie": simulatie_nummer})

    eindstand_per_bot = _bereken_eindstand(volledig_log)
    return {"hand_log": volledig_log, "eindstand_per_bot": eindstand_per_bot}


def _bereken_eindstand(hand_log):
    """
    Gemiddelde eindstack per bot, over alle (simulatie, tafel)-combinaties
    heen. Geen pandas-afhankelijkheid hier, puur voor als deze module
    los van de rest getest wordt.
    """
    laatste_stack_per_combinatie = {}
    for rij in hand_log:
        sleutel = (rij["bot_naam"], rij["simulatie"], rij["tafel"])
        bestaand = laatste_stack_per_combinatie.get(sleutel)
        if bestaand is None or rij["hand_nummer"] > bestaand["hand_nummer"]:
            laatste_stack_per_combinatie[sleutel] = rij

    stacks_per_bot = {}
    for (bot_naam, _simulatie, _tafel), rij in laatste_stack_per_combinatie.items():
        stacks_per_bot.setdefault(bot_naam, []).append(rij["stack"])

    return {
        bot_naam: round(sum(stacks) / len(stacks), 1)
        for bot_naam, stacks in stacks_per_bot.items()
    }
