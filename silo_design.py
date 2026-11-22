# Design of RC coal silo using Janssen's theory
# Run:  python silo_design.py   (needs numpy and matplotlib)
# Change the input values below and run again.

import os
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# INPUT DATA
# ------------------------------------------------------------
D = 5.0          # diameter of silo (m)
h = 2.0          # height of cylindrical part (m)
t = 0.15         # wall thickness (m)
hh = 1.67        # height of hopper (m)
d2 = 0.5         # outlet diameter (m)
w = 8.0          # density of coal (kN/m3)
phi = 30.0       # angle of repose (degrees)
mu = 0.5         # wall friction coefficient mu'
gc = 25.0        # unit weight of concrete (kN/m3)
gf = 1.5         # load factor
fy = 415.0       # yield strength of steel (MPa)
fck = 20.0       # concrete strength (MPa)
bar = 8.0        # bar diameter for wall (mm)
K = 0.33         # lateral pressure ratio, (1-sin phi)/(1+sin phi)

# K from phi can be used instead of 0.33:
# K = (1 - np.sin(np.radians(phi))) / (1 + np.sin(np.radians(phi)))

folder = "silo_output"
os.makedirs(folder, exist_ok=True)


# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------
def ph(z, D=D, w=w, mu=mu, K=K):
    """Horizontal pressure at depth z (kN/m2)"""
    R = D / 4
    return w * R / mu * (1 - np.exp(-mu * K * z / R))


def pv(z):
    """Vertical pressure at depth z (kN/m2)"""
    return ph(z) / K


def steel(Ast_req, dia, t_mm):
    """Spacing of bars for the required steel area (mm2 per m width).
    Minimum steel is 0.12 % and maximum spacing is 300 mm."""
    Amin = 0.0012 * 1000 * t_mm
    A = max(Ast_req, Amin)
    a = np.pi * dia ** 2 / 4
    spacing = min(np.floor(1000 * a / A / 10) * 10, 300)
    provided = 1000 * a / spacing
    return Amin, spacing, provided


t_mm = t * 1000
Ht = h + hh   # total height

# ------------------------------------------------------------
# STEP 1 : PRESSURES
# ------------------------------------------------------------
print("=" * 70)
print("STEP 1 : JANSSEN PRESSURES")
print("=" * 70)
print("R = D/4 = %.2f m" % (D / 4))
print("depth(m)   ph      pv      mu*ph")
for z in np.linspace(0, h, 5):
    print("%6.2f   %6.2f  %6.2f  %6.2f" % (z, ph(z), pv(z), mu * ph(z)))

# ------------------------------------------------------------
# STEP 2 : CYLINDRICAL WALL
# ------------------------------------------------------------
print()
print("=" * 70)
print("STEP 2 : CYLINDRICAL WALL")
print("=" * 70)
ph_base = ph(h)
T = ph_base * D / 2                     # hoop tension per metre height
Tu = gf * T                             # ultimate hoop tension
Ast_wall = Tu * 1000 / (0.87 * fy)      # steel required per metre
Amin_w, s_wall, prov_wall = steel(Ast_wall, bar, t_mm)

print("ph at base            = %.2f kN/m2" % ph_base)
print("Hoop tension T        = %.2f kN/m" % T)
print("Ultimate tension Tu   = %.2f kN/m" % Tu)
print("Ast required          = %.2f mm2/m" % Ast_wall)
print("Minimum Ast (0.12%%)   = %.0f mm2/m" % Amin_w)
print("Provide %.0f mm bars @ %.0f mm c/c (Ast = %.0f mm2/m)" % (bar, s_wall, prov_wall))
print("Vertical bars: 8 mm @ 300 mm c/c")

# ------------------------------------------------------------
# STEP 3 : HOPPER BOTTOM
# ------------------------------------------------------------
print()
print("=" * 70)
print("STEP 3 : HOPPER BOTTOM")
print("=" * 70)
dm = (D + d2) / 2                                   # mean diameter
theta = np.arctan(hh / ((D - d2) / 2))              # slope of hopper
slant = np.hypot((D - d2) / 2, hh)                  # slant length
print("Hopper angle = %.2f deg, slant length = %.2f m" % (np.degrees(theta), slant))

# ---- Method A : class notes ----
self_A = np.pi * dm * t * gc
sur_A = w * h - 4 * ph_base * mu / D
Wu_A = gf * (self_A + sur_A)
T_A = Wu_A / (np.pi * dm) / np.sin(theta)
Ast_A = T_A * 1000 / (0.87 * fy)
Amin_A, s_A, prov_A = steel(Ast_A, bar, t_mm)

print("\nMETHOD A (class notes)")
print("  Self weight of hopper = %.3f kN" % self_A)
print("  Surcharge             = %.2f kN/m2" % sur_A)
print("  Ultimate load         = %.2f" % Wu_A)
print("  Tension T             = %.2f kN/m" % T_A)
print("  Ast required          = %.2f mm2/m" % Ast_A)
print("  Provide %.0f mm @ %.0f mm c/c (%.0f mm2/m)" % (bar, s_A, prov_A))

