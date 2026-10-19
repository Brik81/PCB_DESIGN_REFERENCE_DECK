"""Engineering constants, unit conversions and analytical models.

Every computed number printed on a card comes from here and is covered by
tests/test_eng.py. Model sources are cited per function; see also
data/formulas/formulas.toml.
"""
import math

# CODATA 2018 exact / recommended values
C0 = 299_792_458.0            # m/s, exact
K_B = 1.380649e-23            # J/K, exact
Q_E = 1.602176634e-19         # C, exact
EPS0 = 8.8541878128e-12       # F/m
MU0 = 1.25663706212e-6        # H/m
ETA0 = math.sqrt(MU0 / EPS0)  # ~376.73 ohm
RHO_CU = 1.7241e-8            # ohm*m at 20 degC (IACS annealed copper)
ALPHA_CU = 0.00393            # 1/K near 20 degC

MIL = 0.0254                  # mm per mil, exact (1 in = 25.4 mm)
OZ_UM = {0.5: 17.5, 1: 35.0, 2: 70.0, 3: 105.0}   # nominal industry copper thickness, um


def mil_to_mm(m):
    return m * MIL


def mm_to_mil(mm):
    return mm / MIL


def c_to_k(c):
    return c + 273.15


def db20(ratio):
    return 20 * math.log10(ratio)


def db10(ratio):
    return 10 * math.log10(ratio)


# ---- copper --------------------------------------------------------------

def sheet_resistance(t_um, temp_c=20.0):
    """Copper sheet resistance in ohm/square."""
    return RHO_CU * (1 + ALPHA_CU * (temp_c - 20)) / (t_um * 1e-6)


def trace_resistance(length_mm, width_mm, t_um, temp_c=20.0):
    return sheet_resistance(t_um, temp_c) * length_mm / width_mm


def ipc2221_current(width_mil, t_mil, dT, external=True):
    """IPC-2221 curve fit I = k*dT^0.44*A^0.725 (A in mil^2). Conservative legacy model."""
    k = 0.048 if external else 0.024
    return k * dT ** 0.44 * (width_mil * t_mil) ** 0.725


def via_barrel_area_mm2(d_mm, plating_um):
    """Cross-section of a plated barrel: pi*tp*(d + tp), d = finished hole."""
    tp = plating_um / 1000
    return math.pi * tp * (d_mm + tp)


def via_resistance(d_mm, board_mm, plating_um=25.0, temp_c=20.0):
    """DC resistance of the barrel only (ohm); pads and spreading ignored."""
    rho = RHO_CU * (1 + ALPHA_CU * (temp_c - 20.0))
    return rho * (board_mm / 1000) / (via_barrel_area_mm2(d_mm, plating_um) * 1e-6)


K_CU = 390.0                  # W/(m*K), plated copper; handbooks give 385-401


def via_thermal_res(d_mm, board_mm, plating_um=25.0):
    """Conduction through the barrel only (K/W), unfilled via."""
    return (board_mm / 1000) / (K_CU * via_barrel_area_mm2(d_mm, plating_um) * 1e-6)


# ---- passives ------------------------------------------------------------

def rc_cutoff(r, c):
    return 1 / (2 * math.pi * r * c)


def lc_resonance(l, c):
    return 1 / (2 * math.pi * math.sqrt(l * c))


def thermal_noise_density(r, temp_k=300.0):
    """Johnson noise voltage density, V/sqrt(Hz)."""
    return math.sqrt(4 * K_B * temp_k * r)


E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]   # IEC 60063 (not formula-exact)


def e_series(n):
    """E48/E96/E192 per IEC 60063 rounding (3 significant figures). E192 has one exception (9.20)."""
    vals = [round(10 ** (i / n), 2) for i in range(n)]
    if n == 192:
        vals = [9.20 if abs(v - 9.19) < 1e-9 else v for v in vals]
    return vals


# ---- RF / transmission lines ----------------------------------------------

def wavelength_m(f_hz, eps_eff=1.0):
    return C0 / (f_hz * math.sqrt(eps_eff))


def dipole_len_m(f_mhz):
    """First-order practical half-wave dipole length (0.95 x lambda/2, end effect)."""
    return 143.0 / f_mhz


