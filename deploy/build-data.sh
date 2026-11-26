#!/usr/bin/env bash
# Fill the generated-data volumes for every app page. Run inside the image:
#   docker compose -f deploy/compose.yaml run --rm build-data            # everything missing
#   docker compose -f deploy/compose.yaml run --rm build-data --force    # everything, again
# Order matters: the exports read the map data that fetch_data.py downloads.
set -euo pipefail
cd /app
force=0; [[ "${1:-}" == "--force" ]] && force=1

step() {  # step <output that marks it done> <command...>
    local marker=$1; shift
    if [[ $force -eq 0 && -e $marker ]]; then echo "== skip (have $marker): $*"; return; fi
    echo "== $(date -u +%H:%M:%S) $*"; local t0=$SECONDS
    "$@"
    echo "== done in $((SECONDS - t0)) s"
}

step data/cache/ishikari/study_drive.graphml python scripts/fetch_data.py --area ishikari  # Warm Ishikari, Weather
step out/heat_story/story.json            python scripts/export_heat_story.py           # Map, Proposals base map
step out/proposals/proposals.json         python scripts/export_proposals.py            # Proposals (a few minutes)
step out/siting/siting.json               python scripts/export_siting.py --workers "$(nproc)"  # Siting (~15 min on 8 cores)
step results/weather_years                python experiments/weather_years/run.py       # Weather results panel
echo "== all data in place"
