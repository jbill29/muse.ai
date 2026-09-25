"""Taylor-Couette flow visualizer: velocity profile between concentric rotating cylinders."""
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

st.set_page_config(page_title="Taylor-Couette Flow Visualizer", layout="wide")

# ---------------- Physics ----------------
def couette_coeffs(R1, R2, w1, w2):
    """Return A, B for v_theta(r) = A*r + B/r."""
    denom = R2**2 - R1**2
    A = (w2 * R2**2 - w1 * R1**2) / denom
    B = (w1 - w2) * R1**2 * R2**2 / denom
    return A, B

def v_theta(r, A, B):
    return A * r + B / r

def omega(r, A, B):
    return A + B / r**2

LIVE_PLOTS_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root{
    --track:#dfe1e6; --lab:#31333f; --val:#31333f; --sub:#6b7280;
    --accent:#ff4b4b;
  }
  @media (prefers-color-scheme: dark){
    :root{ --track:#3a3d46; --lab:#e8eaf0; --val:#e8eaf0; --sub:#9aa0ae; }
  }
  html, body{ background:transparent; }
  body{
    font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0; color:var(--lab);
  }
  .wrap{ display:flex; gap:18px; align-items:flex-start; }
  .side{ width:228px; flex:0 0 228px; padding:6px 2px 0 6px; }
  .sld{ margin-bottom:16px; }
  .labrow{ display:flex; justify-content:space-between; align-items:baseline;
           margin-bottom:2px; }
  .labrow .t{ font-size:14px; color:var(--lab); }
  .labrow .v{ font-size:14px; color:var(--val); font-variant-numeric:tabular-nums; }
  input[type=range]{
    -webkit-appearance:none; appearance:none;
    width:100%; height:20px; background:transparent; cursor:pointer; margin:0;
  }
  input[type=range]::-webkit-slider-runnable-track{
    height:4px; border-radius:2px;
    background:linear-gradient(to right,
      var(--accent) 0%, var(--accent) var(--p,50%),
      var(--track) var(--p,50%), var(--track) 100%);
  }
  input[type=range]::-webkit-slider-thumb{
    -webkit-appearance:none; appearance:none;
    width:14px; height:14px; border-radius:50%;
    background:var(--accent); margin-top:-5px; border:none;
    box-shadow:0 1px 3px rgba(0,0,0,.35);
  }
  input[type=range]::-moz-range-track{
    height:4px; border-radius:2px; background:var(--track);
  }
  input[type=range]::-moz-range-progress{
    height:4px; border-radius:2px; background:var(--accent);
  }
  input[type=range]::-moz-range-thumb{
    width:14px; height:14px; border:none; border-radius:50%;
    background:var(--accent); box-shadow:0 1px 3px rgba(0,0,0,.35);
  }
  input[type=range]:focus{ outline:none; }
  #ab{ font-size:13px; color:var(--sub); font-variant-numeric:tabular-nums;
       margin-top:4px; }
  #warn{ color:#ff6b6b; font-size:13px; margin-top:4px; display:none; }
  .plots{ flex:1 1 auto; display:flex; gap:8px; min-width:0; }
  .plots > div{ flex:1 1 0; min-width:0; }
