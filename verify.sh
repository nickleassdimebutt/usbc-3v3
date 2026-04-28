#!/usr/bin/env bash
# verify.sh — DRC (kicad-cli) + fab outputs (KiBot + pcbnew BOM)
# Usage: ./verify.sh         — DRC only
#        ./verify.sh --fab   — DRC + gerbers/drill/CPL/BOM
#        ./verify.sh --all   — above + iBOM + 3D renders (needs extra deps)
set -euo pipefail

KICAD_CLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
KICAD_PY="C:/Program Files/KiCad/10.0/bin/python.exe"
KIBOT="C:/Users/nicho/OneDrive/Documents/KiCad/10.0/3rdparty/Python311/Scripts/kibot.exe"
PCB="usbc-3v3.kicad_pcb"
CONFIG=".kibot.yaml"
FAILS=0
PASSES=0
LOG_DIR="${TMPDIR:-/tmp}"

check() {
  local name="$1"; shift
  printf "  %-20s" "[$name]"
  local log="$LOG_DIR/verify_${name// /_}.log"
  if "$@" >"$log" 2>&1; then
    echo " PASS"; PASSES=$((PASSES+1))
  else
    echo " FAIL"; FAILS=$((FAILS+1))
    grep -E "ERROR|error" "$log" | head -3 || tail -3 "$log"
  fi
}

kibot_out() {
  check "$1" "$KIBOT" -c "$CONFIG" -b "$PCB" "$1"
}

echo "=== usbc-3v3 verification ==="

# DRC — always runs
mkdir -p output/drc
check "DRC" "$KICAD_CLI" pcb drc \
  --output output/drc/drc_report.txt \
  --units mm \
  "$PCB"

# Parse DRC report — count errors vs warnings separately
if [ -f output/drc/drc_report.txt ]; then
  errors=$(grep -c "; error" output/drc/drc_report.txt || true)
  warnings=$(grep -c "; warning" output/drc/drc_report.txt || true)
  unconn_line=$(grep -E "Found [^0].*unconnected" output/drc/drc_report.txt || true)
  echo "  DRC: ${errors:-0} errors, ${warnings:-0} warnings"
  if [ "${errors:-0}" -gt 0 ] || [ -n "$unconn_line" ]; then
    [ -n "$unconn_line" ] && echo "    $unconn_line"
    FAILS=$((FAILS+1)); PASSES=$((PASSES-1))
  fi
fi

if [[ "${1:-}" == "--fab" ]] || [[ "${1:-}" == "--all" ]]; then
  echo "--- fab outputs ---"
  mkdir -p output/fab/gerbers output/fab/cpl output/fab/bom
  kibot_out gerbers
  kibot_out drill
  kibot_out cpl
  check "BOM" "$KICAD_PY" scripts/gen_bom.py
fi

if [[ "${1:-}" == "--all" ]]; then
  echo "--- extended outputs (need extra deps) ---"
  kibot_out ibom
  kibot_out render_top
  kibot_out render_bottom
fi

echo ""
echo "=== RESULT: ${PASSES} passed, ${FAILS} failed ==="
[[ "$FAILS" -eq 0 ]]
