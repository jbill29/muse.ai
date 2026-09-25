"""THF GPC Explorer: an interactive visual guide to the THF gel permeation chromatography instrument."""
import time

import numpy as np
import streamlit as st
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

st.set_page_config(page_title="THF GPC Explorer", layout="wide")

st.title("THF GPC Explorer")
st.write(
    "An interactive visual guide to the gel permeation chromatography (GPC) instrument — "
    "what it measures, how each part works, and how to read its results. "
    "Built as a study companion for disassembly day."
)

tab_flow, tab_sep, tab_chrom, tab_det, tab_cal, tab_check = st.tabs(
    [
        "Flow path",
        "Separation",
        "Chromatogram lab",
        "Detectors",
        "Calibration",
        "Disassembly checklist",
    ]
)

# ----------------------------------------------------------------------------
# Tab 1: Flow path explorer
# ----------------------------------------------------------------------------
COMPONENTS = [
    dict(
        key="reservoir",
        label="THF\nreservoir",
        name="THF solvent reservoir",
        tag="Filtered THF — the mobile phase",
        what=(
            "A bottle of tetrahydrofuran (THF) sits on top of the stack and gravity-feeds "
            "the system. The THF is filtered (0.2–0.45 µm) so no particles ever reach the columns."
        ),
        why=(
            "THF dissolves a huge range of polymers, has low viscosity (so backpressure stays "
            "manageable), and evaporates easily. It is the river everything floats down."
        ),
        fails=(
            "Particles in the solvent clog column frits and raise backpressure permanently. "
            "Contaminated THF (peroxides, water) ruins separations."
        ),
    ),
    dict(
        key="degasser",
        label="Degasser",
        name="Degasser",
        tag="Pulls dissolved air out of the THF",
        what=(
            "A vacuum-membrane module that continuously strips dissolved air out of the THF "
            "before it reaches the pump."
        ),
        why=(
            "Bubbles make the pump stutter (cavitation) and create noise spikes in the detectors — "
            "the light-scattering detector is especially sensitive to them."
        ),
        fails="Bubbly baseline, pump pressure ripple, and ghost peaks that look like sample.",
    ),
    dict(
        key="pump",
        label="Isocratic\npump",
        name="Isocratic pump",
        tag="Exactly 1.0 mL/min, constant composition",
        what=(
            "Pushes THF through the system at exactly 1.0 mL/min. 'Isocratic' means one constant "
            "solvent the whole run — no gradients."
        ),
        why=(
            "The entire method converts *time* into *molecular weight*. If the flow rate drifts, "
            "every molecular weight you compute is wrong."
        ),
        fails="Drifting flow shifts retention times and corrupts all MW results; pump pulsation makes wavy baselines.",
    ),
    dict(
        key="autosampler",
        label="Auto-\nsampler",
        name="Autosampler",
        tag="Precise, reproducible injections",
        what=(
            "Injects a tiny, precise volume (tens of microliters) of your polymer solution "
            "(~1 mg/mL, pre-filtered through 0.45 µm) into the flowing THF."
        ),
        why=(
            "Every run must start identically — injection volume and timing reproducibility is what "
            "makes runs comparable to each other."
        ),
        fails="A bent or clogged needle gives irreproducible injections; carryover contaminates the next run.",
    ),
    dict(
        key="guard",
        label="Guard\ncolumn",
        name="Guard column",
        tag="Cheap sacrificial protector",
        what=(
            "A short, inexpensive column placed in front of the analytical columns. It catches "
            "particles and strongly retained junk."
        ),
        why="It dies so the expensive analytical columns may live — one dirty sample can otherwise kill a column set worth thousands.",
        fails="Without it, particulates and sticky contaminants foul the analytical columns permanently.",
    ),
    dict(
        key="columns",
        label="Columns ×2\n(PL Mixed-C)",
        name="Analytical columns (2× PL gel 5 µm Mixed-C)",
        tag="Where the separation happens",
        what=(
            "Two columns in series packed with 5 µm porous beads. 'Mixed-C' means a blend of pore "
            "sizes, giving a broad separation range (roughly 10²–10⁶ g/mol). This is where big "
            "chains race ahead and small chains lag behind."
        ),
        why="Two columns in series means more theoretical plates — sharper separation and better resolution between sizes.",
        fails="Dried out, dropped, or fouled columns lose resolution permanently. The most expensive single mistake.",
    ),
    dict(
        key="mals",
        label="MALS\n(TREOS)",
        name="miniDAWN TREOS (light scattering)",
        tag="Absolute molecular weight, no standards needed",
        what=(
            "Shines a laser through the flowing liquid and measures scattered light at multiple "
            "angles. Bigger molecules scatter more light."
        ),
        why=(
            "Gives the *absolute* molecular weight at each point of the peak — no calibration "
            "standards required. Needs the concentration (from the RI detector) and the polymer's dn/dc."
        ),
        fails="Bubbles or dust in the flow cell scatter hugely — they look like giant molecules and cause fake MW spikes.",
    ),
    dict(
        key="visc",
        label="Viscometer\n(Viscostar II)",
        name="Viscostar II (viscometer)",
        tag="Viscosity → chain shape",
        what=(
            "Measures the solution's viscosity with a capillary bridge as the liquid flows past, "
            "giving intrinsic viscosity at each point of the peak."
        ),
        why=(
            "Viscosity reveals chain shape and density — compact branched chains versus extended "
            "linear ones — and it enables universal calibration."
        ),
        fails="A clogged capillary drifts the baseline; temperature wobbles change every viscosity reading.",
    ),
    dict(
        key="ri",
        label="RI\n(Optilab rEX)",
        name="Optilab rEX (differential refractometer)",
        tag="Concentration detector",
        what=(
            "Compares the refractive index of the eluting liquid against pure THF. Its signal is "
            "proportional to concentration × dn/dc."
        ),
        why=(
            "It tells you *how much* polymer is eluting at each moment — the concentration profile "
            "the other detectors need. Nearly universal: works for any polymer whose refractive "
            "index differs from THF's."
        ),
        fails="It sits last because it is sensitive to pressure pulses and temperature — drafts or pump ripple show up as baseline waves.",
    ),
]