</style>
</head>
<body>
<div class="wrap">
  <div class="side">
    <div class="sld">
      <div class="labrow"><span class="t">R&#8321; (m)</span><span class="v" id="oR1">1.00</span></div>
      <input id="sR1" type="range" min="0.1" max="2" step="0.05" value="1">
    </div>
    <div class="sld">
      <div class="labrow"><span class="t">R&#8322; (m)</span><span class="v" id="oR2">2.00</span></div>
      <input id="sR2" type="range" min="0.5" max="3" step="0.05" value="2">
    </div>
    <div class="sld">
      <div class="labrow"><span class="t">&omega;&#8321; (rad/s)</span><span class="v" id="ow1">2.0</span></div>
      <input id="sw1" type="range" min="-5" max="5" step="0.1" value="2">
    </div>
    <div class="sld">
      <div class="labrow"><span class="t">&omega;&#8322; (rad/s)</span><span class="v" id="ow2">0.5</span></div>
      <input id="sw2" type="range" min="-5" max="5" step="0.1" value="0.5">
    </div>
    <div class="sld">
      <div class="labrow"><span class="t">&mu; (Pa&middot;s)</span><span class="v" id="omu">0.50</span></div>
      <input id="smu" type="range" min="0.01" max="2" step="0.01" value="0.5">
    </div>
    <div id="ab"></div>
    <div id="warn">Need R&#8322; &gt; R&#8321; &mdash; widen the outer radius or shrink the inner one.</div>
  </div>
  <div class="plots">
    <div id="plotV"></div>
    <div id="plotT"></div>
  </div>
