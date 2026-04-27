# usbc-3v3

USB-C → 3.3V LDO power board.  
Input: 5V USB-C (HRO TYPE-C-31-M-12). Output: 3.3V @ up to 800mA (AMS1117-3.3).  
Board size: 50×30mm. 2-layer, JLCPCB-compatible.

## Bill of Materials

| Ref | Value | Footprint |
|-----|-------|-----------|
| J1  | HRO TYPE-C-31-M-12 | USB-C receptacle |
| U1  | AMS1117-3.3 | SOT-223 |
| R1, R2 | 5.1kΩ | 0402 — CC pull-downs |
| C1, C2 | 10µF/10V | 0805 — VBUS bypass |
| C3  | 10µF/10V | 0805 — 3V3 output bulk |
| C4  | 100nF | 0402 — 3V3 output bypass |
| R3  | 1kΩ | 0402 — LED current limit |
| D1  | RED LED | 0805 |
| J2  | 3V3_OUT | 2-pin 2.54mm header |
| H1–H4 | — | M2 mounting holes |

---

## Verification & Bringup

### Running verification

```bash
# DRC only (fast — always run before ordering)
./verify.sh

# DRC + gerbers + drill + CPL + BOM
./verify.sh --fab

# Above + iBOM + 3D renders (needs extra KiBot deps — Linux recommended)
./verify.sh --all
```

Exit code 0 = all checks passed. Exit code 1 = one or more failures.

### Output locations

| Directory | Contents | Committed to git |
|-----------|----------|-----------------|
| `output/drc/` | DRC report (`drc_report.txt`) | ✅ yes |
| `output/render/` | 3D PNG renders (top + bottom) | ✅ yes |
| `output/ibom/` | Interactive HTML BOM | ✅ yes |
| `output/docs/` | Schematic PDF | ✅ yes |
| `output/fab/` | Gerbers, drill, CPL, BOM | ❌ no — rebuild on demand |

Committed outputs let you **diff what changed** between revisions:
```bash
git diff v1.0..v1.1 -- output/drc/drc_report.txt   # did DRC errors change?
git diff v1.0..v1.1 -- output/render/render_top.png # did the layout change?
```

### After assembly — filling out bringup.md

1. Open `bringup.md`
2. Work through each section in order (visual → continuity → smoke → rails → functional)
3. Fill in the **measured** and **pass/fail** columns as you go
4. Commit the completed checklist: `git add bringup.md && git commit -m "bringup: rev X pass"`

The checklist is pre-populated with expected values derived from the schematic (CC pull-down = 5.1kΩ to GND, 3V3 rail = 3.235–3.365V, quiescent current ≈6–10mA, etc.).
