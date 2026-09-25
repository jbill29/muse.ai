"""Taylor-Couette flow visualizer: velocity profile between concentric rotating cylinders."""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Taylor-Couette Flow Visualizer", layout="wide")

# ---------------- Live widget (browser-side, 60 fps) ----------------
# Sliders live in the real Streamlit sidebar; plots live in the main tab.
# The two iframes share the same origin, so they sync through
# localStorage: the sidebar publishes on every input, the main
# widget redraws on the storage event. No server round-trip.
SIDEBAR_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root{
    --track:#dfe1e6; --lab:#31333f; --val:#31333f;
    --accent:#ff4b4b;
  }
  @media (prefers-color-scheme: dark){
    :root{ --track:#3a3d46; --lab:#e8eaf0; --val:#e8eaf0; }
  }
  html, body{ background:transparent; }
  body{
    font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0; padding:6px 10px 12px 4px; color:var(--lab);
  }
  .ptitle{ font-size:16px; font-weight:600; margin:2px 0 12px; }
  .sld{ margin-bottom:13px; }
  .labrow{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:2px; }
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
  input[type=range]::-moz-range-track{ height:4px; border-radius:2px; background:var(--track); }
  input[type=range]::-moz-range-progress{ height:4px; border-radius:2px; background:var(--accent); }
  input[type=range]::-moz-range-thumb{
    width:14px; height:14px; border:none; border-radius:50%;
    background:var(--accent); box-shadow:0 1px 3px rgba(0,0,0,.35);
  }
  input[type=range]:focus{ outline:none; }
  .chk{ display:flex; align-items:center; gap:8px; font-size:14px; margin:4px 0 10px; cursor:pointer; }
  .chk input{ accent-color:var(--accent); width:16px; height:16px; cursor:pointer; }
  #warn{ color:#ff6b6b; font-size:13px; margin-top:4px; display:none; line-height:1.4; }
</style>
</head>
<body>
<div class="ptitle">Controls</div>
<div class="sld"><div class="labrow"><span class="t">R&#8321; (m)</span><span class="v" id="o_R1"></span></div>
  <input id="s_R1" type="range" min="0.1" max="2" step="0.05" value="1" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">R&#8322; (m)</span><span class="v" id="o_R2"></span></div>
  <input id="s_R2" type="range" min="0.5" max="3" step="0.05" value="2" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">&omega;&#8321; (rad/s)</span><span class="v" id="o_w1"></span></div>
  <input id="s_w1" type="range" min="-5" max="5" step="0.1" value="2" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">&omega;&#8322; (rad/s)</span><span class="v" id="o_w2"></span></div>
  <input id="s_w2" type="range" min="-5" max="5" step="0.1" value="0.5" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">&mu; (Pa&middot;s)</span><span class="v" id="o_mu"></span></div>
  <input id="s_mu" type="range" min="0.01" max="2" step="0.01" value="0.5" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">&rho; (kg/m&sup3;)</span><span class="v" id="o_rho"></span></div>
  <input id="s_rho" type="range" min="500" max="2000" step="10" value="1000" data-dec="0"></div>
<div class="sld"><div class="labrow"><span class="t">Length L (m)</span><span class="v" id="o_Lcyl"></span></div>
  <input id="s_Lcyl" type="range" min="0.1" max="2" step="0.05" value="1" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">Vector density</span><span class="v" id="o_nvec"></span></div>
  <input id="s_nvec" type="range" min="8" max="24" step="1" value="14" data-dec="0"></div>
<label class="chk"><input type="checkbox" id="c_stream" checked> Overlay streamlines</label>
<div id="warn">Need R&#8322; &gt; R&#8321; &mdash; widen the outer radius or shrink the inner one.</div>
<script>
var KEY = 'couette_params_v1';
var IDS = ['R1','R2','w1','w2','mu','rho','Lcyl','nvec'];
var DEFS = { R1:1, R2:2, w1:2, w2:0.5, mu:0.5, rho:1000, Lcyl:1, nvec:14, showStream:true };
function el(id){ return document.getElementById(id); }
function store(){ try { return window.localStorage; } catch (e) { return null; } }
function refreshSlider(id){
  var s = el('s_'+id);
  var dec = parseInt(s.getAttribute('data-dec') || '2', 10);
  el('o_'+id).textContent = parseFloat(s.value).toFixed(dec);
  s.style.setProperty('--p', ((s.value - s.min) / (s.max - s.min) * 100) + '%');
}
function readParams(){
  var p = {}, ls = store(), raw = null;
  if (ls) { try { raw = ls.getItem(KEY); } catch (e) {} }
  if (raw) { try { p = JSON.parse(raw); } catch (e) { p = {}; } }
  var out = {}, k, v;
  for (k in DEFS){
    if (k === 'showStream') continue;
    v = p[k];
    out[k] = (typeof v === 'number' && isFinite(v)) ? v : DEFS[k];
  }
  out.showStream = (typeof p.showStream === 'boolean') ? p.showStream : true;
  return out;
}
function curParams(){
  var p = {}, i;
  for (i = 0; i < IDS.length; i++) p[IDS[i]] = parseFloat(el('s_'+IDS[i]).value);
  p.nvec = Math.round(p.nvec);
  p.showStream = el('c_stream').checked;
  return p;
}
function publish(){
  var ls = store();
  if (!ls) return;
  try { ls.setItem(KEY, JSON.stringify(curParams())); } catch (e) {}
}
function updateWarn(){
  var bad = parseFloat(el('s_R2').value) <= parseFloat(el('s_R1').value);
  el('warn').style.display = bad ? 'block' : 'none';
}
(function init(){
  var p = readParams(), i;
  for (i = 0; i < IDS.length; i++){
    el('s_'+IDS[i]).value = p[IDS[i]];
    refreshSlider(IDS[i]);
  }
  el('c_stream').checked = p.showStream;
  updateWarn();
  publish();
})();
IDS.forEach(function(id){
  el('s_'+id).addEventListener('input', function(){ refreshSlider(id); updateWarn(); publish(); });
});
el('c_stream').addEventListener('change', publish);
</script>
</body>
</html>
"""


MAIN_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root{
    --lab:#31333f; --val:#31333f; --sub:#6b7280; --box:#f1f5f9;
  }
  @media (prefers-color-scheme: dark){
    :root{ --lab:#e8eaf0; --val:#e8eaf0; --sub:#9aa0ae; --box:#232838; }
  }
  html, body{ background:transparent; }
  body{
    font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif;
    margin:0; padding:4px; color:var(--lab);
  }
  .abline{ font-size:14px; color:var(--sub); font-variant-numeric:tabular-nums; margin:4px 0 6px; }
  .plotrow{ display:flex; gap:8px; }
  .plotrow > div{ flex:1 1 0; min-width:0; }
  .note{ font-size:13px; color:var(--sub); margin-top:6px; line-height:1.45; }
  .vecrow{ display:flex; gap:18px; margin-top:14px; align-items:flex-start; flex-wrap:wrap; }
  #vecCanvas{ width:460px; max-width:100%; height:auto; }
  .vecside{ flex:1 1 240px; min-width:240px; }
  .vtitle{ font-size:16px; font-weight:600; margin-bottom:4px; }
  .banner{ padding:10px 12px; border-radius:8px; font-weight:600; font-size:14px; margin:12px 0 4px; line-height:1.4; }
  .banner.ok{ background:#d1fae5; color:#065f46; }
  .banner.bad{ background:#fee2e2; color:#991b1b; }
  @media (prefers-color-scheme: dark){
    .banner.ok{ background:rgba(16,185,129,.16); color:#6ee7b7; }
    .banner.bad{ background:rgba(239,68,68,.16); color:#fca5a5; }
  }
  .mgrid{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:130px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
  .sec{ font-size:14px; font-weight:600; margin:14px 0 2px; }
</style>
</head>
<body>
<div class="abline" id="abLine"></div>
<div class="plotrow"><div id="plotV"></div><div id="plotT"></div></div>
<div class="note">Shear magnitude is largest at the inner wall; the sign gives the stress direction relative to +&theta;.</div>
<div class="vecrow">
  <canvas id="vecCanvas" width="460" height="460"></canvas>
  <div class="vecside">
    <div class="vtitle">Cross-section vector field (r&ndash;&theta; plane)</div>
    <div class="note">Arrows show the local fluid velocity. Length is proportional to speed; color (viridis) also encodes speed.</div>
    <div class="sec">Torque transmitted through the fluid</div>
    <div class="mgrid" id="torqueM"></div>
    <div class="sec">Taylor-vortex threshold</div>
    <div class="banner" id="taylorBanner"></div>
    <div class="mgrid" id="taylorM"></div>
    <div class="note">Ta = &omega;&#8321;&sup2;d&sup3;R&#8321;/&nu;&sup2;, critical 1708 (narrow-gap, outer cylinder at rest). Spin the inner cylinder fast enough and the smooth laminar flow breaks into stacked Taylor vortices.</div>
  </div>
</div>
<script>
var KEY = 'couette_params_v1';
var DEFS = { R1:1, R2:2, w1:2, w2:0.5, mu:0.5, rho:1000, Lcyl:1, nvec:14, showStream:true };
function el(id){ return document.getElementById(id); }
function store(){ try { return window.localStorage; } catch (e) { return null; } }
function readParams(){
  var p = {}, ls = store(), raw = null;
  if (ls) { try { raw = ls.getItem(KEY); } catch (e) {} }
  if (raw) { try { p = JSON.parse(raw); } catch (e) { p = {}; } }
  var out = {}, k, v;
  for (k in DEFS){
    if (k === 'showStream') continue;
    v = p[k];
    out[k] = (typeof v === 'number' && isFinite(v)) ? v : DEFS[k];
  }
  out.showStream = (typeof p.showStream === 'boolean') ? p.showStream : true;
  out.nvec = Math.round(out.nvec);
  return out;
}
function isDark(){ return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; }
function themed(title){
  var d = isDark(), grid = d ? '#2e3138' : '#e5e7eb';
  return {
    title: title, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: '"Source Sans Pro",sans-serif', color: d ? '#e8eaf0' : '#31333f' },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
    margin: { l: 55, r: 10, t: 40, b: 40 }
  };
}
/* viridis colormap stops */
var VIR = [[68,1,84],[72,35,116],[64,67,135],[52,94,141],[41,120,142],[32,144,140],
           [34,167,133],[68,190,112],[121,209,81],[189,222,38],[253,231,37]];
function vcolor(t){
  t = Math.max(0, Math.min(1, t));
  var x = t * (VIR.length - 1), i = Math.floor(x), f = x - i;
  var a = VIR[i], b = VIR[Math.min(i + 1, VIR.length - 1)];
  function c(k){ return Math.round(a[k] + (b[k] - a[k]) * f); }
  return 'rgb(' + c(0) + ',' + c(1) + ',' + c(2) + ')';
}
function draw(){
  var p = readParams();
  if (p.R2 <= p.R1) return; /* keep last frame; the sidebar shows the warning */
  var den = p.R2 * p.R2 - p.R1 * p.R1;
  var A = (p.w2 * p.R2 * p.R2 - p.w1 * p.R1 * p.R1) / den;
  var B = (p.w1 - p.w2) * p.R1 * p.R1 * p.R2 * p.R2 / den;
  /* --- line plots --- */
  var N = 240, r = [], v = [], tau = [], i, ri;
  for (i = 0; i < N; i++){
    ri = p.R1 + (p.R2 - p.R1) * i / (N - 1);
    r.push(ri); v.push(A * ri + B / ri); tau.push(-2 * p.mu * B / (ri * ri));
  }
  var dark = isDark(), wallC = dark ? '#8a8f98' : 'gray';
  var walls = [p.R1, p.R2].map(function(x){
    return { type: 'line', x0: x, x1: x, y0: 0, y1: 1, yref: 'paper',
             line: { dash: 'dash', color: wallC, width: 1 } };
  });
  var cfg = { displayModeBar: true, responsive: true };
  var L1 = themed('Azimuthal velocity across the gap');
  L1.xaxis.title = 'r'; L1.yaxis.title = 'v\u03b8(r)'; L1.shapes = walls; L1.height = 320;
  Plotly.react('plotV', [{ x: r, y: v, mode: 'lines', line: { width: 3, color: '#1f77b4' } }], L1, cfg);
  var L2 = themed('Shear stress across the gap');
  L2.xaxis.title = 'r'; L2.yaxis.title = '\u03c4(r)'; L2.shapes = walls; L2.height = 320;
  Plotly.react('plotT', [{ x: r, y: tau, mode: 'lines', line: { width: 3, color: '#ff7f0e' } }], L2, cfg);
  /* --- vector field on canvas --- */
  drawVec(p, A, B);
  /* --- readouts --- */
  var Tt = 4 * Math.PI * p.mu * p.Lcyl * Math.abs(B);
  el('abLine').textContent = 'v\u03b8(r) = A\u00b7r + B/r   with   A = ' + A.toFixed(3) + ',   B = ' + B.toFixed(3);
  el('torqueM').innerHTML =
    '<div class="mbox"><div class="k">Torque |T|</div><div class="n">' + Tt.toFixed(4) +
    ' N\u00b7m</div><div class="d">Same at every radius (angular-momentum balance)</div></div>';
  var nu = p.mu / p.rho, d = p.R2 - p.R1, TaCrit = 1708;
  var Ta = p.w1 * p.w1 * d * d * d * p.R1 / (nu * nu);
  var w1c = Math.sqrt(TaCrit * nu * nu / (d * d * d * p.R1));
  var lam = Ta < TaCrit, bn = el('taylorBanner');
  bn.className = 'banner ' + (lam ? 'ok' : 'bad');
  bn.textContent = lam
    ? 'LAMINAR \u2014 Taylor number below critical; the profile above applies.'
    : 'TAYLOR VORTICES expected \u2014 Taylor number above critical; the laminar profile above no longer describes the flow.';
  el('taylorM').innerHTML =
    '<div class="mbox"><div class="k">Taylor number Ta</div><div class="n">' + Ta.toPrecision(4) +
    '</div></div>' +
    '<div class="mbox"><div class="k">Critical inner speed \u03c9\u2081,c</div><div class="n">' +
    w1c.toFixed(4) + ' rad/s</div></div>';
}
function drawVec(p, A, B){
  var cv = el('vecCanvas'), ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  ctx.clearRect(0, 0, W, H);
  var cx = W / 2, cy = H / 2, dark = isDark();
  var ext = p.R2 * 1.15, sc = (Math.min(W, H) / 2 - 12) / ext;
  function X(x){ return cx + x * sc; }
  function Y(y){ return cy - y * sc; }
  ctx.lineWidth = 3; ctx.strokeStyle = dark ? '#cbd5e1' : '#0f172a';
  [p.R1, p.R2].forEach(function(rr){
    ctx.beginPath(); ctx.arc(cx, cy, rr * sc, 0, Math.PI * 2); ctx.stroke();
  });
  var n = p.nvec, x0 = -p.R2 * 1.1, dx = (2 * p.R2 * 1.1) / (n - 1);
  var pts = [], vmax = 0, i, j;
  for (i = 0; i < n; i++) for (j = 0; j < n; j++){
    var bx = x0 + dx * i, by = x0 + dx * j, rr = Math.sqrt(bx * bx + by * by);
    if (rr < p.R1 || rr > p.R2) continue;
    var th = Math.atan2(by, bx), vv = A * rr + B / rr, sp = Math.abs(vv);
    pts.push({ bx: bx, by: by, vx: -vv * Math.sin(th), vy: vv * Math.cos(th), sp: sp });
    if (sp > vmax) vmax = sp;
  }
  if (vmax <= 0) vmax = 1;
  var k = 0.8 * dx / vmax;
  pts.forEach(function(q){
    if (q.sp < 1e-9 * vmax) return;
    var ux = q.vx * k, uy = q.vy * k;
    var x1 = X(q.bx - ux / 2), y1 = Y(q.by - uy / 2);
    var x2 = X(q.bx + ux / 2), y2 = Y(q.by + uy / 2);
    var ang = Math.atan2(y2 - y1, x2 - x1);
    var hl = Math.min(9, 0.35 * Math.hypot(x2 - x1, y2 - y1));
    ctx.strokeStyle = vcolor(q.sp / vmax); ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x2, y2); ctx.lineTo(x2 - hl * Math.cos(ang - 0.42), y2 - hl * Math.sin(ang - 0.42));
    ctx.moveTo(x2, y2); ctx.lineTo(x2 - hl * Math.cos(ang + 0.42), y2 - hl * Math.sin(ang + 0.42));
    ctx.stroke();
  });
  if (p.showStream){
    ctx.strokeStyle = dark ? 'rgba(255,255,255,0.5)' : 'rgba(100,116,139,0.55)';
    ctx.lineWidth = 1;
    for (var s = 1; s < 12; s++){
      var rs = p.R1 + (p.R2 - p.R1) * s / 12;
      ctx.beginPath(); ctx.arc(cx, cy, rs * sc, 0, Math.PI * 2); ctx.stroke();
    }
  }
}
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
window.addEventListener('storage', function(e){ if (e.key === KEY) draw(); });
draw();
</script>
</body>
</html>
"""



# One embedded widget holds the sticky control panel plus every
# visualization: v_theta(r) and tau(r) curves, the cross-section vector
# field, torque, and the Taylor-vortex panel. All math runs as
# JavaScript in the browser, so dragging a slider morphs everything
# continuously with no server round-trip.

with st.sidebar:
    components.html(SIDEBAR_HTML, height=600, scrolling=False)


tab_vis, tab_theory = st.tabs(["Visualization", "Theory: derivation without Navier–Stokes"])

with tab_vis:
    st.markdown(
        "Drag any slider in the **sidebar**: every plot updates **live in your browser**, "
        "no server round-trip. Your settings are remembered between visits."
    )
    components.html(MAIN_HTML, height=900, scrolling=False)

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

