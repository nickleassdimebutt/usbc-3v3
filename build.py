"""USB-C → 3.3V LDO — orchestrator.

Reads circuit.py (topology) + layout.py (positions/routes) and generates the
fabrication / documentation deliverables. Modes (composable):

    build.py                    PCB + schematic SVG + BOM (default)
    build.py --datasheet        adds 3D renders + LT-style PDF
    build.py --sim              adds 6 SPICE pre-flight plots
    build.py --datasheet --sim  full v2 set, all artefacts in one pass

Run with KiCad's bundled Python so pcbnew is available:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build.py [flags]
"""
import argparse
import sys
from pathlib import Path

import circuit
import layout
from circuit_toolkit.builders import build_pcb, build_schematic
from circuit_toolkit.fab import write_bom


PROJECT_DIR = Path(__file__).resolve().parent
PCB_PATH = PROJECT_DIR / "usbc-3v3.kicad_pcb"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="usbc-3v3 build orchestrator")
    p.add_argument("--datasheet", action="store_true",
                   help="render 3D PNGs and assemble the LT-style datasheet PDF")
    p.add_argument("--sim", action="store_true",
                   help="run six SPICE pre-flight analyses (transient, "
                        "load step, line/load reg, temp sweep, Monte Carlo)")
    p.add_argument("--monte-carlo-runs", type=int, default=100,
                   help="Monte Carlo iteration count (default 100)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    modes = ["pcb", "schematic", "bom"] \
        + (["sim"] if args.sim else []) \
        + (["datasheet"] if args.datasheet else [])
    print(f"=== usbc-3v3 build  ({', '.join(modes)}) ===")

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

    schematic_svg = PROJECT_DIR / "output/docs/schematic.svg"
    print(f"  → Schematic: {schematic_svg.relative_to(PROJECT_DIR)}")
    try:
        build_schematic(board, schematic_svg)
    except Exception as e:
        print(f"     [warning] schematic generation failed: {e}")

    print(f"  → BOM: output/fab/bom/")
    write_bom(board, PROJECT_DIR / "output/fab/bom")

    sim_dir = PROJECT_DIR / "output/sim"
    if args.sim:
        print(f"\n  → SPICE pre-flight: {sim_dir.relative_to(PROJECT_DIR)}/")
        from circuit_toolkit.sim import simulate_all
        paths = simulate_all(board, sim_dir,
                             monte_carlo_runs=args.monte_carlo_runs)
        for name, p in paths.items():
            print(f"     {name:<14} {p.name}")

    if args.datasheet:
        render_dir = PROJECT_DIR / "output/render"
        docs_dir = PROJECT_DIR / "output/docs"
        print(f"\n  → 3D renders: {render_dir.relative_to(PROJECT_DIR)}/")
        from circuit_toolkit.builders import render_pcb, build_datasheet
        render_pcb(PCB_PATH, render_dir, sides=("top", "bottom"))

        pdf_path = docs_dir / "datasheet.pdf"
        print(f"  → Datasheet PDF: {pdf_path.relative_to(PROJECT_DIR)}")
        build_datasheet(
            board, pdf_path,
            rev="0.1",
            description="USB-C → 3.3V LDO power board",
            render_top=render_dir / "render_top.png",
            render_bottom=render_dir / "render_bottom.png",
            schematic_svg=schematic_svg,
            bringup_md=PROJECT_DIR / "bringup.md",
            sim_dir=sim_dir if args.sim else None,
        )

    print("\nDone. Run ./verify.sh to DRC + fab outputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
