"""
Vertaalt de simpele kies_actie()-functies van studenten naar spelers die
PyPokerEngine daadwerkelijk tegen elkaar kan laten spelen.

Studenten schrijven een functie die door het blok heen groeit:
    Week 1:  kies_actie(hand)
    Week 3:  kies_actie(hand, stack)
    Week 5:  kies_actie(hand, stack, strategie, bluf_kans)

Daarnaast mag een bot vanaf Week 3 optioneel ook `ronde` ("preflop"/"flop"/
"turn"/"river"), `pot` en `inzet_om_te_callen` opnemen, zodat hij een ander
besluit kan nemen per speelronde in plaats van zijn hand-sterkte maar één
keer per hand te wegen (`pot`/`inzet_om_te_callen` sluiten direct aan op
bereken_pot_odds() uit Werkcollege 4). Ook mag een bot `tegenstander_acties_
deze_hand` opnemen: een lijst met wat de ANDERE spelers deze hand al hebben
gedaan (bot_naam/actie/bedrag, over alle straten tot nu toe) -- niet wat ze
ooit in het verleden deden, alleen deze ene hand, precies zoals je dat aan
een echte tafel ook zou zien.

Deze module hoeft niet per week te weten welke vorm het is: met
inspect.signature() geven we een functie alleen de argumenten die hij zelf
accepteert. Zo kan dezelfde toernooi-engine vanaf Week 1 gebruikt worden,
en blijft hij werken als de bot-signatuur in Week 3 en 5 uitbreidt -- en een
bot die een van deze parameters niet kent, krijgt 'm simpelweg niet
aangeboden.
"""
import inspect
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from pypokerengine.api.game import Dealer, setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

# PyPokerEngine gebruikt "T" voor Tien; wij gebruiken overal "10" (zie Week 1).
_RANG_VERTALING = {"T": "10"}

TAFEL_GROOTTE_MAX = 6
STANDAARD_N_HANDEN = 50
STANDAARD_INITIAL_STACK = 1000
STANDAARD_SMALL_BLIND = 10

# Hoeveel keer een bot per straat mag raisen. Stond op 1, staat nu op 2 zodat er
# een re-raise mogelijk is: wie groot inzet kan worden teruggepakt, in plaats van
# dat de tafel alleen kan callen of folden. Dat maakt het spel niet ingewikkelder
# voor de student -- kies_actie() geeft nog steeds gewoon "raise" terug en de
# engine bepaalt of dat mag -- maar het maakt agressie wél weerlegbaar.
MAX_RAISES_PER_STRAAT = 2

# Waarop "grote_raise" inzet. Een gewone raise is het wettelijke minimum -- mediaan
# 40 chips, dus twee big blinds -- en all-in is de hele stack, mediaan 1540. Daar
# zat niets tussen, en dus geen enkele keuze in inzetgrootte. 200 chips is tien big
# blinds: groot genoeg om iemand van een middelmatige hand af te duwen, klein genoeg
# om niet je hele toernooi te riskeren. Gemeten maakt de exacte hoogte boven de 200
# nauwelijks nog verschil.
GROTE_RAISE_CHIPS = 200

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


def _heeft_parameter(kies_actie, naam):
    """Of de student deze parameter zelf in zijn signatuur heeft gezet."""
    try:
        return naam in inspect.signature(kies_actie).parameters
    except (TypeError, ValueError):
        return False


def _ondersteunt_grote_raise(kies_actie):
    """
    "grote_raise" mag vanaf Week 3, op hetzelfde signaal als all-in: "stack".

    Stond eerst op "strategie" (Week 5), met het argument dat inzetgrootte pas een
    keuze is als je een strategie en een bluf-kans hebt. Dat argument houdt geen
    stand: vanaf Week 3 heeft een bot pot odds en een winkans, en dat is precies
    wat je nodig hebt om te bepalen hóeveel je inzet. En het is de eerste vraag
    die een student stelt zodra hij de regels leert -- "hoeveel is een raise?" --
    dus die kun je daar beter meteen beantwoorden.
    """
    return _heeft_parameter(kies_actie, "stack")


def _ondersteunt_all_in_regels(kies_actie):
    """
    Vanaf Week 3 schrijven studenten kies_actie(hand, stack, ...) en kunnen ze
    daarmee bewust reageren op hun eigen stack. Alleen bots met die
    stack-parameter krijgen de Week 3-spelregels: maximaal MAX_RAISES_PER_STRAAT
    raises per straat, en de
    mogelijkheid om zelf "all_in" terug te geven. Week 1/2-bots (die alleen
    `hand` kennen) spelen met het oude, ongewijzigde gedrag, zodat al gedraaide
    toernooien voor die weken niet stiekem veranderen.

    De gate kijkt bewust naar `stack` en niet naar `strategie`: strategie komt
    pas vanaf Week 5, terwijl all-in en de raise-cap al vanaf Week 3 gelden.
    """
    return _heeft_parameter(kies_actie, "stack")


