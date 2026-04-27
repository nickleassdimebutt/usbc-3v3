# USB-C → 3.3V LDO — Bringup Checklist

Board: `usbc-3v3`  
Schematic nets: `VBUS` (5V in), `GND`, `+3V3` (LDO out), `CC1`, `CC2`, `N_LED`  
Fill in **measured** and **pass/fail** columns during bringup.

---

## 1. Visual Inspection (before powering on)

- [ ] J1 (USB-C) — seated flush, no solder bridges between SMD signal pads — expected: no bridges — measured: ___ — pass/fail: ___
- [ ] J1 shield PTH pins (2×) — fully soldered, not lifted — expected: solid fillet — measured: ___ — pass/fail: ___
- [ ] U1 (AMS1117-3.3, SOT-223) — pin 1 (GND) at bottom, large tab (VOUT/pin 2) centred — expected: correct orientation per silkscreen arrow — measured: ___ — pass/fail: ___
- [ ] U1 tab pad — soldered to large centre pad, no voids visible — expected: ≥75% coverage — measured: ___ — pass/fail: ___
- [ ] R1, R2 (5.1kΩ 0402, CC resistors) — placed left of J1, one above/below centre — expected: no tombstoning — measured: ___ — pass/fail: ___
- [ ] C1, C2 (10µF 0805, VBUS bypass) — near J1, correct polarity if electrolytic (these are ceramic — no polarity) — expected: flat, no tilt — measured: ___ — pass/fail: ___
- [ ] C3 (10µF 0805, 3V3 output bulk) — right of U1 — expected: no solder bridges — measured: ___ — pass/fail: ___
- [ ] C4 (100nF 0402, 3V3 output bypass) — adjacent to C3 — expected: no solder bridges — measured: ___ — pass/fail: ___
- [ ] R3 (1kΩ 0402, LED current limit) — between C3 and D1 — expected: no tombstoning — measured: ___ — pass/fail: ___
- [ ] D1 (LED 0805, red) — cathode (line on package) toward J2 side — expected: correct orientation per silkscreen — measured: ___ — pass/fail: ___
- [ ] J2 (2-pin 2.54mm header) — right edge, pin 1 square pad = +3V3 — expected: pins straight — measured: ___ — pass/fail: ___
- [ ] H1–H4 (M2 mounting holes) — four corners, no solder in holes — expected: clear — measured: ___ — pass/fail: ___
- [ ] GND copper pour — visible on F.Cu between components — expected: continuous flood — measured: ___ — pass/fail: ___

---

## 2. Continuity Checks (DMM in continuity/diode mode, board unpowered)

- [ ] USB-C shield (J1 NPTH pins) to GND (J2 pin 2) — expected: 0Ω (continuity beep) — measured: ___ — pass/fail: ___
- [ ] J1 A1/A12/B1/B12 (GND pins) to J2 pin 2 (GND) — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] J1 A4/B9 (VBUS pins) to C1 pad 1 (VBUS) — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] J1 A5 (CC1) to R1 pin 1 — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] J1 B5 (CC2) to R2 pin 1 — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] R1 pin 2, R2 pin 2 to GND — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] U1 pin 3 (VIN) to VBUS net — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] U1 pin 1 (GND) to GND — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] U1 pin 2/tab (VOUT) to J2 pin 1 (+3V3) — expected: 0Ω — measured: ___ — pass/fail: ___
- [ ] VBUS to GND (short check) — expected: >10kΩ (no short) — measured: ___ — pass/fail: ___
- [ ] +3V3 to GND (short check) — expected: >1kΩ (caps → shows charging, not short) — measured: ___ — pass/fail: ___

---

## 3. Smoke Test (current-limited bench supply)

Set supply to **5.0V, current limit 100mA** before connecting.

- [ ] Connect bench supply + to J1 VBUS / − to GND (or use USB-C cable to a USB power meter) — expected: no smoke, no burning smell — measured: ___ — pass/fail: ___
- [ ] Inrush current settles — expected: current drops to steady-state within 100ms — measured: ___ — pass/fail: ___
- [ ] Steady-state current at 5V, no load — expected: 6–10mA (AMS1117 Iq ≈5mA + LED ≈1.3mA) — measured: ___ mA — pass/fail: ___
- [ ] D1 (red LED) illuminates — expected: lit, red — measured: ___ — pass/fail: ___
- [ ] U1 temperature after 60s, no load — expected: warm but not hot (<50°C) — measured: ___ °C — pass/fail: ___

---

## 4. Power Rail Checks (DMM, board powered at 5V)

- [ ] VBUS rail — probe C1/C2 pad 1 (+) to GND — expected: 4.75–5.25V — measured: ___ V — pass/fail: ___
- [ ] +3V3 rail — probe J2 pin 1 (+) to J2 pin 2 (GND), or C3 pad 1 to GND — expected: 3.235–3.365V (AMS1117 ±2%) — measured: ___ V — pass/fail: ___
- [ ] CC1 — probe R1 pad 1 to GND — expected: ~0V (pulled to GND via R1=5.1kΩ, USB host sources CC) — measured: ___ V — pass/fail: ___
- [ ] CC2 — probe R2 pad 1 to GND — expected: ~0V same — measured: ___ V — pass/fail: ___
- [ ] N_LED (anode of D1 / R3 pad 2) — expected: +3V3 − Vf_LED ≈ 1.2–1.5V — measured: ___ V — pass/fail: ___

---

## 5. Functional Tests

- [ ] **3V3 line regulation** — vary input 4.75V→5.25V, measure +3V3 — expected: <±0.1V variation — measured: ___ — pass/fail: ___
- [ ] **3V3 load test** — attach 330Ω load across J2 (≈10mA load) — expected: +3V3 stays ≥3.235V — measured: ___ V — pass/fail: ___
- [ ] **3V3 load test (max)** — attach 33Ω load across J2 (≈100mA), U1 max 800mA — expected: +3V3 stays ≥3.235V, U1 <70°C — measured: ___ V / ___ °C — pass/fail: ___
- [ ] **Power dissipation check** at 100mA load — U1 dissipates (5V−3.3V)×0.1A = 170mW — expected: U1 warm but not burning — measured: ___ — pass/fail: ___
- [ ] **Ripple** — scope +3V3 with 100mA load — expected: <50mV pk-pk — measured: ___ mV — pass/fail: ___
- [ ] **J2 output header** — confirm pin 1 = +3V3, pin 2 = GND with DMM — expected: 3.3V between pins — measured: ___ V — pass/fail: ___

---

## Notes

_Space for any anomalies found during bringup:_

```
Date: ___________
Tester: ___________
Supply used: ___________
Notes:
```
