import sys, copy
sys.path.insert(0, "api")
import datacamp_rooster as r

ok, fout = 0, []
def check(label, cond, detail=""):
    global ok
    if cond: ok += 1
    else: fout.append(f"{label} {detail}")

PEIL = "2026-10-15"  # ná alle deadlines
ALLES_AF = {c["titel"]: "2026-09-01" for c in r.ROOSTER}
NIETS_AF = {}

# --- 1. gedrag ongewijzigd zolang alles verplicht is ---
v = r.samenvatting(ALLES_AF, PEIL)
check("alles af -> af == totaal", v["af"] == v["totaal"] == 11, v)
check("alles af -> niets gemist", v["gemist"] == [])
v = r.samenvatting(NIETS_AF, PEIL)
check("niets af -> alles gemist", len(v["gemist"]) == 11, v["gemist"])
check("verstreken telt alle 11", v["verstreken"] == 11)
check("aanbevolen_totaal is 0", v["aanbevolen_totaal"] == 0)

# --- 2. nu drie courses op aanbevolen zetten ---
origineel = copy.deepcopy(r.ROOSTER)
AANBEVOLEN = {"Introduction to Data Visualization with Seaborn",
              "Exploratory Data Analysis in Python",
              "Data Communication Concepts"}
for item in r.ROOSTER:
    item["verplicht"] = item["titel"] not in AANBEVOLEN

v = r.samenvatting(NIETS_AF, PEIL)
check("totaal telt alleen verplicht", v["totaal"] == 8, v["totaal"])
check("gemist telt alleen verplicht", len(v["gemist"]) == 8, v["gemist"])
check("aanbevolen niet in gemist", not any(c in v["gemist"] for c in ("VA 2", "IDS 6", "VA 5")), v["gemist"])
check("aanbevolen_totaal is 3", v["aanbevolen_totaal"] == 3)
check("aanbevolen_af is 0", v["aanbevolen_af"] == 0)

# alleen de aanbevolen gedaan
alleen_aanbevolen = {t: "2026-09-01" for t in AANBEVOLEN}
v = r.samenvatting(alleen_aanbevolen, PEIL)
check("aanbevolen af telt apart", v["aanbevolen_af"] == 3, v)
check("verplicht blijft 0 af", v["af"] == 0)
check("en die 8 zijn wel gemist", len(v["gemist"]) == 8)

# --- 3. status per course ---
regels = r.status_per_course(NIETS_AF, PEIL)
aanb = [x for x in regels if not x["verplicht"]]
check("aanbevolen nooit 'gemist'", all(x["status"] == r.OPEN for x in aanb), [x["status"] for x in aanb])
verpl = [x for x in regels if x["verplicht"]]
check("verplicht wel 'gemist'", all(x["status"] == r.GEMIST for x in verpl))
check("verplicht-veld komt mee", all("verplicht" in x for x in regels))

# een aanbevolen course die te laat af is, blijft 'te laat af' (geen alarm, wel eerlijk)
laat = {t: "2026-10-14" for t in AANBEVOLEN}
regels = r.status_per_course(laat, PEIL)
check("aanbevolen te laat -> 'te laat af'",
      all(x["status"] == r.AF_TE_LAAT for x in regels if not x["verplicht"]))

r.ROOSTER[:] = origineel
print(f"{ok} controles geslaagd, {len(fout)} mislukt")
for f in fout: print("  FOUT:", f)
raise SystemExit(1 if fout else 0)
