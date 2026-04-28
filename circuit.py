"""USB-C → 3.3V LDO power board — topology only.

The exact same circuit as scripts/build_board.py, expressed via circuit_toolkit
blocks. ~25 lines of intent.
"""
from circuit_toolkit import Board
from circuit_toolkit.blocks import (
    usbc_power, ams1117_ldo, led_indicator, pin_header, m2_mounting_hole,
)


def build() -> Board:
    board = Board("usbc-3v3", size=(48, 30))

    # USB-C power input + CC pulldowns (R1, R2)
    vbus, gnd, cc1, cc2 = usbc_power(board, ref="J1", cc_pulldowns="5.1k")

    # AMS1117-3.3 with 2× 10µF input caps (C1, C2) and 10µF + 100nF output caps (C3, C4)
    v3v3 = ams1117_ldo(
        board, ref="U1",
        vin=vbus, gnd=gnd, output_voltage=3.3,
        in_caps=["10uF/0805", "10uF/0805"],
        out_caps=["10uF/0805", "100nF/0402"],
    )

    # Power-good LED (D1) with 1kΩ current-limit resistor (R3)
    led_indicator(
        board, ref_led="D1", ref_resistor="R3",
        vin=v3v3, gnd=gnd, color="red", current_ma=1.3,
    )

    # 3V3 output header (J2)
    pin_header(board, ref="J2", pins=2, label="3V3_OUT", nets=[v3v3, gnd])

    # Four M2 mounting holes
    for ref in ("H1", "H2", "H3", "H4"):
        m2_mounting_hole(board, ref=ref)

    return board


if __name__ == "__main__":
    print(build())
