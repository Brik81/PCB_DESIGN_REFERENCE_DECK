"""Card 15 - FORMULA MASTER: SI prefixes, constants, conversions, E24/E96, core formulas (registry)."""
from ..config import eq
from ..eng import C0, E24, EPS0, ETA0, K_B, MU0, Q_E, RHO_CU, e_series
from ..template import footer, new_card

PREFIXES = [("p", "10^{−12}"), ("n", "10^{−9}"), ("µ", "10^{−6}"), ("m", "10^{−3}"),
            ("k", "10^{3}"), ("M", "10^{6}"), ("G", "10^{9}"), ("T", "10^{12}")]
CORE = [("Ohm", "ohm"), ("power", "power"), ("divider", "divider"), ("RC τ", "rc_tau"), ("RC f_{c}", "rc_fc"),
        ("LC f_{0}", "lc_f0"), ("X_{C}", "xc"), ("X_{L}", "xl"), ("E cap.", "cap_energy"), ("E ind.", "ind_energy"),
        ("dB volts", "db_v"), ("dB power", "db_p"), ("wavelength", "lambda"), ("delay", "tpd"),
        ("reflection", "gamma"), ("VSWR", "vswr"), ("Z_{0}", "z0_lc"), ("knee", "knee"), ("crystal", "xtal_cl"),
        ("Nyquist", "nyquist"), ("shunt", "shunt"), ("curr. div.", "current_divider"), ("inv. amp", "inv_amp"),
        ("non-inv.", "noninv_amp"), ("R noise", "noise_r"), ("ADC LSB", "adc_lsb"), ("ADC SNR", "adc_snr"),
        ("LDO loss", "ldo_pd"), ("buck D", "buck_d"), ("boost D", "boost_d"), ("efficiency", "efficiency"),
        ("T_{j}", "tj"), ("trace R", "cu_r"), ("ret. loss", "return_loss"), ("L-match", "lmatch_q")]


def build(card):
    b, f, k = new_card(card, "prefixes, constants, E-series", "core formulas, one page")
    footer(k)
    prefixes(f)
    constants(f)
    conversions(f)
    eseries(f)
    core(k)
    b.meta["formula_keys"] = [key for _, key in CORE]
    return b


def prefixes(f):
    p = f.panel("prefixes", 1.6, 11.8, 20.0, 17.6, "SI PREFIX")
    p.table([[a, b, c, d] for (a, b), (c, d) in zip(PREFIXES[:4], PREFIXES[4:])], [0, 2.4, 10.4, 12.8],
            header=False, pitch=1.75)


def constants(f):
    p = f.panel("constants", 23.0, 11.8, 32.6, 17.6, "CONSTANTS")
    p.table([["c", f"{C0:.0f} m/s"], ["k", f"{K_B:.4e} J/K"], ["q", f"{Q_E:.4e} C"],
             ["ε_{0}", f"{EPS0:.4e} F/m"], ["µ_{0}", f"{MU0:.4e} H/m"], ["η_{0}", f"{ETA0:.2f} Ω"],
             ["ρ_{Cu}", f"{RHO_CU:.3e} Ωm 20 °C"]], [0, 4.6], header=False, pitch=1.75)


def conversions(f):
    p = f.panel("conversions", 57.0, 11.8, 27.0, 17.6, "CONVERSIONS")
    p.lines(["1 mil = 0.0254 mm", "1 mm = 39.37 mil", "1 oz Cu ≈ 35 µm", "°F = 1.8·°C + 32",
             "0 dBm = 1 mW", "P_{dBm} = 10·log(P/1 mW)", "dBV ref 1 V_{rms}"], pitch=1.75)


def eseries(f):
    p = f.panel("eseries", 1.6, 31.0, 82.4, 21.38, "E24 (E12 = every 2nd) / E96")
    cols = 12
    cw = p.w / cols
    y = p.cy + 0.8
    for r in range(2):
        for c in range(cols):
            v = E24[r * cols + c]
            p.text(f"{v:.1f}", p.x + cw * c + cw - 1.2, y, just="right")
        y += 1.6
    f.line(p.x, y - 0.6, p.x2, y - 0.6)
    e96 = e_series(96)
    y += 0.5
    for r in range(8):
        for c in range(cols):
            p.text(f"{e96[r * cols + c]:.2f}", p.x + cw * c + cw - 1.2, y, just="right")
        y += 1.6


def core(k):
    p = k.panel("core", 1.6, 11.8, 82.4, 37.6, "CORE FORMULAS (registry; assumptions in docs)")
    half = (len(CORE) + 1) // 2
    y0 = p.cy + 0.8
    p.table([[a, eq(b)] for a, b in CORE[:half]], [0, 11.0], y=y0, header=False, pitch=1.75)
    p.table([[a, eq(b)] for a, b in CORE[half:]], [42.0, 53.0], y=y0, header=False, pitch=1.75)
