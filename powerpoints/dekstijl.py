"""
Het palet en de vier bouwstenen die alle decks van dit vak delen.

Stond eerst alleen in maak_presentatie_week3.py. Toen het week-6-deck erbij kwam
was de keuze: overtypen of delen. Overtypen is precies hoe een lesversie en een
backendversie van dezelfde functie uit elkaar gaan lopen, dus delen.

Een dia is hier altijd hetzelfde: een leeg canvas (layout 6), een gekleurd vlak
over de hele dia, een kop met een categorie erboven, en daarna kaarten en
tekstblokken op maat. Alles in inches, want dat leest beter dan EMU.
"""
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

BG = RGBColor(248, 249, 250)
PRIMAIR = RGBColor(18, 30, 49)
ACCENT = RGBColor(27, 77, 62)
GEDEMPT = RGBColor(80, 90, 100)
KAART = RGBColor(255, 255, 255)
LIJN = RGBColor(220, 225, 230)
LICHTGROEN = RGBColor(79, 195, 161)
WAARSCHUWING = RGBColor(179, 38, 30)

# Dezelfde kleuren als hex, voor de matplotlib-platen die op deze dia's landen.
HEX = {
    "primair": "#121E31",
    "accent": "#1B4D3E",
    "gedempt": "#505A64",
    "lijn": "#DCE1E6",
    "papier": "#F8F9FA",
    "rood": "#B3261E",
    "lichtgroen": "#4FC3A1",
}


def nieuwe_dia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    achtergrond = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                       prs.slide_width, prs.slide_height)
    achtergrond.fill.solid()
    achtergrond.fill.fore_color.rgb = BG
    achtergrond.line.fill.background()
    achtergrond.shadow.inherit = False
    return dia


def kop(dia, categorie, titel):
    vak = dia.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.7), Inches(1.1))
    tf = vak.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = categorie
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    p2 = tf.add_paragraph()
    p2.text = titel
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = PRIMAIR
    p2.space_before = Pt(4)


def kaart(dia, links, boven, breedte, hoogte, kleur=KAART):
    vorm = dia.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, links, boven, breedte, hoogte)
    vorm.fill.solid()
    vorm.fill.fore_color.rgb = kleur
    vorm.line.color.rgb = LIJN
    vorm.line.width = Pt(0.75)
    vorm.shadow.inherit = False
    vorm.adjustments[0] = 0.03
    return vorm


MONO = "Consolas"


def tekstblok(dia, links, boven, breedte, hoogte, regels):
    """
    regels: (tekst, puntgrootte, vet, kleur, ruimte_ervoor) -- met optioneel een
    zesde element: de naam van een lettertype.

    Dat zesde is er voor code. In Arial lijnen kolommen die je met spaties hebt
    uitgevuld niet uit, want elk teken is even breed behalve in een monospace
    lettertype. Zet code dus op MONO en niet op "vier spaties en hopen".
    """
    vak = dia.shapes.add_textbox(links, boven, breedte, hoogte)
    tf = vak.text_frame
    tf.word_wrap = True
    for i, regel in enumerate(regels):
        tekst, grootte, vet, kleur, ruimte = regel[:5]
        lettertype = regel[5] if len(regel) > 5 else None
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = tekst
        p.font.size = Pt(grootte)
        p.font.bold = vet
        p.font.color.rgb = kleur
        if lettertype:
            p.font.name = lettertype
        if ruimte:
            p.space_before = Pt(ruimte)
    return vak
