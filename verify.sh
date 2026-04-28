#!/usr/bin/env bash
# verify.sh — DRC (kicad-cli) + fab + datasheet + SPICE pre-flight checks.
# Usage: ./verify.sh              — DRC only
#        ./verify.sh --fab        — DRC + gerbers/drill/CPL/BOM
#        ./verify.sh --datasheet  — DRC + 3D renders + datasheet PDF
#        ./verify.sh --sim        — DRC + SPICE pre-flight (6 analyses)
#        ./verify.sh --all        — fab + datasheet + sim + iBOM
# Modes are composable; for example: ./verify.sh --datasheet --sim
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

# Parse mode flags from any position (composable)
WANT_FAB=0; WANT_DATASHEET=0; WANT_SIM=0; WANT_EXTRA=0
for arg in "$@"; do
  case "$arg" in
    --fab)        WANT_FAB=1 ;;
    --datasheet)  WANT_DATASHEET=1 ;;
    --sim)        WANT_SIM=1 ;;
    --all)        WANT_FAB=1; WANT_DATASHEET=1; WANT_SIM=1; WANT_EXTRA=1 ;;
  esac
done

if [[ "$WANT_FAB" -eq 1 ]]; then
  echo "--- fab outputs ---"
  mkdir -p output/fab/gerbers output/fab/cpl output/fab/bom
  kibot_out gerbers
  kibot_out drill
  kibot_out cpl
  check "BOM" "$KICAD_PY" scripts/gen_bom.py
fi

if [[ "$WANT_SIM" -eq 1 ]]; then
  echo "--- SPICE pre-flight ---"
  mkdir -p output/sim
  check "sim (6 plots)" "$KICAD_PY" build.py --sim
  for name in transient load_step line_reg load_reg temp_sweep monte_carlo; do
    if [[ -f "output/sim/${name}.png" ]]; then
      echo "  ✓ output/sim/${name}.png"
    else
      echo "  ✗ output/sim/${name}.png  (missing)"; FAILS=$((FAILS+1))
    fi
  done
fi

if [[ "$WANT_DATASHEET" -eq 1 ]]; then
  echo "--- datasheet ---"
  mkdir -p output/render output/docs
  if [[ "$WANT_SIM" -eq 1 ]]; then
    # sim already ran above — re-run build with --datasheet to embed sim plots.
    check "datasheet (with sim plots)" "$KICAD_PY" build.py --datasheet --sim
  else
    check "datasheet" "$KICAD_PY" build.py --datasheet
  fi
  if [[ -f "output/docs/datasheet.pdf" ]]; then
    size_kb=$(( $(wc -c <"output/docs/datasheet.pdf") / 1024 ))
    echo "  ✓ output/docs/datasheet.pdf  (${size_kb} KB)"
  else
    echo "  ✗ output/docs/datasheet.pdf  (missing)"; FAILS=$((FAILS+1))
  fi
fi

if [[ "$WANT_EXTRA" -eq 1 ]]; then
  echo "--- extended outputs (need extra deps) ---"
  kibot_out ibom
fi

echo ""
echo "=== RESULT: ${PASSES} passed, ${FAILS} failed ==="
[[ "$FAILS" -eq 0 ]]