</div>
<script>
function val(id){ return parseFloat(document.getElementById(id).value); }
function paintTrack(el){
  var p = (el.value - el.min) / (el.max - el.min) * 100;
  el.style.setProperty('--p', p + '%');
}
function dark(){ return window.matchMedia('(prefers-color-scheme: dark)').matches; }
function draw(){
  var R1 = val('sR1'), R2 = val('sR2'), w1 = val('sw1'),
      w2 = val('sw2'), mu = val('smu');
  document.getElementById('oR1').textContent = R1.toFixed(2);
  document.getElementById('oR2').textContent = R2.toFixed(2);
  document.getElementById('ow1').textContent = w1.toFixed(1);
  document.getElementById('ow2').textContent = w2.toFixed(1);
  document.getElementById('omu').textContent = mu.toFixed(2);
  ['sR1','sR2','sw1','sw2','smu'].forEach(function(id){
    paintTrack(document.getElementById(id));
  });
  var warn = document.getElementById('warn');
  if (R2 <= R1){ warn.style.display = 'block'; return; }
  warn.style.display = 'none';
  var den = R2*R2 - R1*R1;
  var A = (w2*R2*R2 - w1*R1*R1) / den;
  var B = (w1 - w2)*R1*R1*R2*R2 / den;
  document.getElementById('ab').textContent = 'A = ' + A.toFixed(3) + '    B = ' + B.toFixed(3);
  var N = 240, r = [], v = [], tau = [];
  for (var i = 0; i < N; i++){
    var ri = R1 + (R2 - R1)*i/(N - 1);
    r.push(ri);
    v.push(A*ri + B/ri);
    tau.push(-2*mu*B/(ri*ri));
  }
  var isDark = dark();
  var grid = isDark ? '#2e3138' : '#e5e7eb';
  var wallColor = isDark ? '#8a8f98' : 'gray';
  var walls = [
    {type:'line', x0:R1, x1:R1, y0:0, y1:1, yref:'paper',
     line:{dash:'dash', color:wallColor, width:1}},
    {type:'line', x0:R2, x1:R2, y0:0, y1:1, yref:'paper',
     line:{dash:'dash', color:wallColor, width:1}}
  ];
  function layout(title, yt){
    return {
      title: title,
      xaxis: {title:'r', gridcolor:grid, zerolinecolor:grid},
      yaxis: {title:yt, gridcolor:grid, zerolinecolor:grid},
      shapes: walls,
      margin: {l:55, r:10, t:45, b:40},
      height: 420,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {family:'"Source Sans Pro",sans-serif',
             color: isDark ? '#e8eaf0' : '#31333f'}
    };
  }
  var cfg = {displayModeBar:true, responsive:true};
  Plotly.react('plotV',
    [{x:r, y:v, mode:'lines', line:{width:3, color:'#1f77b4'}}],
    layout('Azimuthal velocity across the gap', 'v\u03b8(r)'), cfg);
  Plotly.react('plotT',
    [{x:r, y:tau, mode:'lines', line:{width:3, color:'#ff7f0e'}}],
    layout('Shear stress across the gap', '\u03c4(r)'), cfg);
}
document.querySelectorAll('input[type=range]').forEach(function(el){
  el.addEventListener('input', draw);
});
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
draw();
</script>
</body>
</html>
"""


@st.fragment
def visualization():
    """Interactive visualization: sliders + every plot live in one fragment,
    so dragging a slider reruns only this block instead of the whole app."""
    st.write("Drag a slider — every plot below updates instantly.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Geometry**")
        R1 = st.slider("Inner radius R1", 0.1, 2.0, 1.0, 0.05)
        R2 = st.slider("Outer radius R2", 0.5, 3.0, 2.0, 0.05)
        if R2 <= R1:
            st.error("R2 must be larger than R1")
            st.stop()
    with c2:
        st.markdown("**Rotation**")
        w1 = st.slider("Inner angular velocity ω1 (rad/s)", -5.0, 5.0, 2.0, 0.1)
        w2 = st.slider("Outer angular velocity ω2 (rad/s)", -5.0, 5.0, 0.5, 0.1)
    with c3:
        st.markdown("**Fluid & cylinder (Newtonian)**")
        mu = st.slider("Dynamic viscosity μ (Pa·s)", 0.01, 2.0, 0.5, 0.01)
        rho = st.slider("Density ρ (kg/m³)", 100.0, 2000.0, 1000.0, 10.0)
        Lcyl = st.slider("Cylinder length L (m)", 0.1, 5.0, 1.0, 0.1)
        n_vec = st.slider("Vector field density", 10, 30, 18, 1)
        show_stream = st.checkbox("Overlay streamlines", value=True)

    A, B = couette_coeffs(R1, R2, w1, w2)
    T_torque = -4 * np.pi * mu * Lcyl * B  # N·m, signed

    # ---------------- Taylor-vortex threshold (narrow-gap criterion) ----------------
    # Convention: Ta = w1^2 * d^3 * R1 / nu^2, critical Ta_c = 1708
    # (narrow-gap limit, outer cylinder at rest; Taylor 1923).
    # Kinematic viscosity nu = mu / rho, hence the density input above.
    d_gap = R2 - R1
    nu = mu / rho
    TA_CRIT = 1708.0
    Ta = w1**2 * d_gap**3 * R1 / nu**2 if nu > 0 else float("inf")
    w1_crit = (TA_CRIT * nu**2 / (d_gap**3 * R1)) ** 0.5
    is_laminar = Ta < TA_CRIT

    st.subheader("Live playground \u2014 velocity & shear stress")
    st.caption(
        "Drag the sliders: both curves morph in real time, computed entirely in "
        "your browser with no server round-trip. These sliders drive only these "
        "two plots; the controls above drive the vector field, torque, and "
        "Taylor panel below."
    )
    components.html(LIVE_PLOTS_HTML, height=500, scrolling=False)

    st.latex(r"v_\theta(r) = A r + \frac{B}{r}")
    st.latex(
        r"A = \frac{\omega_2 R_2^2 - \omega_1 R_1^2}{R_2^2 - R_1^2}"
        r",\quad B = \frac{(\omega_1 - \omega_2) R_1^2 R_2^2}{R_2^2 - R_1^2}"
    )
    st.latex(r"\tau(r) = \mu\,r\,\frac{d\Omega}{dr} = -\frac{2\,\mu\,B}{r^2}")
    st.write(
        f"Values from the controls above: A = {A:.3f}, B = {B:.3f}, "
        f"T = {T_torque:.4f} N\u00b7m. Shear magnitude is largest at the inner wall; "
        "the sign gives the stress direction relative to +\u03b8."
    )

    st.subheader("Torque transmitted through the fluid")
    st.latex(r"T = -4\,\pi\,\mu\,L\,B")
    st.metric(
        "Torque |T|",
        f"{abs(T_torque):.4f} N·m",
        help="Same at every radius in steady flow (angular-momentum balance).",
    )
    st.caption(
        f"μ = {mu} Pa·s, L = {Lcyl} m. "
        "The sign of T indicates direction; the magnitude is what the motor must supply."
    )

    st.subheader("Taylor-vortex threshold")
    st.markdown(
        "Spin the inner cylinder fast enough and the smooth laminar flow above "
        "breaks down into a stack of donut-shaped Taylor vortices. This panel flags "
        "whether your current settings stay laminar."
    )
    if is_laminar:
        st.success("LAMINAR — Taylor number below critical; the profile above applies.")
    else:
        st.error(
            "TAYLOR VORTICES expected — Taylor number above critical; "
            "the laminar profile above no longer describes the flow."
        )
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.metric(
            "Taylor number Ta",
            f"{Ta:.4g}",
            help="Ta = ω1² d³ R1 / ν². Laminar while Ta < 1708.",
        )
    with tcol2:
        st.metric(
            "Critical inner speed ω1,c",
            f"{w1_crit:.4g} rad/s",
            help="Inner-cylinder speed at which Ta reaches 1708 for this geometry and fluid.",
        )
    st.latex(r"Ta = \frac{\omega_1^2\, d^3\, R_1}{\nu^2}, \qquad Ta_c = 1708")
    st.markdown(
        "**Why it happens (geometric picture).** Picture a thin ring of fluid nudged "
        "slightly outward. Out there its neighbors move more slowly, but the displaced "
        "ring keeps its faster spin — so centrifugal force flings it further outward, "
        "while slower fluid sinks inward to take its place. Viscosity tries to smear "
        "this motion out, and at gentle spin rates it wins. Past a critical rate the "
        "centrifugal imbalance wins instead, and the runaway motion rolls up into a "
        "stack of donut-shaped vortices."
    )
    st.caption(
        "Convention: Ta = ω1²d³R1/ν² with critical value 1708 (narrow-gap limit, outer "
        "cylinder at rest). Approximate when the gap is wide or ω2 ≠ 0 — counter-rotation "
        "and wide gaps shift the true threshold."
    )

    st.subheader("Cross-section vector field (r–θ plane)")
    st.markdown(
        "Arrows show the local fluid velocity. Their length is proportional to speed; "
        "color also encodes speed."
    )
    # Vector field on a Cartesian grid, masked to the annulus
    n = n_vec
    x = np.linspace(-R2 * 1.1, R2 * 1.1, n)
    y = np.linspace(-R2 * 1.1, R2 * 1.1, n)
    X, Y = np.meshgrid(x, y)
    Rs = np.sqrt(X**2 + Y**2)
    mask = (Rs >= R1) & (Rs <= R2)
    Theta = np.arctan2(Y, X)
    Vt = np.full_like(Rs, np.nan)
    Vt[mask] = v_theta(Rs[mask], A, B)
    Vx = np.full_like(Rs, np.nan)
    Vy = np.full_like(Rs, np.nan)
    Vx[mask] = -Vt[mask] * np.sin(Theta[mask])
    Vy[mask] = Vt[mask] * np.cos(Theta[mask])
    speed = np.sqrt(Vx**2 + Vy**2)

    # Arrow sizing: normalize so the longest arrow spans 0.8x the grid
    # spacing. This guarantees no excessive overlap at any slider setting,
    # while color still encodes the absolute speed.
    dx = float(x[1] - x[0])
    vmax = float(np.nanmax(speed)) if np.any(mask) else 0.0
    if vmax > 0:
        _s = 0.8 * dx / vmax
        Ux, Uy = Vx * _s, Vy * _s
    else:
        Ux, Uy = Vx, Vy

    fig3, ax3 = plt.subplots(figsize=(7, 7))
    # draw cylinder walls
    th = np.linspace(0, 2 * np.pi, 200)
    ax3.plot(R1 * np.cos(th), R1 * np.sin(th), "k-", lw=3, label="Inner wall")
    ax3.plot(R2 * np.cos(th), R2 * np.sin(th), "k-", lw=3, label="Outer wall")
    q = ax3.quiver(
        X, Y, Ux, Uy, speed,
        cmap="viridis", scale=1, scale_units="xy",
        width=0.012, pivot="mid",
    )
    if show_stream:
        # Streamlines of purely azimuthal flow are exact circles r = const,
        # so draw them analytically. (streamplot requires a rectangular grid
        # and rejects the polar grid used here.)
        for rr in np.linspace(R1, R2, 14)[1:-1]:
            ax3.plot(
                rr * np.cos(th), rr * np.sin(th),
                color="white", lw=0.7, alpha=0.85,
            )
    ax3.set_aspect("equal")
    ax3.set_xlim(-R2 * 1.15, R2 * 1.15)
    ax3.set_ylim(-R2 * 1.15, R2 * 1.15)
    ax3.set_xlabel("x")
    ax3.set_ylabel("y")
    ax3.set_title("Velocity vectors in the annulus")
    fig3.colorbar(q, ax=ax3, label="speed |v|")
    ax3.legend(loc="upper right")
    st.pyplot(fig3)


st.title("Taylor–Couette Flow: Velocity Between Concentric Cylinders")
st.markdown(
    "Laminar azimuthal flow in the gap between two independently rotating cylinders. "
    "Use the controls at the top of the Visualization tab — every plot updates instantly."
)

tab_vis, tab_theory = st.tabs(["Visualization", "Theory: derivation without Navier–Stokes"])

with tab_vis:
    visualization()

with tab_theory:
    st.header("Theory: the profile from symmetry, torque balance, and geometry")
    st.markdown(
        "_No Navier–Stokes equations are invoked. Everything follows from_ "
        "_symmetry, the no-slip condition, steady angular-momentum balance, "
        "_and a geometric picture of shear between curved layers._"
    )

    st.subheader("1. What the flow must look like (symmetry)")
    st.markdown(
        "The setup is invariant under rotations about the axis and translations along it. "
        "In a steady laminar state we expect the same symmetries in the flow: no dependence "
        "on angle θ or height z, no radial or axial motion (nothing drives fluid inward or "
        "upward), so the velocity is purely azimuthal and a function of radius alone:"
    )
    st.latex(r"\mathbf{v} = v_\theta(r)\,\hat{\boldsymbol{\theta}}, \qquad \Omega(r) \equiv \frac{v_\theta(r)}{r}")

    st.subheader("2. No-slip at the walls")
    st.markdown(
        "Fluid in contact with a solid wall moves with the wall. The walls are the two "
        "cylinder surfaces, so:"
    )
    st.latex(r"v_\theta(R_1) = \omega_1 R_1, \qquad v_\theta(R_2) = \omega_2 R_2")

    st.subheader("3. Torque on any cylindrical shell is the same (steady angular momentum)")
    st.markdown(
        "Picture a thin cylindrical shell of fluid at radius r, of length L. Its angular "
        "momentum can only change if there is a net torque on it. In steady flow the angular "
        "momentum of every shell is constant, and there are no body torques — so the torque "
        "exerted by the fluid inside r on the shell must exactly balance the torque exerted "
        "by the fluid outside r. Hence the torque transmitted across _every_ cylindrical "
        "surface is the same constant T."
    )
    st.latex(r"T(r) = T = \text{constant (independent of } r\text{)}")
    st.markdown(
        "Torque = (tangential shear force) × (lever arm). On a cylinder of radius r and "
        "length L, area = 2πrL, shear stress = τ(r), lever arm = r:"
    )
    st.latex(r"T = \tau(r)\,(2\pi r L)\,r = 2\pi L\,r^2\,\tau(r) = \text{const}")

    st.subheader("4. Shear rate from geometry: neighboring rings slide by r·dΩ/dr")
    st.markdown(
        "Consider two nearby rings at r and r + dr, rotating at Ω(r) and Ω(r + dr). "
        "In a short time dt, the outer ring advances by an extra angle dΩ·dt relative to "
        "the inner ring. A small fluid element spanning the gap gets tilted: the tangential "
        "displacement difference across dr is r·dΩ·dt. Dividing by dr·dt gives the rate of "
        "angular shear strain:"
    )
    st.latex(r"\dot{\gamma}(r) = r\,\frac{d\Omega}{dr}")
    st.markdown(
        "Physical check: if the whole fluid rotates as a solid body (Ω = const), there is no "
        "sliding between rings and the shear is zero — the formula gives exactly that. "
        "For a Newtonian fluid, shear stress is proportional to shear rate, τ = μ·γ̇, so:"
    )
    st.latex(r"\tau(r) = \mu\, r\,\frac{d\Omega}{dr}")

    st.subheader("5. Constant torque → a simple differential equation")
    st.markdown("Insert the shear stress into the torque expression:")
    st.latex(r"T = 2\pi L\,r^2 \left(\mu\, r\,\frac{d\Omega}{dr}\right) = 2\pi\mu L\,r^3\frac{d\Omega}{dr}")
    st.markdown("Since T is constant, so is the combination r³·dΩ/dr:")
    st.latex(r"r^3\,\frac{d\Omega}{dr} = C \quad (\text{constant})")
    st.markdown("This is the whole dynamics in one line — no PDEs needed. Integrate:")
    st.latex(r"\frac{d\Omega}{dr} = \frac{C}{r^3} \;\;\Longrightarrow\;\; \Omega(r) = A - \frac{C}{2r^2}")
    st.markdown("Multiply by r to get the linear velocity, and rename the constant:")
    st.latex(r"\boxed{\,v_\theta(r) = A\,r + \frac{B}{r}\,}")
    st.markdown(
        "Geometric reading: the **Ar** term is solid-body rotation (rings moving together, "
        "no shear); the **B/r** term is a potential-vortex swirl (fast near the center, "
        "required whenever the cylinders rotate at different rates, because torque must "
        "still be transmitted uniformly)."
    )

    st.subheader("6. Fix A and B from the walls")
    st.markdown("Apply the no-slip conditions:")
    st.latex(r"\begin{cases} A R_1 + B/R_1 = \omega_1 R_1 \\ A R_2 + B/R_2 = \omega_2 R_2 \end{cases}")
    st.markdown("Solving the two linear equations:")
    st.latex(
        r"\boxed{\,A = \frac{\omega_2 R_2^2 - \omega_1 R_1^2}{R_2^2 - R_1^2}\,},"
        r"\qquad \boxed{\,B = \frac{(\omega_1 - \omega_2)\,R_1^2 R_2^2}{R_2^2 - R_1^2}\,}"
    )

    st.subheader("7. Sanity checks (purely physical)")
    st.markdown(
        "- **Both cylinders spin together** (ω₁ = ω₂ = ω): then B = 0 and A = ω, so "
        "v_θ = ωr — solid-body rotation, zero shear, as expected.\n"
        "- **Narrow gap** (R₂ − R₁ ≪ R₁): expand the profile and it becomes nearly linear "
        "across the gap — locally it looks like simple shear between parallel plates.\n"
        "- **Outer cylinder at rest, inner spinning**: B ≠ 0 gives the characteristic "
        "1/r decay of a vortex, steepest near the inner wall where the shear is largest.\n"
        "- **Torque**: T = −4πμL·B, so the constant B directly measures the torque "
        "transmitted through the fluid — one number, same at every radius."
    )
    st.latex(r"T = -4\pi\,\mu\,L\,B")