def flow_diagram(selected_key):
    """Horizontal block schematic of the flow path; the selected component is highlighted."""
    n = len(COMPONENTS)
    fig, ax = plt.subplots(figsize=(13, 2.6))
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, c in enumerate(COMPONENTS):
        selected = c["key"] == selected_key
        box = FancyBboxPatch(
            (i + 0.06, 0.25),
            0.88,
            0.5,
            boxstyle="round,pad=0.02",
            facecolor="#fbbf24" if selected else "#dbeafe",
            edgecolor="#b45309" if selected else "#3b82f6",
            linewidth=2.2 if selected else 1.2,
        )
        ax.add_patch(box)
        ax.text(
            i + 0.5,
            0.5,
            c["label"],
            ha="center",
            va="center",
            fontsize=8.5,
            weight="bold" if selected else "normal",
        )
        if i < n - 1:
            ax.annotate(
                "",
                xy=(i + 1.0, 0.5),
                xytext=(i + 0.98, 0.5),
                arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.6),
            )
    ax.text(0.02, 0.08, "THF in", fontsize=8, color="#64748b")
    ax.text(n - 0.02, 0.08, "→ waste", fontsize=8, color="#64748b", ha="right")
    fig.tight_layout()
    return fig


@st.fragment
def frag_tab_flow():
        st.header("Follow the flow path")
        st.write(
            "THF travels through the instrument in one fixed order. "
            "Pick a component to highlight it and see what it does."
        )
        sel_name = st.selectbox("Component", [c["name"] for c in COMPONENTS])
        comp = next(c for c in COMPONENTS if c["name"] == sel_name)
        col_a, col_b = st.columns([2.1, 1])
        with col_a:
            st.pyplot(flow_diagram(comp["key"]))
        with col_b:
            st.subheader(comp["name"])
            st.caption(comp["tag"])
            st.write("**What it does:** " + comp["what"])
            st.write("**Why it matters:** " + comp["why"])
            st.write("**If it goes wrong:** " + comp["fails"])