def monopole_len_m(f_mhz):
    """First-order practical quarter-wave monopole length."""
    return 71.5 / f_mhz


def gamma(zl, z0=50.0):
    return (zl - z0) / (zl + z0)


def return_loss_db(g):
    return -20 * math.log10(abs(g))


def vswr(g):
    g = abs(g)
    return (1 + g) / (1 - g)


def ellipk(k):
    """Complete elliptic integral of the first kind K(k) via AGM (modulus k)."""
    a, b = 1.0, math.sqrt(1 - k * k)
    while abs(a - b) > 1e-15:
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def _kk(k):
    """K(k)/K(k')"""
    return ellipk(k) / ellipk(math.sqrt(1 - k * k))


def microstrip(w, h, er, t=0.0):
    """Hammerstad & Jensen (1980) microstrip, with their strip-thickness correction.

    Returns (Z0 ohm, eps_eff). Quasi-static; ~1 % vs field solver for 0.1<w/h<10.
    """
    def z_air(u):
        f = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / u) ** 0.7528))
        return ETA0 / (2 * math.pi) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))

    def e_eff(u):
        a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
        b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
        return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)

    u = w / h
    if t > 0:
        th = t / h
        du1 = th / math.pi * math.log(1 + 4 * math.e / (th / math.tanh(math.sqrt(6.517 * u)) ** 2))
        dur = 0.5 * (1 + 1 / math.cosh(math.sqrt(er - 1))) * du1
        u1, ur = u + du1, u + dur
    else:
        u1 = ur = u
    ee = e_eff(ur) * (z_air(u1) / z_air(ur)) ** 2
    return z_air(ur) / math.sqrt(e_eff(ur)), ee


def microstrip_width(z0, h, er, t=0.0):
    """Solve microstrip() for width by bisection."""
    lo, hi = 0.01 * h, 20 * h
    for _ in range(100):
        mid = (lo + hi) / 2
        if microstrip(mid, h, er, t)[0] > z0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def diff_microstrip(w, s, h, er, t=0.0):
    """Edge-coupled differential microstrip, IPC-2141 approximation (~+/-10 %)."""
    z0, _ = microstrip(w, h, er, t)
    return 2 * z0 * (1 - 0.48 * math.exp(-0.96 * s / h))


def diff_microstrip_width(zd, s, h, er, t=0.0):
    """Solve diff_microstrip() for trace width at a fixed edge gap s."""
    lo, hi = 0.01 * h, 20 * h
    for _ in range(100):
        mid = (lo + hi) / 2
        if diff_microstrip(mid, s, h, er, t) > zd:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def stripline(w, b, er):
    """Symmetric stripline, zero-thickness exact conformal mapping (Cohn). b = ground-ground spacing."""
    k = 1 / math.cosh(math.pi * w / (2 * b))
    return ETA0 / (4 * math.sqrt(er)) * _kk(k)


def cpwg(w, s, h, er):
    """Grounded coplanar waveguide, conformal mapping (Wadell 1991, zero thickness). Returns (Z0, eps_eff)."""
    k1 = w / (w + 2 * s)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * s) / (4 * h))
    r1, r3 = _kk(k1), _kk(k3)
    ee = (1 + er * r3 / r1) / (1 + r3 / r1)
    return 60 * math.pi / math.sqrt(ee) / (r1 + r3), ee


def cpwg_gap(z0, w, h, er):
    lo, hi = 0.01, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if cpwg(w, mid, h, er)[0] < z0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def prop_delay_ps_per_mm(eps_eff):
    return math.sqrt(eps_eff) / C0 * 1e-3 * 1e12


# ---- formatting ------------------------------------------------------------

def fmt(v, digits=3):
    """Significant-figure formatting without exponent for 1e-3..1e6."""
    if v == 0:
        return "0"
    d = max(0, digits - 1 - int(math.floor(math.log10(abs(v)))))
    return f"{v:.{d}f}"


def dim(v):
    """Dimension formatting: at least one, at most two decimals (1.0, 1.25, 0.635 -> 0.635)."""
    s = f"{v:.3f}".rstrip("0")
    return s + "0" if s.endswith(".") else s