# ---- Method B : corrected ----
self_B = gc * t * np.pi * dm * slant
sur_B = pv(h) * np.pi * D ** 2 / 4
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

print("\nMETHOD B (corrected)")
print("  Self weight of hopper = %.1f kN" % self_B)
print("  Surcharge pv x area   = %.1f kN" % sur_B)
print("  Coal inside hopper    = %.1f kN" % mat_B)
print("  Ultimate load         = %.1f kN" % Wu_B)
print("  Tension T             = %.1f kN/m" % T_B)
print("  Ast required          = %.0f mm2/m" % Ast_B)
print("  Provide %.0f mm @ %.0f mm c/c (%.0f mm2/m)" % (dia_B, s_B, prov_B))


# ------------------------------------------------------------
# FIGURE 1 : 2D SECTION
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 9))
a, b = D / 2, d2 / 2

# coal
ax.fill([-a, a, a, b, -b, -a], [0, 0, -h, -Ht, -Ht, -h], color="#444444", alpha=0.7)
# concrete wall
ax.plot([-a, -a, -b], [0, -h, -Ht], "k", linewidth=4)
ax.plot([a, a, b], [0, -h, -Ht], "k", linewidth=4)
ax.plot([-b, b], [-Ht, -Ht], "k", linewidth=4)

# hoop bars as red dots
y = s_wall / 2000
while y < h:
    ax.plot([-a, a], [-y, -y], "r.", markersize=4)
    y += s_wall / 1000

# pressure diagram
zz = np.linspace(0, h, 40)
ax.plot(a + 0.2 + ph(zz) / ph_base * 1.2, -zz, "r", linewidth=2, label="ph on wall")
ax.plot([a + 0.2, a + 0.2], [0, -h], "r", linewidth=1)

ax.text(0, 0.35, "D = %.1f m" % D, ha="center")
ax.text(-a - 0.2, -h / 2, "h = %.1f m" % h, ha="right", rotation=90, va="center")
ax.text(-a - 0.2, -h - hh / 2, "%.2f m" % hh, ha="right", rotation=90, va="center")
ax.text(0, -h / 2, "COAL\nw = %.0f kN/m3" % w, ha="center", color="white", fontsize=12)
ax.text(0, -Ht - 0.3, "d2 = %.1f m" % d2, ha="center")
ax.text(-a, -Ht - 0.9, "Wall: %.0f mm @ %.0f c/c (hoop), 8 mm @ 300 c/c (vertical)\n"
        "Hopper A: %.0f mm @ %.0f c/c    Hopper B: %.0f mm @ %.0f c/c"
        % (bar, s_wall, bar, s_A, dia_B, s_B), fontsize=8)
ax.set_aspect("equal")
ax.set_title("Coal silo - section and reinforcement")
ax.legend(loc="upper right")
ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig1_section.png"), dpi=150)

# ------------------------------------------------------------
# FIGURE 2 : PRESSURES
# ------------------------------------------------------------
z_all = np.linspace(0, Ht, 100)
fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(ph(z_all), z_all, "r", label="ph (horizontal)")
ax.plot(pv(z_all), z_all, "b", label="pv (vertical)")
ax.plot(mu * ph(z_all), z_all, "g", label="wall friction mu*ph")
ax.axhline(h, color="gray", linestyle="--")
ax.text(0.5, h - 0.1, "cylinder / hopper", color="gray")
ax.set_xlabel("Pressure (kN/m2)")
ax.set_ylabel("Depth (m)")
ax.invert_yaxis()
ax.set_title("Janssen pressures")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig2_pressures.png"), dpi=150)

# ------------------------------------------------------------
# FIGURE 3 : WALL HOOP TENSION AND STEEL
# ------------------------------------------------------------
z_w = np.linspace(0, h, 100)
T_w = ph(z_w) * D / 2
Ast_w = gf * T_w * 1000 / (0.87 * fy)

fig, axs = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
axs[0].plot(T_w, z_w, "b", label="T")
axs[0].plot(gf * T_w, z_w, "r", label="Tu = 1.5 T")
axs[0].set_xlabel("Hoop tension (kN/m)")
axs[0].set_ylabel("Depth (m)")
axs[0].set_title("Hoop tension in wall")
axs[0].legend()
axs[1].plot(Ast_w, z_w, "b", label="Ast required")
axs[1].axvline(Amin_w, color="k", linestyle="--", label="Minimum 0.12%")
axs[1].axvline(prov_wall, color="g", label="Provided %.0f mm @ %.0f" % (bar, s_wall))
axs[1].set_xlabel("Steel (mm2/m)")
axs[1].set_title("Hoop steel")
axs[1].legend(fontsize=8)
axs[0].invert_yaxis()
for axis in axs:
    axis.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig3_wall.png"), dpi=150)