with tab_flow:
    frag_tab_flow()

# ----------------------------------------------------------------------------
# Tab 2: Separation — big = fast, small = slow
# ----------------------------------------------------------------------------
BAND_V = [0.95, 0.62, 0.38]
BAND_COLORS = ["#ef4444", "#f59e0b", "#3b82f6"]
BAND_NAMES = ["large chains", "medium chains", "small chains"]
T_MAX = 3.4


def pore_figure():
    """Two-panel schematic: excluded large chain vs permeating small chain."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for ax, big in zip(axes, [True, False]):
        ax.set_xlim(-1.7, 1.7)
        ax.set_ylim(-1.45, 1.45)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.add_patch(Circle((0, 0), 1.0, facecolor="#e2e8f0", edgecolor="#475569", lw=2))
        for px, py in [(-0.45, 0.35), (0.42, 0.42), (0.02, -0.48)]:
            ax.add_patch(
                Circle((px, py), 0.28, facecolor="white", edgecolor="#475569", lw=1.6)
            )
        ax.text(0, 1.18, "porous bead", ha="center", fontsize=9, color="#475569")
        if big:
            ax.add_patch(
                Circle(
                    (-1.05, 0.55),
                    0.44,
                    facecolor="#ef4444",
                    edgecolor="#991b1b",
                    alpha=0.8,
                    lw=2,
                )
            )
            ax.text(-1.05, 0.55, "chain", ha="center", va="center", fontsize=8, color="white", weight="bold")
            ax.annotate(
                "",
                xy=(1.5, -1.05),
                xytext=(-1.5, -1.05),
                arrowprops=dict(arrowstyle="->", color="#991b1b", lw=2.2),
            )
            ax.text(
                0,
                -1.32,
                "too big for pores → flows around",
                ha="center",
                fontsize=9,
                color="#991b1b",
            )
            ax.set_title("Large chain: EXCLUDED → elutes FIRST", fontsize=11, weight="bold", color="#991b1b")
        else:
            ax.add_patch(
                Circle(
                    (0.42, 0.42),
                    0.15,
                    facecolor="#3b82f6",
                    edgecolor="#1e3a8a",
                    alpha=0.95,
                    lw=2,
                )
            )
            ax.annotate(
                "",
                xy=(1.5, -1.05),
                xytext=(-1.5, -1.05),
                arrowprops=dict(arrowstyle="->", color="#1e3a8a", lw=1.2, ls="dashed"),
            )
            ax.text(
                0,
                -1.32,
                "wanders in and out of pores → delayed",
                ha="center",
                fontsize=9,
                color="#1e3a8a",
            )
            ax.set_title("Small chain: PERMEATES → elutes LAST", fontsize=11, weight="bold", color="#1e3a8a")
    fig.tight_layout()
    return fig


def elution_figure(t):
    """Column with three bands moving down + the chromatogram being recorded."""
    fig, (axc, axh) = plt.subplots(
        1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 2.3]}
    )
    # --- column ---
    axc.set_xlim(0, 1)
    axc.set_ylim(0, 1.08)
    axc.axis("off")
    axc.add_patch(
        Rectangle((0.18, 0), 0.64, 1.0, facecolor="#f1f5f9", edgecolor="#475569", lw=2)
    )
    axc.text(0.5, 1.03, "column", ha="center", fontsize=10, weight="bold")
    t_elute = [1.0 / v for v in BAND_V]
    for v, color, name in zip(BAND_V, BAND_COLORS, BAND_NAMES):
        y = 1.0 - v * t
        if y > 0.02:
            axc.add_patch(
                Rectangle((0.18, y - 0.04), 0.64, 0.08, facecolor=color, edgecolor="none", alpha=0.9)
            )
            axc.text(0.9, y, name.split()[0], va="center", fontsize=8, color=color, weight="bold")
    axc.text(0.5, 0.5, "flow ↓", ha="center", fontsize=9, color="#94a3b8")
    # --- chromatogram ---
    tg = np.linspace(0, T_MAX, 600)
    trace = np.zeros_like(tg)
    for te in t_elute:
        trace += np.exp(-0.5 * ((tg - te) / 0.13) ** 2)
    axh.set_xlim(0, T_MAX)
    axh.set_ylim(0, 1.4)
    axh.plot(tg, trace, color="#94a3b8", lw=1.4, alpha=0.55)
    recorded = np.where(tg <= t, trace, np.nan)
    axh.plot(tg, recorded, color="#0f172a", lw=2.6)
    axh.fill_between(tg, 0, np.where(tg <= t, trace, 0.0), color="#0f172a", alpha=0.10)
    axh.axvline(t, color="#0f172a", ls="--", lw=1)
    for te, color, name in zip(t_elute, BAND_COLORS, BAND_NAMES):
        if t >= te - 0.03:
            axh.text(te, 1.22, name, ha="center", fontsize=9, color=color, weight="bold")
    axh.set_xlabel("time →")
    axh.set_ylabel("detector signal")
    axh.set_title("Chromatogram being recorded", fontsize=11, weight="bold")
    axh.grid(alpha=0.3)
    fig.tight_layout()
    return fig


@st.fragment
def frag_tab_sep():
        st.header("Separation: big = fast, small = slow")
        st.write(
            "The beads are full of pores, and ideally nothing sticks — separation is purely by size. "
            "Chains too big for the pores stay in the fast lane; chains that fit take the scenic route."
        )
        st.pyplot(pore_figure())
        st.subheader("Watch it happen")
        st.write("Scrub through time (or animate) and see the bands separate inside the column while the detector draws the chromatogram.")
        t_now = st.slider("Time", 0.0, T_MAX, 0.0, 0.02, key="etime")
        animate = st.button("▶ Animate", key="eanim")
        ph = st.empty()
        if animate:
            for tt in np.linspace(0.0, T_MAX, 80):
                ph.pyplot(elution_figure(tt))
                time.sleep(0.045)
        else:
            ph.pyplot(elution_figure(t_now))
        st.info(
            "Notice the elution order: **large → medium → small**. "
            "This is backwards from most chromatography, where bigger things usually come out later."
        )


with tab_sep:
    frag_tab_sep()

# ----------------------------------------------------------------------------
# Tab 3: Chromatogram lab
# ----------------------------------------------------------------------------
def lognormal_mu_sig(Mn, D):
    """Natural-log mean/std of the number distribution from Mn and dispersity."""
    s2 = np.log(D)
    return np.log(Mn) - s2 / 2.0, np.sqrt(s2)


def chromatogram(logMn, D, t):
    """Weight-fraction chromatogram on the time grid t (calibration log10M = 7 - 0.25 t)."""
    Mn = 10.0**logMn
    Mw = Mn * D
    mu, sig = lognormal_mu_sig(Mn, D)
    xmean_w = (mu + sig**2) / np.log(10.0)  # weight-average of log10 M
    xsd = sig / np.log(10.0)
    x = 7.0 - 0.25 * t
    w = np.exp(-0.5 * ((x - xmean_w) / xsd) ** 2)
    w /= w.max()
    t_Mn = (7.0 - np.log10(Mn)) / 0.25
    t_Mw = (7.0 - np.log10(Mw)) / 0.25
    return t, w, t_Mn, t_Mw, Mn, Mw


@st.fragment
def frag_tab_chrom():
        st.header("Chromatogram lab")
        st.write(
            "Dial in a molecular-weight distribution and watch the chromatogram it produces. "
            "The distribution is log-normal — the standard model for polymer samples."
        )
        cc1, cc2 = st.columns([1, 2.2])
        with cc1:
            logMn_A = st.slider("Sample A: Mn (log₁₀ g/mol)", 3.0, 6.5, 5.0, 0.05)
            D_A = st.slider("Sample A: dispersity Đ = Mw/Mn", 1.05, 3.0, 1.5, 0.05)
            st.caption(f"Sample A Mn = {10.0**logMn_A:,.0f} g/mol")
            show_B = st.checkbox("Compare with sample B")
            if show_B:
                logMn_B = st.slider("Sample B: Mn (log₁₀ g/mol)", 3.0, 6.5, 4.7, 0.05)
                D_B = st.slider("Sample B: dispersity Đ = Mw/Mn", 1.05, 3.0, 2.2, 0.05)
                st.caption(f"Sample B Mn = {10.0**logMn_B:,.0f} g/mol")
        with cc2:
            t = np.linspace(2, 16, 500)
            fig, ax = plt.subplots(figsize=(9, 4.6))
            tA, wA, tMnA, tMwA, MnA, MwA = chromatogram(logMn_A, D_A, t)
            ax.plot(tA, wA, color="#3b82f6", lw=2.5, label="Sample A")
            ax.axvline(tMnA, color="#3b82f6", ls="--", lw=1.2, alpha=0.8)
            ax.axvline(tMwA, color="#3b82f6", ls=":", lw=1.6, alpha=0.8)
            ax.text(tMnA, 1.03, "Mn", ha="center", fontsize=9, color="#3b82f6", weight="bold")
            ax.text(tMwA, 0.94, "Mw", ha="center", fontsize=9, color="#3b82f6", weight="bold")
            if show_B:
                tB, wB, tMnB, tMwB, MnB, MwB = chromatogram(logMn_B, D_B, t)
                ax.plot(tB, wB, color="#f59e0b", lw=2.5, label="Sample B")
                ax.axvline(tMnB, color="#f59e0b", ls="--", lw=1.2, alpha=0.8)
            ax.set_xlim(2, 16)
            ax.set_ylim(0, 1.32)
            ax.set_xlabel("elution time (min) →")
            ax.set_ylabel("RI signal (normalized)")
            ax.set_title("Simulated chromatogram", fontsize=12, weight="bold")
            ax.legend()
            ax.grid(alpha=0.3)
            fig.tight_layout()
            st.pyplot(fig)
            m1, m2, m3 = st.columns(3)
            m1.metric("Sample A Mn", f"{MnA:,.0f} g/mol")
            m2.metric("Sample A Mw", f"{MwA:,.0f} g/mol")
            m3.metric("Sample A Đ", f"{D_A:.2f}")
            if show_B:
                n1, n2, n3 = st.columns(3)
                n1.metric("Sample B Mn", f"{MnB:,.0f} g/mol")
                n2.metric("Sample B Mw", f"{MwB:,.0f} g/mol")
                n3.metric("Sample B Đ", f"{D_B:.2f}")
        st.info(
            "Reading the plot: the **peak position** tells you the typical chain size, the **width** tells you "
            "the dispersity, and **shoulders or double peaks** mean a bimodal sample (e.g. a side reaction). "
            "Mn and Mw sit at different times because Mw weights the big chains more — and big chains elute earlier."
        )


with tab_chrom:
    frag_tab_chrom()

# ----------------------------------------------------------------------------
# Tab 4: Detectors — triple detection
# ----------------------------------------------------------------------------
@st.fragment
def frag_tab_det():
        st.header("Three detectors, three answers")
        st.write(
            "One peak flows past three detectors in series. Each sees something different — "
            "together they give mass, concentration, and shape at every point."
        )
        a_mh = st.slider(
            "Mark–Houwink exponent a (chain stiffness)", 0.3, 1.0, 0.7, 0.05, key="mh"
        )
        st.caption("a ≈ 0.5: compact coil · a ≈ 0.7–0.8: expanded coil in a good solvent · a → 1: stiff rod")
        Mn_d, D_d = 1e5, 1.6
        mu_d, sig_d = lognormal_mu_sig(Mn_d, D_d)
        td = np.linspace(2, 16, 600)
        xd = 7.0 - 0.25 * td
        Md = 10.0**xd
        xmean_d = (mu_d + sig_d**2) / np.log(10.0)
        xsd_d = sig_d / np.log(10.0)
        wd = np.exp(-0.5 * ((xd - xmean_d) / xsd_d) ** 2)
        wd /= wd.max()
        ri = wd
        mals = wd * Md
        mals /= mals.max()
        visc = wd * Md**a_mh
        visc /= visc.max()

        def peak_time(y):
            return td[int(np.argmax(y))]

        fig, axes = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True)
        specs = [
            (ri, "#3b82f6", "RI (Optilab rEX): concentration → how MUCH elutes when"),
            (mals, "#ef4444", "MALS (miniDAWN TREOS): ∝ concentration × mass → HOW BIG it is"),
            (visc, "#10b981", "Viscometer (Viscostar II): ∝ concentration × viscosity → chain SHAPE"),
        ]
        for ax, (y, color, title) in zip(axes, specs):
            ax.plot(td, y, color=color, lw=2.4)
            ax.axvline(peak_time(y), color=color, ls="--", lw=1.2, alpha=0.7)
            ax.set_ylabel("normalized")
            ax.set_title(title, fontsize=10, loc="left", color=color, weight="bold")
            ax.grid(alpha=0.3)
            ax.set_ylim(0, 1.15)
        axes[2].set_xlabel("elution time (min) →")
        fig.tight_layout()
        st.pyplot(fig)
        st.info(
            f"See how the peaks shift: the MALS peak (t = {peak_time(mals):.1f} min) comes out earlier than the RI peak "
            f"(t = {peak_time(ri):.1f} min), because light scattering weights each slice by its mass — the heavy chains "
            "dominate. That skew is exactly the extra information triple detection buys you."
        )


with tab_det:
    frag_tab_det()

# ----------------------------------------------------------------------------
# Tab 5: Calibration — three levels
# ----------------------------------------------------------------------------
@st.fragment
def frag_tab_cal():
        st.header("Calibration: three levels of sophistication")
        st.write(
            "The columns separate by hydrodynamic volume, not mass. How you convert that to "
            "molecular weight is a ladder — each rung more powerful than the last."
        )
        a_s = st.slider(
            "Sample's Mark–Houwink exponent a (polystyrene standards: a = 0.7)",
            0.5,
            0.95,
            0.6,
            0.05,
            key="cals",
        )
        st.caption(
            "Move the slider: the further your polymer's coil behavior is from polystyrene's, "
            "the more conventional calibration misreads it. (K held equal for illustration.)"
        )
        # Universal line: log10(Vh) = Au - Bu*t ; Vh = K*M^(1+a)
        Au, Bu = 9.17, 0.51
        K_mh, a_ps = 1.2e-4, 0.7
        tc = np.linspace(4, 14, 300)
        Vh = 10.0 ** (Au - Bu * tc)
        M_true = (Vh / K_mh) ** (1.0 / (1.0 + a_s))
        M_app = 10.0 ** ((Au - np.log10(K_mh)) / (1 + a_ps) - Bu * tc / (1 + a_ps))
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
        ax1.plot(tc, np.log10(M_app), color="#3b82f6", lw=2.4, label="PS conventional calibration")
        ts = np.array([5, 7, 9, 11, 13])
        ax1.scatter(
            ts,
            (Au - np.log10(K_mh)) / (1 + a_ps) - Bu * ts / (1 + a_ps),
            color="#3b82f6",
            s=45,
            zorder=5,
            label="PS standards",
        )
        ax1.plot(tc, np.log10(M_true), color="#ef4444", lw=2.4, ls="--", label="Sample true MW")
        ax1.fill_between(tc, np.log10(M_app), np.log10(M_true), color="#ef4444", alpha=0.12)
        ax1.set_xlabel("elution time (min)")
        ax1.set_ylabel("log₁₀ M")
        ax1.set_title("Level 1 — conventional: misreads the sample", fontsize=11, weight="bold")
        ax1.legend(fontsize=8)
        ax1.grid(alpha=0.3)
        ax2.plot(tc, np.log10(Vh), color="#10b981", lw=2.4)
        ax2.set_xlabel("elution time (min)")
        ax2.set_ylabel("log₁₀([η]·M)")
        ax2.set_title("Level 2 — universal: one line fits all", fontsize=11, weight="bold")
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        t0 = 9.0
        m_app_0 = 10.0 ** np.interp(t0, tc, np.log10(M_app))
        m_true_0 = 10.0 ** np.interp(t0, tc, np.log10(M_true))
        err = (m_app_0 / m_true_0 - 1.0) * 100.0
        c1, c2 = st.columns(2)
        c1.metric(f"At t = {t0:.0f} min, conventional reads", f"{m_app_0:,.0f} g/mol")
        c2.metric("True molecular weight there", f"{m_true_0:,.0f} g/mol", delta=f"{err:+.0f}% error")
        st.write(
            "**Level 1 — conventional:** run polystyrene standards, plot log M vs time. Simple, but only "
            "valid if your polymer coils like polystyrene. Result: 'polystyrene-equivalent' MW.\n\n"
            "**Level 2 — universal:** the columns separate by hydrodynamic volume, and [η]·M is proportional "
            "to it for *every* polymer. With the viscometer measuring [η] at each point, one curve works for "
            "any chemistry — the right-hand plot above.\n\n"
            "**Level 3 — light scattering:** skip curves entirely. MALS computes MW from the scattered light "
            "itself at each point. The gold standard — and it's sitting in your instrument."
        )


with tab_cal:
    frag_tab_cal()

# ----------------------------------------------------------------------------
# Tab 6: Disassembly checklist
# ----------------------------------------------------------------------------
CHECKLIST = {
    "Safety first": [
        "Pump stopped and system fully depressurized (gauge reads zero)",
        "PPE on: gloves and safety glasses",
        "Working in the fume hood; no ignition sources nearby (THF is very flammable)",
        "Asked mentor about the lab's THF peroxide-test routine",
    ],
    "Document everything": [
        "Photographed every tube route, fitting, and cable connection",
        "Labeled tubes and fittings as they were disconnected",
    ],
    "Columns — the crown jewels": [
        "Capped both ends of each column immediately after removal",
        "Columns kept wet — never allowed to dry out",
        "No drops or shocks; stored in original boxes if available",
    ],
    "Detectors and autosampler": [
        "Capped all flow-cell ports on the detectors",
        "Did NOT open any optical bench (MALS especially — dust on optics)",
        "Autosampler needle protected from bending",
    ],
    "Small parts": [
        "Ferrules, frits, and screws bagged and labeled",
    ],
    "Shipping": [
        "Asked the repair facility what solvent the system should be shipped in",
        "All THF waste collected for proper disposal — none down the drain",
    ],
}

@st.fragment
def frag_tab_check():
        st.header("Disassembly checklist — for tomorrow")
        st.write("Tick these off in the lab with your mentor. Safety items first.")
        done = 0
        total = 0
        for group, items in CHECKLIST.items():
            st.subheader(group)
            for i, item in enumerate(items):
                total += 1
                if st.checkbox(item, key=f"chk-{group}-{i}"):
                    done += 1
        st.progress(done / total if total else 0.0)
        st.write(f"**{done} of {total} done**")
        if done == total:
            st.success("All packed and ready to ship. Nice work.")
        st.warning(
            "If anything is pressurized, unfamiliar, or smells strongly of THF — stop and ask your mentor. "
            "This list is a memory aid, not a substitute for their instructions."
        )


with tab_check:
    frag_tab_check()

st.divider()
st.caption(
    "Study companion for learning the instrument — always follow your mentor's and your lab's "
    "procedures in the real lab."
)
