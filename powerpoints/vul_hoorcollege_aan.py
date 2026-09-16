"""
Voegt dia's toe aan het hoorcollege-deck over EDA en datamanipulatie.

Het origineel wordt NOOIT overschreven: dit script leest het bronbestand en
schrijft een nieuwe kopie ernaast. De opmaak volgt die van het deck zelf --
Arial, titel 32pt in #25167A op (2.17, 1.03), tekstblok op (2.17, 2.28) --
zodat de nieuwe dia's niet opvallen tussen de bestaande.

    python3 powerpoints/vul_hoorcollege_aan.py "/pad/naar/03_Exploring Manipulating Data.pptx"

Schrijft powerpoints/hoorcollege/03_Exploring_Manipulating_Data_aangevuld.pptx
"""
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
UITVOER = os.path.join(HIER, "hoorcollege", "03_Exploring_Manipulating_Data_aangevuld.pptx")

TITELKLEUR = RGBColor(0x25, 0x16, 0x7A)
TEKSTKLEUR = RGBColor(0x00, 0x00, 0x00)
ACCENT = RGBColor(0x1B, 0x4D, 0x3E)
GEDEMPT = RGBColor(0x50, 0x5A, 0x64)

# (titel, [(niveau, tekst, vet, kleur), ...])
NIEUWE_DIAS = [
    (
        "Wat je bot tot nu toe kon: alleen de openingshand",
        [
            (0, "In week 3 rekent je bot met twee kaarten en verder niets.", True, TEKSTKLEUR),
            (1, "schat_winkans([\"A\", \"K\"], tegenstanders=5) → één getal, vóór de flop", False, TEKSTKLEUR),
            (1, "Dat getal verandert de hele hand niet meer — ook niet als er drie schoppen vallen", False, TEKSTKLEUR),
            (0, "Waarom dat kon: winkansen preflop veranderen nooit.", True, TEKSTKLEUR),
            (1, "169 mogelijke starthanden, dus je rekent ze één keer uit en plakt de tabel in je bot", False, TEKSTKLEUR),
            (1, "Precies waar een dictionary voor bedoeld is: sleutel → waarde", False, TEKSTKLEUR),
            (0, "Wat je bot dus niet weet:", True, TEKSTKLEUR),
            (1, "of het bord bij zijn kaarten past, of iemand anders aan een flush werkt", False, GEDEMPT),
        ],
    ),
    (
        "Vanaf week 5: per straat opnieuw rekenen",
        [
            (0, "Je bot krijgt het bord erbij, en zijn eigen kaarten mét kleur.", True, TEKSTKLEUR),
            (1, "schat_winkans(hand_met_kleur, bord=bord, tegenstanders=3)", False, ACCENT),
            (1, "De ontbrekende kaarten worden om jouw bord heen gedeeld — geen willekeurig bord meer", False, TEKSTKLEUR),
            (0, "Kleur is hier niet optioneel. Zelfde rangen, bord met drie schoppen:", True, TEKSTKLEUR),
            (1, "S7 S8, allebei schoppen: 36,6% op de flop — en 94,1% op de river, met de flush", False, ACCENT),
            (1, "H7 C8, gemengde kleuren: 8,0% op de flop — en 0,0% op de river", False, GEDEMPT),
            (0, "En een opzoektabel werkt hier niet meer.", True, TEKSTKLEUR),
            (1, "Binnen de categorie \"één paar\" op de flop loopt de echte winkans van 8,5% tot 75,5%", False, TEKSTKLEUR),
            (1, "Een tabelwaarde van gemiddeld 33,8% zit dan in beide richtingen ver mis", False, GEDEMPT),
        ],
    ),
    (
        "Wat moest, en wat mocht — week 3",
        [
            (0, "VERPLICHT — zonder dit wordt je inzending afgekeurd", True, TITELKLEUR),
            (1, "kies_actie(hand, stack)   — die twee namen, exact zo gespeld", False, TEKSTKLEUR),
            (1, "je bot geeft één string terug: fold, call, raise, all_in of grote_raise", False, TEKSTKLEUR),
            (0, "OPTIONEEL — je krijgt ze alleen als je ze zelf opschrijft", True, ACCENT),
            (1, "ronde · pot · inzet_om_te_callen · tegenstander_acties_deze_hand", False, ACCENT),
            (1, "De engine kijkt naar je parameternamen. Verkeerd gespeld = je krijgt hem niet.", False, TEKSTKLEUR),
            (0, "Twee dingen die pas aangaan mét stack:", True, TEKSTKLEUR),
            (1, "all_in en grote_raise mogen dan pas — zonder te weten hoeveel je hebt kun je dat niet afwegen", False, TEKSTKLEUR),
            (1, "en de cap van twee raises per straat gaat gelden", False, TEKSTKLEUR),
        ],
    ),
    (
        "De bot die niet nadenkt werd eerste",
        [
            (0, "Toernooi week 3, 27 bots. De uitslag bovenaan:", True, TEKSTKLEUR),
            (1, "1.  Testbot_CalltAlles — 1748 chips, foldt 0,0%", False, ACCENT),
            (1, "2.  een van jullie — 1738 chips, foldt 82,5%", False, TEKSTKLEUR),
            (1, "3.  een van jullie — 1256 chips, foldt 58,7%", False, TEKSTKLEUR),
            (0, "Die eerste is één regel: geef altijd \"call\" terug, wat je ook hebt.", True, TEKSTKLEUR),
            (1, "Geen winkans, geen pot odds, kijkt niet eens naar zijn kaarten", False, TEKSTKLEUR),
            (1, "De klas foldde 92,2% van alle beslissingen; negen bots foldden 99% of meer", False, TEKSTKLEUR),
            (1, "Correlatie tussen fold% en eindstand: -0,69 — meer folden is minder eindigen", False, GEDEMPT),
            (0, "Waarom verliest een bot mét regels van een bot zonder regels?", True, TITELKLEUR),
        ],
    ),
]


