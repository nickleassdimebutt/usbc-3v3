"""USB-C → 3.3V LDO — orchestrator.

One source builds an entire AMS1117-family product line. Modes (composable):

    build.py                          PCB + schematic SVG + BOM (default 3.3 V)
    build.py --datasheet              adds 3D renders + LT-style PDF
    build.py --sim                    adds 6 SPICE pre-flight plots
    build.py --variants 3.3 5.0 1.8   builds three boards, one per output V
    build.py --datasheet --sim --variants 3.3 5.0 1.8
                                       full v2 set, every variant, in one pass

Variant outputs land at ``variants/<board-name>/{<name>.kicad_pcb, output/...}``.
The default 3.3 V build (no --variants) writes to the project root for
back-compat with the canonical usbc-3v3 design.

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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="usbc-3v3 build orchestrator")
    p.add_argument("--datasheet", action="store_true",
                   help="render 3D PNGs and assemble the LT-style datasheet PDF")
    p.add_argument("--sim", action="store_true",
                   help="run six SPICE pre-flight analyses")
    p.add_argument("--monte-carlo-runs", type=int, default=100,
                   help="Monte Carlo iteration count (default 100)")
    p.add_argument("--variants", nargs="+", type=float, default=None,
                   metavar="V",
                   help="build one board per listed output voltage (e.g. "
                        "--variants 3.3 5.0 1.8). Without this flag, "
                        "builds 3.3 V into the project root.")
    return p.parse_args(argv)


def _build_one(output_v: float, project_root: Path, args: argparse.Namespace) -> int:
    """Build a single variant. `project_root` is where artefacts land
    (PCB at ``<root>/<name>.kicad_pcb``, outputs under ``<root>/output/``)."""
    board = circuit.build(output_v=output_v)
    out_net = circuit.output_net_name(output_v)
    layout_data = layout.get_layout(output_net=out_net)

    pcb_path = project_root / f"{board.name}.kicad_pcb"
    project_root.mkdir(parents=True, exist_ok=True)

    print(f"  topology: {board}")
    print(f"  rail: {out_net}")
    print(f"  → PCB: {pcb_path.relative_to(PROJECT_DIR)}")
    build_pcb(
        board,
        positions=layout_data["positions"],
        output=pcb_path,
        tracks=layout_data["tracks"],
        vias=layout_data["vias"],
        zones=layout_data["zones"],
        pad_zone_full=layout_data["pad_zone_full"],
        ref_text_overrides=layout_data["ref_text_overrides"],
        outline=layout_data["outline"],
    )

    schematic_svg = project_root / "output/docs/schematic.svg"
    print(f"  → Schematic: {schematic_svg.relative_to(PROJECT_DIR)}")
    try:
        build_schematic(board, schematic_svg)
    except Exception as e:
        print(f"     [warning] schematic generation failed: {e}")

    print(f"  → BOM: {(project_root / 'output/fab/bom').relative_to(PROJECT_DIR)}/")
    write_bom(board, project_root / "output/fab/bom")

    sim_dir = project_root / "output/sim"
    if args.sim:
        print(f"\n  → SPICE pre-flight: {sim_dir.relative_to(PROJECT_DIR)}/")
        from circuit_toolkit.sim import simulate_all
        paths = simulate_all(board, sim_dir,
                             monte_carlo_runs=args.monte_carlo_runs)
        for name, p in paths.items():
            print(f"     {name:<14} {p.name}")

    if args.datasheet:
        render_dir = project_root / "output/render"
        docs_dir = project_root / "output/docs"
        print(f"\n  → 3D renders: {render_dir.relative_to(PROJECT_DIR)}/")
        from circuit_toolkit.builders import (
            render_pcb, build_datasheet, plot_pcbdraw,
            build_hierarchical_schematic,
        )
        render_pcb(pcb_path, render_dir, sides=("top", "bottom"))

        print(f"  → pcbdraw stylized views")
        try:
            plot_pcbdraw(pcb_path, render_dir,
                         sides=("front", "back"), to_png=True, dpi=200)
            pcbdraw_front = render_dir / "pcbdraw_front.png"
            pcbdraw_back = render_dir / "pcbdraw_back.png"
        except Exception as e:
            print(f"     [warning] pcbdraw failed: {e}")
            pcbdraw_front = None
            pcbdraw_back = None

        print(f"  → hierarchical schematics")
        hier_dir = docs_dir / "hierarchical"
        try:
            schematic_blocks = build_hierarchical_schematic(board, hier_dir)
        except Exception as e:
            print(f"     [warning] hierarchical schematic failed: {e}")
            schematic_blocks = None

        pdf_path = docs_dir / "datasheet.pdf"
        print(f"  → Datasheet PDF: {pdf_path.relative_to(PROJECT_DIR)}")
        build_datasheet(
            board, pdf_path,
            rev="0.1",
            description=f"USB-C → {output_v:g} V LDO power board",
            render_top=render_dir / "render_top.png",
            render_bottom=render_dir / "render_bottom.png",
            pcbdraw_front=pcbdraw_front,
            pcbdraw_back=pcbdraw_back,
            schematic_svg=schematic_svg,
            schematic_blocks=schematic_blocks,
            bringup_md=PROJECT_DIR / "bringup.md",
            sim_dir=sim_dir if args.sim else None,
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    targets: list[tuple[float, Path]]
    if args.variants:
        targets = [
            (v, PROJECT_DIR / "variants" / circuit.variant_name(v))
            for v in args.variants
        ]
    else:
        # back-compat: default 3.3V at project root
        targets = [(3.3, PROJECT_DIR)]

    modes = ["pcb", "schematic", "bom"] \
        + (["sim"] if args.sim else []) \
        + (["datasheet"] if args.datasheet else [])
    print(f"=== usbc-3v3 build  ({', '.join(modes)})  "
          f"variants: {[circuit.variant_name(v) for v, _ in targets]} ===")

    rc = 0
    for output_v, project_root in targets:
        print(f"\n--- {circuit.variant_name(output_v)} ---")
        rc |= _build_one(output_v, project_root, args)

    print("\nDone. Run ./verify.sh to DRC + fab outputs.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
