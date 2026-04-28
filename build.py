"""USB-C → 3.3V LDO — orchestrator.

Reads circuit.py (topology) + layout.py (positions/routes) and generates:
    usbc-3v3.kicad_pcb         (via pcbnew, DRC-clean)
    output/docs/schematic.svg  (via netlistsvg)
    output/fab/bom/bom.csv     (BOM with LCSC numbers)
    output/fab/bom/bom_jlcpcb.csv

Run with KiCad's Python so pcbnew is available:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build.py
"""
from pathlib import Path
import sys

import circuit
import layout
from circuit_toolkit.builders import build_pcb, build_schematic
from circuit_toolkit.fab import write_bom


PROJECT_DIR = Path(__file__).resolve().parent
PCB_PATH = PROJECT_DIR / "usbc-3v3.kicad_pcb"


def main() -> int:
    print("=== usbc-3v3 build ===")
    board = circuit.build()
    print(f"  topology: {board}")

    print(f"\n  → PCB: {PCB_PATH.name}")
    build_pcb(
        board,
        positions=layout.positions,
        output=PCB_PATH,
        tracks=layout.tracks,
        vias=layout.vias,
        zones=layout.zones,
        pad_zone_full=layout.pad_zone_full,
        ref_text_overrides=layout.ref_text_overrides,
        outline=layout.outline,
    )

    print(f"  → Schematic: output/docs/schematic.svg")
    try:
        build_schematic(board, PROJECT_DIR / "output/docs/schematic.svg")
    except Exception as e:
        print(f"     [warning] schematic generation failed: {e}")

    print(f"  → BOM: output/fab/bom/")
    write_bom(board, PROJECT_DIR / "output/fab/bom")

    print("\nDone. Run ./verify.sh to DRC + fab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
