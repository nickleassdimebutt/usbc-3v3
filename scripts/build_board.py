"""USB-C → 3.3V LDO power board — headless pcbnew build script.

Circuit:
  J1  USB-C HRO TYPE-C-31-M-12    5V input (VBUS / GND / CC pull-downs)
  U1  AMS1117-3.3 SOT-223          LDO regulator
  C1  10µF 0805 MLCC               Input bulk cap
  C2  100nF 0402 MLCC              Input bypass
  C3  10µF 0805 MLCC               Output bulk cap
  C4  100nF 0402 MLCC              Output bypass
  R1  5.1kΩ 0402                   CC1 pull-down
  R2  5.1kΩ 0402                   CC2 pull-down
  R3  1kΩ 0402                     LED current limit
  D1  LED 0805 red                  Power indicator
  J2  2-pin 2.54mm header          3V3 output

Run with KiCad's bundled Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\build_board.py
"""

import sys
from pathlib import Path
import pcbnew

PROJECT_DIR = Path(__file__).resolve().parent.parent
PCB_PATH    = PROJECT_DIR / "usbc-3v3.kicad_pcb"
FP_BASE     = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

def mm(v): return pcbnew.FromMM(v)
def vec(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def load_fp(lib, name):
    io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    fp = io.FootprintLoad(str(FP_BASE / f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {lib}:{name}")
    return fp

def add_fp(board, lib, name, ref, value, x, y, rot=0):
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(vec(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    board.Add(fp)
    return fp

def ensure_net(board, name):
    n = board.FindNet(name)
    if n is None:
        board.Add(pcbnew.NETINFO_ITEM(board, name))
        board.BuildConnectivity()
        n = board.FindNet(name)
    return n

def pad(fp, num):
    p = fp.FindPadByNumber(num)
    if p is None:
        raise RuntimeError(f"{fp.GetReference()} has no pad {num!r}")
    return p

def track(board, x1, y1, x2, y2, net, w=0.5, layer=None):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(mm(w))
    t.SetLayer(layer or pcbnew.F_Cu)
    t.SetNet(net)
    board.Add(t)

def via(board, x, y, net, drill=0.4, size=0.8):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetDrill(mm(drill))
    v.SetWidth(mm(size))
    v.SetNet(net)
    board.Add(v)

def outline(board, x, y, w, h):
    corners = [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]
    for (x1,y1),(x2,y2) in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(vec(x1, y1))
        seg.SetEnd(vec(x2, y2))
        seg.SetWidth(mm(0.05))
        board.Add(seg)

def main():
    board = pcbnew.LoadBoard(str(PCB_PATH))

    # Wipe prior content (idempotent)
    for t in list(board.GetTracks()):  board.Remove(t)
    for f in list(board.GetFootprints()): board.Remove(f)
    for d in list(board.GetDrawings()): board.Remove(d)

    # ── Nets ──────────────────────────────────────────────────────────────
    VBUS = ensure_net(board, "VBUS")
    GND  = ensure_net(board, "GND")
    V33  = ensure_net(board, "+3V3")
    CC1  = ensure_net(board, "CC1")
    CC2  = ensure_net(board, "CC2")

    # ── Footprints ────────────────────────────────────────────────────────
    # USB-C connector — at left edge, rotated 90° so socket faces left
    j1 = add_fp(board, "Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                "J1", "HRO TYPE-C-31-M-12", 5.5, 15.0, rot=270)

    # AMS1117-3.3 SOT-223 — centre board
    u1 = add_fp(board, "Package_TO_SOT_SMD", "SOT-223-3_TabPin2",
                "U1", "AMS1117-3.3", 22.0, 15.0, rot=270)

    # Input caps — between J1 and U1
    c1 = add_fp(board, "Capacitor_SMD", "C_0805_2012Metric",
                "C1", "10uF/10V", 13.0, 10.5)          # VBUS bulk
    c2 = add_fp(board, "Capacitor_SMD", "C_0402_1005Metric",
                "C2", "100nF", 13.0, 19.5)              # VBUS bypass

    # Output caps — right of U1
    c3 = add_fp(board, "Capacitor_SMD", "C_0805_2012Metric",
                "C3", "10uF/10V", 30.0, 10.5)           # 3V3 bulk
    c4 = add_fp(board, "Capacitor_SMD", "C_0402_1005Metric",
                "C4", "100nF", 30.0, 19.5)              # 3V3 bypass

    # CC pull-down resistors
    r1 = add_fp(board, "Resistor_SMD", "R_0402_1005Metric",
                "R1", "5.1k", 9.0, 8.5)
    r2 = add_fp(board, "Resistor_SMD", "R_0402_1005Metric",
                "R2", "5.1k", 9.0, 21.5)
    r2.Reference().SetPosition(vec(9.0, 22.8))  # move ref below to clear J1 SH pad

    # Power LED + current-limit resistor
    r3 = add_fp(board, "Resistor_SMD", "R_0402_1005Metric",
                "R3", "1k", 33.5, 15.0)
    d1 = add_fp(board, "LED_SMD", "LED_0805_2012Metric",
                "D1", "RED", 37.0, 15.0, rot=180)

    # Output header
    j2 = add_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
                "J2", "3V3_OUT", 42.0, 15.0)

    # Mounting holes
    for ref, x, y in [("H1",2,2),("H2",46,2),("H3",2,28),("H4",46,28)]:
        add_fp(board, "MountingHole", "MountingHole_2.2mm_M2", ref, "M2", x, y)

    # ── Net assignments ───────────────────────────────────────────────────
    # USB-C: VBUS, GND, CC1, CC2, shield→GND, D+/D-/SBU→GND (power-only)
    for pn in ("A4","A9","B4","B9"):  pad(j1,pn).SetNet(VBUS)
    for pn in ("A1","A12","B1","B12"): pad(j1,pn).SetNet(GND)
    for pn in ("SH","SH","SH","SH"):
        pass  # shield pads — SetNet by pad number not reliable for multi-SH; handle below
    for p in j1.Pads():
        if p.GetNumber() == "SH": p.SetNet(GND)
    pad(j1,"A5").SetNet(CC1)
    pad(j1,"B5").SetNet(CC2)
    for pn in ("A6","A7","A8","B6","B7","B8"): pad(j1,pn).SetNet(GND)
    # B7/A8 are in a dense pad area — use solid fill so zone doesn't starve thermal spokes
    for p in j1.Pads():
        if p.GetNumber() in ("B7", "A8"):
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # AMS1117-3.3: pin1=GND, pin2(tab)=3V3, pin3=VBUS
    pad(u1,"1").SetNet(GND)
    for p in u1.Pads():
        if p.GetNumber() == "2": p.SetNet(V33)
    pad(u1,"3").SetNet(VBUS)

    # Input caps: C1 pin1=VBUS, pin2=GND; C2 same
    pad(c1,"1").SetNet(VBUS); pad(c1,"2").SetNet(GND)
    pad(c2,"1").SetNet(VBUS); pad(c2,"2").SetNet(GND)

    # Output caps: C3/C4 pin1=3V3, pin2=GND
    pad(c3,"1").SetNet(V33); pad(c3,"2").SetNet(GND)
    pad(c4,"1").SetNet(V33); pad(c4,"2").SetNet(GND)

    # CC resistors: pad1=CC, pad2=GND
    pad(r1,"1").SetNet(CC1); pad(r1,"2").SetNet(GND)
    pad(r2,"1").SetNet(CC2); pad(r2,"2").SetNet(GND)

    # LED chain: R3 pad1=3V3, R3 pad2 → D1 anode; D1 cathode → GND
    N_LED = ensure_net(board, "N_LED")
    pad(r3,"1").SetNet(V33); pad(r3,"2").SetNet(N_LED)
    pad(d1,"2").SetNet(N_LED); pad(d1,"1").SetNet(GND)  # rot=180: pad2=anode(left), pad1=cathode(right)

    # Output header: pin1=3V3, pin2=GND
    pad(j2,"1").SetNet(V33); pad(j2,"2").SetNet(GND)

    # ── Routing ───────────────────────────────────────────────────────────
    # All positions verified against probed pad coordinates.
    #
    # VBUS: J1 A4/B9@(9.545,12.55), A9/B4@(9.545,17.45) → C1,C2 → U1pin3@(19.7,11.85)
    # 3V3:  U1pin2_small@(22,11.85), U1pin2_tab@(22,18.15) → C3,C4,R3,J2
    # GND:  copper pour on F.Cu handles all GND pads

    # ── VBUS ─────────────────────────────────────────────────────────────
    # 0.3mm stubs from dense J1 pads → vertical VBUS bus at x=11.8
    # (shifted from 11.5 to open clearance for CC vias at x=10.87)
    track(board,  9.545, 12.55, 11.8, 12.55, VBUS, w=0.3)
    track(board,  9.545, 17.45, 11.8, 17.45, VBUS, w=0.3)
    # Vertical bus linking both VBUS y-levels → also jogs to caps
    track(board, 11.8, 10.5,  11.8, 19.5,  VBUS, w=0.5)
    track(board, 11.8, 10.5,  12.05, 10.5, VBUS, w=0.3)  # → C1 pad1
    track(board, 11.8, 19.5,  12.52, 19.5, VBUS, w=0.3)  # → C2 pad1
    # VBUS horizontal bus at y=11.85 → U1 pin3 (19.7, 11.85)
    track(board, 11.8, 11.85, 19.7,  11.85, VBUS, w=0.8)

    # ── 3V3 ──────────────────────────────────────────────────────────────
    # Bus runs at y=8.5 (above all caps) to avoid clearance issues near cap GND pads
    # U1 pin2 small (22,11.85) → up to y=8.5 → horizontal right bus
    track(board, 22.0, 11.85, 22.0,  8.5,  V33, w=0.5)
    track(board, 22.0,  8.5,  42.0,  8.5,  V33, w=0.5)  # horizontal bus
    # Drops from bus to pads
    track(board, 29.05, 8.5,  29.05, 10.5, V33, w=0.3)  # → C3 pad1
    track(board, 33.0,  8.5,  33.0,  15.0, V33, w=0.5)  # → R3 area
    track(board, 32.99, 15.0, 33.0,  15.0, V33, w=0.3)  # R3 pad1 stub
    track(board, 42.0,  8.5,  42.0,  15.0, V33, w=0.5)  # → J2 pad1
    # U1 tab (22,18.15) → right → vertical to join bus via x=29.0 connector
    track(board, 22.0, 18.15, 29.0,  18.15, V33, w=0.5)
    track(board, 29.0,  8.5,  29.0,  19.5,  V33, w=0.5)  # x=29 spine (connects top bus to tab)
    track(board, 29.0,  19.5, 29.52, 19.5,  V33, w=0.3)  # → C4 pad1

    # ── N_LED: R3 pad2 (34.01,15) → D1 pad2 (36.062,15) ─────────────────
    track(board, 34.01, 15.0, 36.062, 15.0, N_LED, w=0.3)

    # ── CC1: J1 A5 (9.545,13.75) → R1 pad1 (8.49,8.5) ──────────────────
    # Stub right through B8/B7 gap (each 0.2mm clear), via at x=10.87
    # (10.87 = pad right edge 10.27 + via radius 0.4 + clearance 0.2)
    track(board,  9.545, 13.75, 10.87, 13.75, CC1, w=0.3)
    via(board, 10.87, 13.75, CC1)
    track(board, 10.87, 13.75,  7.0,  13.75, CC1, w=0.3, layer=pcbnew.B_Cu)
    track(board,  7.0,  13.75,  7.0,   8.5,  CC1, w=0.3, layer=pcbnew.B_Cu)
    via(board, 7.0, 8.5, CC1)
    track(board,  7.0,   8.5,   8.49,  8.5,  CC1, w=0.3)

    # ── CC2: J1 B5 (9.545,16.75) → R2 pad1 (8.49,21.5) ─────────────────
    # Stub right through A8/A9 gap, jog to y=16.0 before via (clears A8 corner)
    track(board,  9.545, 16.75, 10.87, 16.75, CC2, w=0.3)
    track(board, 10.87, 16.75, 10.87, 16.0,   CC2, w=0.3)
    via(board, 10.87, 16.0, CC2)
    track(board, 10.87, 16.0,   7.0,  16.0,  CC2, w=0.3, layer=pcbnew.B_Cu)
    track(board,  7.0,  16.0,   7.0,  21.5,  CC2, w=0.3, layer=pcbnew.B_Cu)
    via(board, 7.0, 21.5, CC2)
    track(board,  7.0,  21.5,   8.49, 21.5,  CC2, w=0.3)

    # ── GND bridges: isolated J1 pads the zone can't reach ───────────────
    # B8/B7/A8 are sandwiched between CC pads — route stubs left into open space
    track(board, 9.545, 13.25, 7.5, 13.25, GND, w=0.25)  # B8
    track(board, 9.545, 14.25, 7.5, 14.25, GND, w=0.25)  # B7
    track(board, 9.545, 16.25, 7.5, 16.25, GND, w=0.25)  # A8
    # SH PTH shield pins connect to outer GND SMD pads via L-routes
    track(board, 8.63, 10.68, 9.545, 10.68, GND, w=0.25)
    track(board, 9.545, 10.68, 9.545, 11.75, GND, w=0.25)  # → B12/A1
    track(board, 8.63, 19.32, 9.545, 19.32, GND, w=0.25)
    track(board, 9.545, 19.32, 9.545, 18.25, GND, w=0.25)  # → A12

    # ── GND copper pour on F.Cu ───────────────────────────────────────────
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.F_Cu)
    zone.SetNet(GND)
    pts = zone.Outline()
    pts.NewOutline()
    for xv, yv in [(1, 1), (47, 1), (47, 29), (1, 29)]:
        pts.Append(mm(xv), mm(yv))
    zone.SetMinThickness(mm(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    board.Add(zone)

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    # ── Board outline: 48 × 30 mm ────────────────────────────────────────
    outline(board, 0.0, 0.0, 48.0, 30.0)

    board.Save(str(PCB_PATH))

    fps   = len(board.GetFootprints())
    nets  = len(board.GetNetInfo().NetsByName())
    print(f"OK: {PCB_PATH}")
    print(f"  footprints: {fps}  nets: {nets}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
