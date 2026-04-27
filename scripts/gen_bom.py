#!/usr/bin/env python
"""
gen_bom.py — Generate BOM from PCB file (no schematic required).
Run with KiCad's Python: C:/Program Files/KiCad/10.0/bin/python.exe
"""
import sys, csv, os
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin\Lib\site-packages")
import pcbnew

PCB = os.path.join(os.path.dirname(__file__), "..", "usbc-3v3.kicad_pcb")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "fab", "bom")
os.makedirs(OUT_DIR, exist_ok=True)

board = pcbnew.LoadBoard(PCB)

rows = []
for fp in board.GetFootprints():
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
        continue
    rows.append({
        "Reference": fp.GetReference(),
        "Value":     fp.GetValue(),
        "Footprint": fp.GetFPIDAsString(),
        "Side":      "Front" if fp.IsFlipped() is False else "Back",
    })

rows.sort(key=lambda r: r["Reference"])

# Group for BOM
groups = {}
for r in rows:
    key = (r["Value"], r["Footprint"])
    if key not in groups:
        groups[key] = {"refs": [], "Value": r["Value"], "Footprint": r["Footprint"]}
    groups[key]["refs"].append(r["Reference"])

# Write flat CSV
flat = os.path.join(OUT_DIR, "bom.csv")
with open(flat, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Reference", "Value", "Footprint", "Side"])
    for r in rows:
        w.writerow([r["Reference"], r["Value"], r["Footprint"], r["Side"]])
print(f"Wrote {flat}")

# Write JLCPCB grouped CSV
jlc = os.path.join(OUT_DIR, "bom_jlcpcb.csv")
with open(jlc, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Qty", "Comment", "Footprint"])
    for (val, fp), g in sorted(groups.items()):
        refs = ",".join(sorted(g["refs"]))
        w.writerow([refs, len(g["refs"]), val, fp])
print(f"Wrote {jlc}")

print(f"\nBOM summary: {len(rows)} components, {len(groups)} unique values")
for (val, fp), g in sorted(groups.items()):
    print(f"  {len(g['refs']):2d}× {val:15s}  {','.join(g['refs'])}")
