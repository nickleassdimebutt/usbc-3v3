"""USB-C → 3.3V LDO power board — topology only.

The exact same circuit, expressed via circuit_toolkit blocks. Parameterised
on the LDO output voltage so the same source builds usbc-3v3 / usbc-5v0 /
usbc-1v8 / usbc-2v5 — every AMS1117 variant is SOT-223, so the layout is
reused unchanged.
"""
from circuit_toolkit import Board
from circuit_toolkit.blocks import (
    usbc_power, ams1117_ldo, led_indicator, pin_header, m2_mounting_hole,
)


def variant_name(output_v: float) -> str:
    """Canonical board name for a given LDO output voltage."""
    if output_v == int(output_v):
        return f"usbc-{int(output_v)}v0"
    # 3.3 → "usbc-3v3"
    return f"usbc-{str(output_v).replace('.', 'v')}"


def output_net_name(output_v: float) -> str:
    """Canonical output rail net name (matches what ams1117_ldo emits by default)."""
    if output_v == int(output_v):
        return f"+{int(output_v)}V"
    return f"+{str(output_v).replace('.', 'V')}"


def build(output_v: float = 3.3, label_v: str | None = None) -> Board:
    """Build the topology for a given LDO output voltage.

    Args:
        output_v: 3.3, 5.0, 1.8, or 2.5 — must be a supported AMS1117 variant.
        label_v: optional override for the silkscreen pin-header label.
                 Defaults to the rail name without the '+' prefix.
    """
    name = variant_name(output_v)
    board = Board(name, size=(48, 30))

    # USB-C power input + CC pulldowns (R1, R2)
    vbus, gnd, cc1, cc2 = usbc_power(board, ref="J1", cc_pulldowns="5.1k")

    # AMS1117-x LDO with 2× 10µF input caps and 10µF + 100nF output caps
    vout = ams1117_ldo(
        board, ref="U1",
        vin=vbus, gnd=gnd, output_voltage=output_v,
        in_caps=["10uF/0805", "10uF/0805"],
        out_caps=["10uF/0805", "100nF/0402"],
    )

    # Power-good LED (D1) with auto-sized resistor (R3) — reuse 1k for any
    # supply ≥ 2.5V; below that the supply can't light a red LED reliably.
    led_indicator(
        board, ref_led="D1", ref_resistor="R3",
        vin=vout, gnd=gnd, color="red", current_ma=1.3,
        supply_voltage=output_v,
    )

    # Output header (J2) — silkscreen labelled with the rail
    if label_v is None:
        label_v = output_net_name(output_v)[1:] + "_OUT"  # strip the '+'
    pin_header(board, ref="J2", pins=2, label=label_v, nets=[vout, gnd])

    # Four M2 mounting holes
    for ref in ("H1", "H2", "H3", "H4"):
        m2_mounting_hole(board, ref=ref)

    return board


if __name__ == "__main__":
    print(build())