def voeg_dia_toe(prs, titel, regels, nummer):
    """Eén dia in de stijl van het deck: leeg canvas, twee tekstvakken, paginanummer."""
    dia = prs.slides.add_slide(prs.slide_layouts[0])

    kop = dia.shapes.add_textbox(Inches(2.17), Inches(1.03), Inches(9.0), Inches(1.25))
    p = kop.text_frame.paragraphs[0]
    p.text = titel
    p.font.name = "Arial"
    p.font.size = Pt(32)
    p.font.color.rgb = TITELKLEUR
    kop.text_frame.word_wrap = True

    vak = dia.shapes.add_textbox(Inches(2.17), Inches(2.28), Inches(9.6), Inches(4.42))
    tf = vak.text_frame
    tf.word_wrap = True
    for i, (niveau, tekst, vet, kleur) in enumerate(regels):
        alinea = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        alinea.text = tekst
        alinea.level = niveau
        alinea.font.name = "Arial"
        alinea.font.size = Pt(17 if niveau == 0 else 14)
        alinea.font.bold = vet
        alinea.font.color.rgb = kleur
        if niveau == 0 and i:
            alinea.space_before = Pt(13)

    nr = dia.shapes.add_textbox(Inches(10.69), Inches(6.70), Inches(0.69), Inches(0.40))
    pn = nr.text_frame.paragraphs[0]
    pn.text = str(nummer)
    pn.font.name = "Arial"
    pn.font.size = Pt(12)
    pn.font.color.rgb = GEDEMPT
    return dia


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bron = sys.argv[1]
    if not os.path.exists(bron):
        print(f"Bronbestand niet gevonden: {bron}")
        return 2
    if os.path.abspath(bron) == os.path.abspath(UITVOER):
        print("Bron en uitvoer zijn hetzelfde bestand. Dat doen we niet.")
        return 2

    prs = Presentation(bron)
    begin = len(prs.slides)
    for i, (titel, regels) in enumerate(NIEUWE_DIAS):
        voeg_dia_toe(prs, titel, regels, begin + i + 1)

    os.makedirs(os.path.dirname(UITVOER), exist_ok=True)
    prs.save(UITVOER)
    print(f"{begin} dia's uit het origineel + {len(NIEUWE_DIAS)} nieuwe -> {UITVOER}")
    print(f"Het origineel is niet aangeraakt: {bron}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