# ------------------------------------------------------------
# FIGURE 4 : HOPPER METHOD A AND B
# ------------------------------------------------------------
names = ["Method A", "Method B"]
fig, axs = plt.subplots(1, 3, figsize=(13, 4.5))
data = [([Wu_A, Wu_B], "Ultimate load (kN)"),
        ([T_A, T_B], "Tension in slab (kN/m)"),
        ([Ast_A, Ast_B], "Ast required (mm2/m)")]
for axis, (values, title) in zip(axs, data):
    axis.bar(names, values, color=["gray", "tomato"])
    axis.set_title(title)
    for i in range(2):
        axis.text(i, values[i], "%.1f" % values[i], ha="center", va="bottom")
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig4_hopper.png"), dpi=150)

# ------------------------------------------------------------
# FIGURE 5 : PARAMETRIC STUDY (ultimate hoop tension)
# ------------------------------------------------------------
fig, axs = plt.subplots(1, 3, figsize=(14, 4.5))

dens = np.linspace(6, 12, 25)
axs[0].plot(dens, [gf * ph(h, w=x) * D / 2 for x in dens], "r")
axs[0].axvline(w, color="k", linestyle="--")
axs[0].set_xlabel("Density of coal (kN/m3)")

for angle in (25, 30, 35):
    Ki = (1 - np.sin(np.radians(angle))) / (1 + np.sin(np.radians(angle)))
    frictions = np.linspace(0.3, 0.8, 25)
    axs[1].plot(frictions, [gf * ph(h, mu=x, K=Ki) * D / 2 for x in frictions], label="phi = %d" % angle)
axs[1].set_xlabel("Wall friction mu'")
axs[1].legend()

dias = np.linspace(3, 8, 26)
axs[2].plot(dias, [gf * ph(h, D=x) * x / 2 for x in dias], "g")
axs[2].axvline(D, color="k", linestyle="--")
axs[2].set_xlabel("Diameter (m)")

for axis in axs:
    axis.set_ylabel("Tu (kN/m)")
    axis.grid(alpha=0.3)
axs[0].set_title("Tu against density")
axs[1].set_title("Tu against mu'")
axs[2].set_title("Tu against diameter")
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig5_parametric.png"), dpi=150)

# ------------------------------------------------------------
# FIGURE 6 : 3D MODEL
# ------------------------------------------------------------
fig = plt.figure(figsize=(8, 9))
ax = fig.add_subplot(111, projection="3d")

theta_c = np.linspace(0, 2 * np.pi, 60)

# concrete cylinder
zc = np.linspace(0, -h, 2)
TH, ZC = np.meshgrid(theta_c, zc)
ax.plot_surface(a * np.cos(TH), a * np.sin(TH), ZC, color="lightgray", alpha=0.3)

# concrete hopper (cone)
zh = np.linspace(-h, -Ht, 10)
rad = a + (zh + h) / (-hh) * (b - a)
TH2, ZH = np.meshgrid(theta_c, zh)
RAD = np.tile(rad, (len(theta_c), 1)).T
ax.plot_surface(RAD * np.cos(TH2), RAD * np.sin(TH2), ZH, color="lightgray", alpha=0.3)

# coal surface on top
rr = np.linspace(0, a - t, 2)
TH3, RR = np.meshgrid(theta_c, rr)
ax.plot_surface(RR * np.cos(TH3), RR * np.sin(TH3), np.zeros_like(RR), color="black", alpha=0.8)

# hoop bars in cylinder
rm = a - t / 2
y = s_wall / 2000
while y < h:
    ax.plot(rm * np.cos(theta_c), rm * np.sin(theta_c), -y, color="orangered", linewidth=0.8)
    y += s_wall / 1000

# hoop bars in hopper
n_rings = int(min(np.ceil(slant / (s_A / 1000)), 40))
for i in range(1, n_rings + 1):
    u = i / (n_rings + 1)
    r_i = rm - u * (D - d2) / 2
    ax.plot(r_i * np.cos(theta_c), r_i * np.sin(theta_c), -h - u * hh, color="goldenrod", linewidth=0.8)

# vertical bars at 300 mm
count = int(min(np.floor(np.pi * D / 0.3), 60))
for i in range(count):
    ang = 2 * np.pi * i / count
    ax.plot([rm * np.cos(ang)] * 2, [rm * np.sin(ang)] * 2, [0, -h], color="steelblue", linewidth=0.6)

ax.set_box_aspect((D, D, Ht))
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.set_zlabel("height (m)")
ax.set_title("3D model of silo with reinforcement")
ax.view_init(elev=20, azim=-60)
fig.tight_layout()
fig.savefig(os.path.join(folder, "fig6_3d.png"), dpi=150)

print("\nFigures saved in folder:", folder)
plt.show()    # the 3D figure can be rotated with the mouse
