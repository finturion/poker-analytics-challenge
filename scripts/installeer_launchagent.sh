#!/bin/zsh
# Zet de wekelijkse DataCamp-snapshot klaar als LaunchAgent (maandag 11:00).
#
# Waarom hier een kopieerstap zit: launchd mag niets in iCloud Drive lezen.
# Een agent die rechtstreeks naar deze projectmap wijst, faalt met
# "Operation not permitted". Daarom draait de wekelijkse run vanuit een
# lokale map buiten iCloud, en zet dit script daar de actuele versie neer.
#
# Draai dit script opnieuw na elke wijziging in datacamp_snapshot.py,
# in de klaslijst of in de plist. Het is idempotent.
#
# Gebruik:  ./installeer_launchagent.sh

set -eu
HIER="${0:A:h}"
LOKAAL="$HOME/Library/Application Support/datacamp-snapshot"
LABEL="nl.finturion.datacamp-snapshot"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$LOKAAL" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

for bestand in datacamp_snapshot.py datacamp_snapshot_wekelijks.sh klaslijst_datacamp.csv; do
  if [ ! -r "$HIER/$bestand" ]; then
    echo "FOUT: $HIER/$bestand ontbreekt."
    exit 1
  fi
  cp "$HIER/$bestand" "$LOKAAL/$bestand"
done
chmod 600 "$LOKAAL/klaslijst_datacamp.csv"   # bevat studentnummers en e-mailadressen
chmod +x "$LOKAAL/datacamp_snapshot_wekelijks.sh"

cp "$HIER/$LABEL.plist" "$PLIST"
/usr/bin/sed -i '' \
  "s|<string>/Users/jerome/Library/Mobile Documents/.*datacamp_snapshot_wekelijks.sh</string>|<string>$LOKAAL/datacamp_snapshot_wekelijks.sh</string>|" \
  "$PLIST"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Klaar. De agent draait elke maandag om 11:00 vanuit $LOKAAL."
echo "Nu testen:   launchctl kickstart -k gui/$(id -u)/$LABEL"
echo "Log:         ~/Library/Logs/datacamp-snapshot.log"
echo "Stoppen:     launchctl bootout gui/$(id -u)/$LABEL"