def roep_student_bot_aan(
    kies_actie, hand, stack, strategie, bluf_kans, ronde=None, pot=None, inzet_om_te_callen=None,
    tegenstander_acties_deze_hand=None, bord=None, hand_met_kleur=None,
):
    """
    Roept de functie van de student aan met alleen de argumenten die hij
    zelf in zijn eigen functie-signatuur accepteert.

    Crasht de studentcode (bv. een vergeten edge case), dan folded de bot
    die hand — één kapotte bot mag de rest van het toernooi niet verstoren.
    """
    beschikbaar = {
        "hand": hand,
        "stack": stack,
        "strategie": strategie,
        "bluf_kans": bluf_kans,
        "ronde": ronde,
        "pot": pot,
        "inzet_om_te_callen": inzet_om_te_callen,
        "tegenstander_acties_deze_hand": tegenstander_acties_deze_hand,
        # De kaarten op tafel, en je eigen twee MET kleur. Twee aparte namen, en
        # `hand` blijft precies wat hij was -- twee rangen zonder kleur. Anders
        # zou elke bot uit Week 1 en 3 breken die `hand[0] == hand[1]` doet of
        # een rang in een verzameling opzoekt.
        #
        # Ze horen bij elkaar: een winkans mét bord kan alleen als je ook je
        # eigen kleuren kent, want zonder kleur is een flush niet te zien.
        "bord": bord,
        "hand_met_kleur": hand_met_kleur,
    }
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
        self._hand_deze_hand = None
        self._eerste_actie_deze_hand = None
        self._raises_deze_straat = 0
        self._huidige_straat = None
        self._ondersteunt_all_in = _ondersteunt_all_in_regels(kies_actie)
        self._ondersteunt_grote_raise = _ondersteunt_grote_raise(kies_actie)
        self._acties_deze_hand = []
        self._uuid_naar_naam = {}
        self.hand_log = []

    def declare_action(self, valid_actions, hole_card, round_state):
        hand = _naar_onze_hand(hole_card)
        eigen_stack = self._vind_eigen_stack(round_state)
        ronde = round_state.get("street")
        pot = round_state.get("pot", {}).get("main", {}).get("amount")
        inzet_om_te_callen = next(
            (a["amount"] for a in valid_actions if a["action"] == "call"), None
        )
        gekozen = roep_student_bot_aan(
            self._kies_actie, hand, eigen_stack, self._strategie, self._bluf_kans,
            ronde=ronde, pot=pot, inzet_om_te_callen=inzet_om_te_callen,
            tegenstander_acties_deze_hand=list(self._acties_deze_hand),
            # In de notatie van de engine en van beschrijf_hand(): "SA", "CT".
            # Preflop is dit een lege lijst, niet None -- dan hoeft een bot geen
            # onderscheid te maken tussen "nog geen bord" en "geen bord gekregen".
            bord=list(round_state.get("community_card") or []),
            hand_met_kleur=list(hole_card),
        )
        # Een grote raise telt voor de cap net zo hard als een gewone: anders zou je
        # met "grote_raise" onbeperkt kunnen blijven verhogen.
        if self._ondersteunt_all_in and gekozen in ("raise", "grote_raise"):
            if self._raises_deze_straat >= MAX_RAISES_PER_STRAAT:
                # het maximum voor deze straat is bereikt -- niet meer raisen, wel callen
                gekozen = "call"
            else:
                self._raises_deze_straat += 1
        if self._eerste_actie_deze_hand is None:
            self._eerste_actie_deze_hand = gekozen
        return self._naar_geldige_actie(
            gekozen, valid_actions, self._ondersteunt_all_in, self._ondersteunt_grote_raise
        )

    def _vind_eigen_stack(self, round_state):
        for seat in round_state["seats"]:
            if seat["uuid"] == self.uuid:
                return seat["stack"]
        return None

    @staticmethod
    def _is_geldige_raise(actie_info):
        bedrag = actie_info["amount"]
        return not (isinstance(bedrag, dict) and bedrag["min"] == -1)

    @classmethod
    def _naar_geldige_actie(cls, gekozen, valid_actions, all_in_ondersteund=False,
                            grote_raise_ondersteund=False):
        """
        Valt terug op call, dan fold, als de gekozen actie nu niet mag.

        Voor bots zonder all-in-regels (Week 1/2) is dit ongewijzigd het
        oorspronkelijke gedrag: een "raise" telt al als beschikbaar zodra hij
        in valid_actions voorkomt, ook als PyPokerEngine 'm eigenlijk als
        onmogelijk markeert (min/max op -1) -- dat leidt dan verderop in de
        engine tot een automatische fold. Dat is bekend, historisch gedrag en
        blijft zo, om al gedraaide Week 1/2-toernooien niet te laten
        verschuiven.

        Voor bots MET all-in-regels (Week 3+) is dit gecorrigeerd: "raise"
        telt alleen als beschikbaar als hij ook echt een geldig bedrag heeft,
        anders valt de bot netjes terug op call (die PyPokerEngine zelf
        automatisch als all-in afhandelt als de stack te klein is om volledig
        te callen). "all_in" zet de hele stack in: een raise naar het
        maximale bedrag als dat nog kan, anders een call.

        "grote_raise" (vanaf Week 5) is een raise van GROTE_RAISE_CHIPS in plaats
        van het wettelijke minimum. Kan dat bedrag niet -- omdat het onder het
        minimum ligt of boven wat de stack toelaat -- dan wordt het naar het
        dichtstbijzijnde toegestane bedrag getrokken. Zo doet een grote raise altijd
        íets, ook met een korte stack, en wordt hij nooit stil een fold.
        """
        toegestaan = {a["action"]: a for a in valid_actions}

        if grote_raise_ondersteund and gekozen == "grote_raise":
            raise_info = toegestaan.get("raise")
            if raise_info and cls._is_geldige_raise(raise_info):
                minimum, maximum = raise_info["amount"]["min"], raise_info["amount"]["max"]
                return "raise", max(minimum, min(GROTE_RAISE_CHIPS, maximum))
            gekozen = "call"

        if all_in_ondersteund and gekozen == "all_in":
            raise_info = toegestaan.get("raise")
            if raise_info and cls._is_geldige_raise(raise_info):
                return "raise", raise_info["amount"]["max"]
            gekozen = "call"

        volgorde = [gekozen, "call", "fold"]
        for optie in volgorde:
            info = toegestaan.get(optie)
            if info is None:
                continue
            if all_in_ondersteund and optie == "raise" and not cls._is_geldige_raise(info):
                continue
            bedrag = info["amount"]
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
        self._hand_deze_hand = _naar_onze_hand(hole_card)
        self._eerste_actie_deze_hand = None
        self._acties_deze_hand = []
        self._uuid_naar_naam = {seat["uuid"]: seat["name"] for seat in seats}

    def receive_street_start_message(self, street, round_state):
        self._raises_deze_straat = 0
        self._huidige_straat = street

    def receive_game_update_message(self, new_action, round_state):
        if new_action["player_uuid"] == self.uuid:
            return  # eigen acties horen niet in tegenstander_acties_deze_hand
        self._acties_deze_hand.append({
            "bot_naam": self._uuid_naar_naam.get(new_action["player_uuid"], "onbekend"),
            "actie": new_action["action"],
            "bedrag": new_action["amount"],
            # De straat waarin deze actie viel. De lijst loopt over de HELE hand --
            # dat zegt de parameternaam ook -- en werd zonder dit label een val:
            # gemeten stond er in 35% van de beslissingen een raise in terwijl
            # niemand op déze straat verhoogde. Met dit label kun je filteren.
            "ronde": self._huidige_straat,
        })

    def receive_round_result_message(self, winners, hand_info, round_state):
        eigen_stack = self._vind_eigen_stack(round_state)
        self.hand_log.append(
            {
                "bot_naam": self.bot_naam,
                "hand_nummer": self._huidige_hand_nummer,
                # De twee kaarten waarmee deze hand is gespeeld. Staat erin zodat
                # studenten kunnen nagaan wélke handen ze speelden en wat die
                # opleverden -- zonder dit veld is de winkans-grens die ze in
                # Week 3 kozen achteraf niet te controleren. Het maakt ook de
                # drempels van tegenstanders leesbaar uit hun eigen log, en dat
                # is een legitieme pokervaardigheid: de hand is afgelopen.
                "hand": self._hand_deze_hand,
                # actie is None als de bot deze hand niet aan de beurt kwam. Dat
                # gebeurt vaker dan je denkt: iedereen foldde naar zijn blind (dan
                # wón hij juist), of hij is uitgespeeld en heeft geen chips meer.
                # Hier stond eerst `or "fold"`, en dat was een leugen: gemeten
                # kreeg 5% van de fold-regels een POSITIEVE winst, en 55% van alle
                # regels kwam van bots met stack 0 die gewoon doorschreven. Elke
                # analyse van "wat leverde elke actie op" werd daar fout van.
                "actie": self._eerste_actie_deze_hand,
                "aan_zet": self._eerste_actie_deze_hand is not None,
                "uitgespeeld": eigen_stack == 0,
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


def speel_tafel(bots, tafel_nummer, n_handen=STANDAARD_N_HANDEN, seed=None, startstacks=None):
    """
    bots: dict {bot_naam: kies_actie-functie of {"kies_actie", "strategie", "bluf_kans"}},
    2 tot TAFEL_GROOTTE_MAX bots.

    startstacks: optioneel {bot_naam: chips}. Zonder dit begint iedereen op
    STANDAARD_INITIAL_STACK. Mét dit begint elke bot met zijn eigen aantal
    chips -- dat is wat een vervolgronde nodig heeft, waarin je verder speelt
    met wat je de vorige ronde hebt overgehouden.

    PyPokerEngine kent maar één initial_stack voor de hele tafel, dus we
    gebruiken hier de Dealer rechtstreeks: die maakt bij register_player de
    Player-objecten aan, en dáárna kunnen we hun stack per speler zetten,
    vóór de eerste hand wordt gedeeld.

    Retourneert het hand-log van alle bots aan deze tafel samen, met
    tafel_nummer erbij zodat je resultaten van meerdere tafels kan combineren.
    """
    if len(bots) < 2:
        raise ValueError("Een tafel heeft minstens 2 bots nodig.")

    if seed is not None:
        random.seed(seed)

    dealer = Dealer(STANDAARD_SMALL_BLIND, STANDAARD_INITIAL_STACK, 0)
    dealer.set_verbose(0)

    spelers = {}
    for bot_naam, bot_invoer in bots.items():
        info = _normaliseer_bot_invoer(bot_invoer)
        speler = StudentBotSpeler(bot_naam, info["kies_actie"], strategie=info["strategie"], bluf_kans=info["bluf_kans"])
        spelers[bot_naam] = speler
        dealer.register_player(bot_naam, speler)

    if startstacks:
        for speler_object in dealer.table.seats.players:
            if speler_object.name in startstacks:
                speler_object.stack = int(startstacks[speler_object.name])

    dealer.start_game(n_handen)

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

    # Een tafel met maar 1 bot kan niet spelen. Die bot bij de vorige tafel
    # plakken gaf een tafel van TAFEL_GROOTTE_MAX + 1 -- bij 7 bots één tafel van
    # 7, en bij 44 studenten plus 5 referentiebots precies hetzelfde. Zeven-handed
    # poker speelt tighter dan de 6-max die de rest van het toernooi speelt, dus
    # dat is geen detail. In plaats daarvan halen we een bot van de vórige tafel
    # erbij, zodat er twee tafels van 2 en 6 ontstaan in plaats van één van 7.
    if len(tafels) >= 2 and len(tafels[-1]) < 2:
        tafels[-1].append(tafels[-2].pop())
    return tafels


def bereken_startstacks(vorige_eindstand, bonus=STANDAARD_INITIAL_STACK):
    """
    Zet de eindstand van een vorige ronde om in startstacks voor de volgende.

    Iedereen krijgt `bonus` chips erbij, zodat niemand uitgesloten raakt omdat
    hij de blinds niet meer kan betalen -- ook een bot die de vorige ronde
    helemaal is uitgespeeld begint dus weer met een volwaardige stack. Wat je
    daarboven hebt overgehouden, neem je mee.

    Dat is het hele punt van doorspelen: je woensdag-inzending bepaalt waarmee
    je donderdag aan tafel gaat, dus een placeholder inleveren kost je echte
    chips in plaats van niets.
    """
    return {naam: int(round(stand)) + bonus for naam, stand in vorige_eindstand.items()}


def speel_toernooi(bots, n_simulaties=5, n_handen=STANDAARD_N_HANDEN, seed=0, startstacks=None):
    """
    bots: dict {bot_naam: kies_actie-functie of {"kies_actie", "strategie", "bluf_kans"}}.

    Speelt meerdere simulaties, en verdeelt de bots binnen elke simulatie
    opnieuw willekeurig over tafels van maximaal TAFEL_GROOTTE_MAX bots. Zo
    weet je per bot hoe hij presteert over meerdere tafels en meerdere
    simulaties heen, niet slechts één toevallige zit.

    startstacks: optioneel {bot_naam: chips}, bijvoorbeeld uit
    bereken_startstacks() van de vorige ronde. Elke simulatie begint met
    dezelfde startstacks -- de simulaties zijn parallelle werelden, geen
    opeenvolgende rondes.

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
            tafel_log = speel_tafel(
                bots_aan_tafel, tafel_index, n_handen=n_handen, seed=tafel_seed,
                startstacks=startstacks,
            )
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
