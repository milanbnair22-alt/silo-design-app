"""
Checks that silo_calc.py gives the same numbers as the ORIGINAL silo_design.py.

For each test case the original script is executed unchanged (only its input
lines are edited), and its variables are compared with silo_calc.design().

Run from the project folder:   python tests/test_silo_calc.py
"""
import os
import re
import sys
import tempfile

os.environ["MPLBACKEND"] = "Agg"
import io
import contextlib
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import silo_calc as sc

ORIGINAL = os.path.join(ROOT, "silo_design.py")

CASES = {
    "defaults": {},
    "bigger silo": dict(D=6.0, h=9.0, t=0.2, hh=2.5, d2=0.6, w=9.0, mu=0.45, bar=10.0, K=0.35),
    "heavy load": dict(D=8.0, h=14.0, t=0.3, hh=3.0, d2=0.8, w=10.0, phi=35.0, mu=0.4, gf=1.5, fy=500.0, bar=12.0, K=0.27),
    "small silo": dict(D=3.0, h=4.0, t=0.12, hh=1.2, d2=0.4, w=7.0, mu=0.6, gc=24.0, bar=8.0, K=0.4),
}


def run_original(overrides):
    """Execute the untouched original script with edited input lines."""
    src = open(ORIGINAL).read()
    for key, val in overrides.items():
        src, n = re.subn(r"^(%s\s*=\s*)[-\d.]+" % key, r"\g<1>%r" % val, src, count=1, flags=re.M)
        assert n == 1, "could not edit input %s" % key
    ns = {"__name__": "original"}
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(src, ORIGINAL, "exec"), ns)
        finally:
            os.chdir(cwd)
    import matplotlib.pyplot as plt
    plt.close("all")
    return ns


fails = 0


def check(label, mine, ref):
    global fails
    ok = np.allclose(mine, ref, rtol=1e-9, atol=1e-9)
    if not ok:
        fails += 1
        print("  FAIL %-28s mine=%s original=%s" % (label, mine, ref))
    return ok


def main():
    global fails
    for name, over in CASES.items():
        inp = dict(sc.DEFAULTS)
        inp.update(over)
        ns = run_original(over)
        r = sc.design(**inp)
        n_before = fails

        # Step 1 / 2 : pressures and wall
        check("ph_base", r["ph_base"], ns["ph_base"])
        check("wall T", r["wall"]["T"], ns["T"])
        check("wall Tu", r["wall"]["Tu"], ns["Tu"])
        check("wall Ast", r["wall"]["Ast"], ns["Ast_wall"])
        check("wall Amin", r["wall"]["Amin"], ns["Amin_w"])
        check("wall spacing", r["wall"]["spacing"], ns["s_wall"])
        check("wall provided", r["wall"]["provided"], ns["prov_wall"])
        # Step 3 : hopper geometry
        check("theta", r["hopper"]["theta"], ns["theta"])
        check("slant", r["hopper"]["slant"], ns["slant"])
        # Method A
        for k_mine, k_orig in [("self_w", "self_A"), ("surcharge", "sur_A"), ("Wu", "Wu_A"),
                               ("T", "T_A"), ("Ast", "Ast_A"), ("spacing", "s_A"), ("provided", "prov_A")]:
            check("A " + k_mine, r["A"][k_mine], ns[k_orig])
        # Method B
        for k_mine, k_orig in [("self_w", "self_B"), ("surcharge", "sur_B"), ("coal", "mat_B"), ("Wu", "Wu_B"),
                               ("T", "T_B"), ("Ast", "Ast_B"), ("spacing", "s_B"), ("provided", "prov_B"),
                               ("dia", "dia_B")]:
            check("B " + k_mine, r["B"][k_mine], ns[k_orig])

        # Janssen functions at several depths (original ph/pv use the edited inputs as defaults)
        z = np.linspace(0, inp["h"] + inp["hh"], 11)
        check("ph(z)", sc.ph(z, inp["D"], inp["w"], inp["mu"], inp["K"]), ns["ph"](z))
        check("pv(z)", sc.pv(z, inp["D"], inp["w"], inp["mu"], inp["K"]), ns["pv"](z))

        # Parametric study: same expressions as Figure 5 of the original
        dens = np.linspace(6, 12, 25)
        check("tu vs density",
              sc.tu_vs_density(dens, inp["D"], inp["h"], inp["mu"], inp["K"], inp["gf"]),
              [inp["gf"] * ns["ph"](inp["h"], w=x) * inp["D"] / 2 for x in dens])
        fr = np.linspace(0.3, 0.8, 25)
        for ang in (25, 30, 35):
            Ki = (1 - np.sin(np.radians(ang))) / (1 + np.sin(np.radians(ang)))
            check("tu vs mu (phi=%d)" % ang,
                  sc.tu_vs_friction(fr, ang, inp["D"], inp["h"], inp["w"], inp["gf"]),
                  [inp["gf"] * ns["ph"](inp["h"], mu=x, K=Ki) * inp["D"] / 2 for x in fr])
        dias = np.linspace(3, 8, 26)
        check("tu vs diameter",
              sc.tu_vs_diameter(dias, inp["h"], inp["w"], inp["mu"], inp["K"], inp["gf"]),
              [inp["gf"] * ns["ph"](inp["h"], D=x) * x / 2 for x in dias])

        print("%-12s %s" % (name, "OK - matches original" if fails == n_before else "MISMATCH"))
    print("\nRESULT:", "ALL CHECKS PASSED" if fails == 0 else "%d CHECK(S) FAILED" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
