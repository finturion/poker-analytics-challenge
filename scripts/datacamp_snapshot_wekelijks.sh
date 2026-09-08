#!/bin/zsh
# Wekelijkse DataCamp-snapshot, aangeroepen door de LaunchAgent
# nl.finturion.datacamp-snapshot (maandag 11:00).
#
# Dit script draait NIET vanuit de projectmap in iCloud, maar vanuit de map
# waarin installeer_launchagent.sh het heeft neergezet
# (~/Library/Application Support/datacamp-snapshot). Reden: launchd mag
# bestanden in iCloud Drive niet lezen -- een agent die daarheen wijst faalt
# met "Operation not permitted". Alle paden hieronder zijn daarom relatief aan
# de map van dit script zelf.
#
# Waarom een wrapper en niet python direct in de plist: launchd start met een
# vrijwel lege omgeving (geen PATH, geen env vars uit je shell). Hier zetten we
# dus zelf het pad naar python, halen we het docent-token op, en -- het
# belangrijkste -- laten we een mislukking niet stil zijn. Een scrape die
# maandag om 11:00 faalt terwijl jij er niet naar kijkt, is net zo erg als geen
# scrape: daarom een macOS-melding zodra er iets misgaat.
#
# Het docent-token staat NIET in dit script en niet in de plist. Zet het één
# keer neer, op één van deze twee manieren:
#   Keychain (voorkeur):
#     security add-generic-password -s datacamp-snapshot-docent-token -a "$USER" -w
#     (de -w zonder waarde vraagt het interactief; verschijnt er later een
#      keychain-venster, kies dan "Always Allow")
#   Of een bestand met alleen leesrecht voor jou:
#     mkdir -p ~/.config/datacamp-snapshot
#     printf '%s' '<token>' > ~/.config/datacamp-snapshot/docent-token
#     chmod 600 ~/.config/datacamp-snapshot/docent-token

set -u
PYTHON="/Users/jerome/anaconda3/bin/python3"
HIER="${0:A:h}"
TOKEN_BESTAND="$HOME/.config/datacamp-snapshot/docent-token"

export DATACAMP_KLASLIJST="$HIER/klaslijst_datacamp.csv"
export DATACAMP_UITVOER="$HIER/snapshots"

melding() {
  /usr/bin/osascript -e "display notification \"$1\" with title \"DataCamp-snapshot\"" 2>/dev/null
}

echo "=== $(date '+%Y-%m-%d %H:%M:%S') start wekelijkse DataCamp-snapshot ==="

TOKEN="$(/usr/bin/security find-generic-password -s datacamp-snapshot-docent-token -w 2>/dev/null)"
if [ -z "${TOKEN:-}" ] && [ -r "$TOKEN_BESTAND" ]; then
  TOKEN="$(/bin/cat "$TOKEN_BESTAND")"
fi
if [ -z "${TOKEN:-}" ]; then
  echo "FOUT: geen docent-token gevonden (keychain noch $TOKEN_BESTAND). Zie de uitleg boven in dit script."
  melding "Geen docent-token gevonden. De snapshot is niet gedraaid."
  exit 1
fi

if [ ! -r "$HIER/datacamp_snapshot.py" ]; then
  echo "FOUT: $HIER/datacamp_snapshot.py ontbreekt. Draai installeer_launchagent.sh opnieuw."
  melding "Snapshot-script niet gevonden. Draai installeer_launchagent.sh."
  exit 1
fi

cd "$HIER" || exit 1
POKER_DOCENT_TOKEN="$TOKEN" "$PYTHON" datacamp_snapshot.py --stuur-naar-hub
CODE=$?

if [ $CODE -ne 0 ]; then
  echo "FOUT: datacamp_snapshot.py stopte met code $CODE."
  melding "De snapshot is mislukt (code $CODE). Kijk in ~/Library/Logs/datacamp-snapshot.log."
else
  echo "Klaar."
  melding "Nieuwe DataCamp-stand staat in de hub."
fi
exit $CODE
