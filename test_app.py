"""
End-to-end test of app.py with Streamlit's AppTest: change sidebar inputs, press
Calculate Design, and check that the numbers and graphs on screen match the
ORIGINAL silo_design.py run with the same inputs.

Run from the project folder:   python tests/test_app.py
"""
import json
import os
import sys

os.environ["MPLBACKEND"] = "Agg"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import numpy as np
from streamlit.testing.v1 import AppTest
from test_silo_calc import run_original   # runs the untouched original script (also runs its own checks)

fails = 0
def ok(cond, msg):
    global fails
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    fails += 0 if cond else 1

def page_text(at):
    return " ".join(m.value for m in at.markdown)

def arr(v):
    """Plotly may send arrays as base64 typed arrays ({'dtype','bdata'}); decode to numpy."""
    if isinstance(v, dict) and "bdata" in v:
        import base64
        a = np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v["dtype"]))
        return a.reshape([int(x) for x in str(v["shape"]).split(",")]) if "shape" in v else a
    return np.array(v, dtype=float)

def figs(at):
    return [json.loads(e.proto.spec) for e in at.get("plotly_chart")]

NEW = dict(D=6.0, h=9.0, t=0.2, hh=2.5, d2=0.6, w=9.0, phi=30.0, mu=0.45, K=0.35, gf=1.5, bar=10.0)

at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=90)
at.run()
ok(not at.exception, "app starts with default inputs without exceptions")
base_text, base_figs = page_text(at), figs(at)

# --- type new values into the sidebar and press Calculate Design ---
keymap = {n.key: n for n in at.sidebar.number_input}
for k, v in NEW.items():
    keymap[k].set_value(v)
at.sidebar.button[0].click()
at.run()
ok(not at.exception, "app runs without exceptions after changing inputs")
new_text, new_figs = page_text(at), figs(at)
ok(new_text != base_text, "displayed results changed after Calculate Design")
ok(len(new_figs) == len(base_figs), "same number of graphs drawn (%d)" % len(new_figs))

# --- compare with the original script at the same inputs ---
ns = run_original(NEW)
def shown(x, n):   # how the app formats a number
    return f"{float(x):,.{n}f}"
checks = {
    "horizontal pressure": shown(ns["ph_base"], 2),
    "ultimate hoop tension": shown(ns["Tu"], 2),
    "wall steel required": shown(ns["Ast_wall"], 1),
    "wall provided spacing": "%.0f mm @ %.0f mm c/c" % (NEW["bar"], ns["s_wall"]),
    "hopper A tension": shown(ns["T_A"], 2),
    "hopper B ultimate load": shown(ns["Wu_B"], 1),
    "hopper B tension": shown(ns["T_B"], 1),
    "hopper B bars": "%.0f mm @ %.0f mm c/c" % (ns["dia_B"], ns["s_B"]),
    "hopper angle": shown(np.degrees(ns["theta"]), 2),
    "slant length": shown(ns["slant"], 2),
}
for name, s in checks.items():
    ok(s in new_text, "screen shows original-script value for %s (%s)" % (name, s))

# --- graphs follow the inputs ---
def trace_vals(fig_list, title_part):
    for f in fig_list:
        t = (f["layout"].get("title") or {}).get("text", "")
        if title_part in t:
            return f
    return None
sec_old, sec_new = trace_vals(base_figs, "Section"), trace_vals(new_figs, "Section")
ok(arr(sec_new["data"][0]["y"]).min() == -(NEW["h"] + NEW["hh"]) and arr(sec_old["data"][0]["y"]).min() == -(2.0 + 1.67),
   "section drawing height follows h + hh (%.2f m)" % (NEW["h"] + NEW["hh"]))
pr = trace_vals(new_figs, "Janssen pressure")
ok(abs(arr(pr["data"][0]["x"])[-1] - ns["ph"](NEW["h"] + NEW["hh"])) < 1e-6,
   "pressure graph ends at the original script's ph for the new silo")
tu_d = trace_vals(new_figs, "coal density")
ref = [NEW["gf"] * ns["ph"](NEW["h"], w=x) * NEW["D"] / 2 for x in np.linspace(6, 12, 25)]
ok(np.allclose(arr(tu_d["data"][0]["y"]), ref), "parametric density curve matches the original expression")
tu_s = trace_vals(new_figs, "silo diameter")
ref = [NEW["gf"] * ns["ph"](NEW["h"], D=x) * x / 2 for x in np.linspace(3, 8, 26)]
ok(np.allclose(arr(tu_s["data"][0]["y"]), ref), "parametric diameter curve matches the original expression")
f3d = [f for f in new_figs if any(d["type"] in ("surface", "scatter3d") for d in f["data"])][0]
zs = np.concatenate([np.ravel(arr(d["z"])) for d in f3d["data"] if d["type"] == "surface"])
ok(abs(zs.min() + NEW["h"] + NEW["hh"]) < 1e-9, "3D model extends to the new total height")
xs = np.concatenate([np.ravel(arr(d["x"])) for d in f3d["data"] if d["type"] == "surface"])
ok(abs(xs.max() - NEW["D"] / 2) < 1e-6, "3D model radius follows the new diameter")

# --- parametric controls change the graph ---
pk = {n.key: n for n in at.main.number_input}
pk["d_hi"].set_value(15.0)
at.run()
tu_d2 = trace_vals(figs(at), "coal density")
ok(abs(arr(tu_d2["data"][0]["x"]).max() - 15.0) < 1e-9, "changing the density range updates the parametric graph")

# --- invalid input handled ---
keymap = {n.key: n for n in at.sidebar.number_input}
keymap["d2"].set_value(6.0); keymap["D"].set_value(5.0)
at.sidebar.button[0].click(); at.run()
ok(len(at.error) == 1 and not at.exception, "d2 >= D shows an error message instead of crashing")

print("\nRESULT:", "ALL APP TESTS PASSED" if fails == 0 else "%d FAILED" % fails)
sys.exit(1 if fails else 0)
