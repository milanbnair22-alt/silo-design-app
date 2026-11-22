"""
Calculation engine for the RC coal silo (Janssen's theory).

Every formula in this file is copied from the original silo_design.py.
The ONLY structural change: the original reads module-level variables
(D, h, t, ...) and prints results; here the same expressions take those
values as arguments and return them in a dict so the Streamlit app can
call them with the inputs typed in the sidebar.

Nothing in this file imports Streamlit, so it can be tested on its own:
    python test_silo_calc.py
"""
import numpy as np

# Defaults = the input block of the original script
DEFAULTS = dict(
    D=5.0, h=2.0, t=0.15, hh=1.67, d2=0.5, w=8.0, phi=30.0, mu=0.5,
    gc=25.0, gf=1.5, fy=415.0, fck=20.0, bar=8.0, K=0.33,
)


def k_from_phi(phi):
    """Alternative given (commented out) in the original script."""
    return (1 - np.sin(np.radians(phi))) / (1 + np.sin(np.radians(phi)))


# ------------------------------------------------------------
# FUNCTIONS (same bodies as the original)
# ------------------------------------------------------------
def ph(z, D, w, mu, K):
    """Horizontal pressure at depth z (kN/m2)"""
    R = D / 4
    return w * R / mu * (1 - np.exp(-mu * K * z / R))


def pv(z, D, w, mu, K):
    """Vertical pressure at depth z (kN/m2)"""
    return ph(z, D, w, mu, K) / K


def steel(Ast_req, dia, t_mm):
    """Spacing of bars for the required steel area (mm2 per m width).
    Minimum steel is 0.12 % and maximum spacing is 300 mm."""
    Amin = 0.0012 * 1000 * t_mm
    A = max(Ast_req, Amin)
    a = np.pi * dia ** 2 / 4
    spacing = min(np.floor(1000 * a / A / 10) * 10, 300)
    provided = 1000 * a / spacing
    return Amin, spacing, provided


# ------------------------------------------------------------
# FULL DESIGN (Steps 1-3 of the original script)
# ------------------------------------------------------------
def design(D, h, t, hh, d2, w, phi, mu, gc, gf, fy, fck, bar, K):
    """Run Steps 1-3 of the original script and return every result."""
    t_mm = t * 1000
    Ht = h + hh   # total height
    P = dict(D=D, w=w, mu=mu, K=K)   # shared Janssen parameters

    r = dict(inputs=dict(D=D, h=h, t=t, hh=hh, d2=d2, w=w, phi=phi, mu=mu,
                         gc=gc, gf=gf, fy=fy, fck=fck, bar=bar, K=K),
             t_mm=t_mm, Ht=Ht)

    # ---- STEP 1 : pressures at the base of the cylinder ----
    r["R"] = D / 4
    r["ph_base"] = ph(h, **P)
    r["pv_base"] = pv(h, **P)
    r["fric_base"] = mu * ph(h, **P)

    # ---- STEP 2 : cylindrical wall ----
    ph_base = r["ph_base"]
    T = ph_base * D / 2                     # hoop tension per metre height
    Tu = gf * T                             # ultimate hoop tension
    Ast_wall = Tu * 1000 / (0.87 * fy)      # steel required per metre
    Amin_w, s_wall, prov_wall = steel(Ast_wall, bar, t_mm)
    r["wall"] = dict(T=T, Tu=Tu, Ast=Ast_wall, Amin=Amin_w, spacing=s_wall,
                     provided=prov_wall, bar=bar)

    # ---- STEP 3 : hopper bottom ----
    dm = (D + d2) / 2                                   # mean diameter
    theta = np.arctan(hh / ((D - d2) / 2))              # slope of hopper
    slant = np.hypot((D - d2) / 2, hh)                  # slant length
    r["hopper"] = dict(dm=dm, theta=theta, theta_deg=float(np.degrees(theta)),
                       slant=slant)

    # Method A : class notes
    self_A = np.pi * dm * t * gc
    sur_A = w * h - 4 * ph_base * mu / D
    Wu_A = gf * (self_A + sur_A)
    T_A = Wu_A / (np.pi * dm) / np.sin(theta)
    Ast_A = T_A * 1000 / (0.87 * fy)
    Amin_A, s_A, prov_A = steel(Ast_A, bar, t_mm)
    r["A"] = dict(self_w=self_A, surcharge=sur_A, Wu=Wu_A, T=T_A, Ast=Ast_A,
                  Amin=Amin_A, spacing=s_A, provided=prov_A, dia=bar)

    # Method B : corrected
    self_B = gc * t * np.pi * dm * slant
    sur_B = pv(h, **P) * np.pi * D ** 2 / 4
    r1, r2 = D / 2, d2 / 2
    mat_B = w * np.pi * hh / 3 * (r1 ** 2 + r1 * r2 + r2 ** 2)
    Wu_B = gf * (self_B + sur_B + mat_B)
    T_B = Wu_B / (np.pi * dm) / np.sin(theta)
    Ast_B = T_B * 1000 / (0.87 * fy)

    # try bigger bars until spacing is not less than 100 mm
    for dia_B in (8, 10, 12, 16):
        Amin_B, s_B, prov_B = steel(Ast_B, dia_B, t_mm)
        if s_B >= 100:
            break
    r["B"] = dict(self_w=self_B, surcharge=sur_B, coal=mat_B, Wu=Wu_B, T=T_B,
                  Ast=Ast_B, Amin=Amin_B, spacing=s_B, provided=prov_B,
                  dia=dia_B, spacing_ok=bool(s_B >= 100))
    return r


# ------------------------------------------------------------
# PROFILES USED BY THE FIGURES (same expressions as the original)
# ------------------------------------------------------------
def pressure_profile(z, D, w, mu, K):
    """Figure 2: ph, pv and wall friction at depths z."""
    z = np.asarray(z, dtype=float)
    return ph(z, D, w, mu, K), pv(z, D, w, mu, K), mu * ph(z, D, w, mu, K)


def wall_profile(z, D, w, mu, K, gf, fy):
    """Figure 3: hoop tension, ultimate tension and Ast along the wall."""
    z = np.asarray(z, dtype=float)
    T_w = ph(z, D, w, mu, K) * D / 2
    Ast_w = gf * T_w * 1000 / (0.87 * fy)
    return T_w, gf * T_w, Ast_w


# ------------------------------------------------------------
# PARAMETRIC STUDY (Figure 5 of the original)
# ------------------------------------------------------------
def tu_vs_density(dens, D, h, mu, K, gf):
    return np.array([gf * ph(h, D, x, mu, K) * D / 2 for x in dens])


def tu_vs_friction(frictions, angle, D, h, w, gf):
    """K is recomputed from the angle, exactly as in the original."""
    Ki = k_from_phi(angle)
    return np.array([gf * ph(h, D, w, x, Ki) * D / 2 for x in frictions])


def tu_vs_diameter(dias, h, w, mu, K, gf):
    return np.array([gf * ph(h, x, w, mu, K) * x / 2 for x in dias])
