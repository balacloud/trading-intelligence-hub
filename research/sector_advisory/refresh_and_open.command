#!/bin/bash
# Double-click this file in Finder to regenerate the Sector/Theme Advisory
# Panel with fresh Tradier/STA data and open it in your browser -- one click
# instead of two terminal commands. Static HTML can't do this itself (no
# browser sandbox lets a local page run Python or read your Tradier token),
# so this is the practical middle ground: still fully local/static, nothing
# new left running in the background.
cd "$(dirname "$0")"

echo "Regenerating Sector/Theme Advisory Panel..."
python3 generate_sector_advisory.py --output sector_advisory.html
STATUS=$?

if [ $STATUS -eq 0 ]; then
    open sector_advisory.html
else
    echo ""
    echo "Generation failed (exit $STATUS) -- not opening a stale/missing report."
fi

echo ""
read -p "Press Enter to close this window..."
