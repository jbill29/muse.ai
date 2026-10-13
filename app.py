"""Hagen-Poiseuille visualizer: laminar flow in a circular pipe, derived from
first principles. Tab 1 balances pressure force against viscous shear on an
imaginary fluid cylinder to get the parabolic velocity profile; Tab 2
integrates the parabola to the Hagen-Poiseuille law Q = pi*DP*D^4/(128*mu*L).

All graphics run as JavaScript in the browser at 60 fps: the real Streamlit
sidebar publishes slider values through localStorage, and each tab's widget
redraws on the storage event. No server round-trip while dragging.
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Hagen-Poiseuille: laminar pipe flow", layout="wide")

# ---------------- Sidebar controls (publishes to localStorage) ----------------
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
  .snote{ font-size:12.5px; color:var(--lab); opacity:.75; margin-top:6px; line-height:1.45; }
</style>
</head>
<body>
<div class="ptitle">Controls</div>
<div class="sld"><div class="labrow"><span class="t">&Delta;P pressure drop (Pa)</span><span class="v" id="o_dp"></span></div>
  <input id="s_dp" type="range" min="10" max="2000" step="10" value="200" data-dec="0"></div>
<div class="sld"><div class="labrow"><span class="t">&mu; viscosity (mPa&middot;s)</span><span class="v" id="o_mu"></span></div>
  <input id="s_mu" type="range" min="0.5" max="50" step="0.5" value="1" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">L pipe length (m)</span><span class="v" id="o_len"></span></div>
  <input id="s_len" type="range" min="0.5" max="10" step="0.1" value="5" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">D pipe diameter (mm)</span><span class="v" id="o_dia"></span></div>
  <input id="s_dia" type="range" min="2" max="50" step="0.5" value="10" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">&rho; density (kg/m&sup3;)</span><span class="v" id="o_rho"></span></div>
  <input id="s_rho" type="range" min="500" max="2000" step="10" value="1000" data-dec="0"></div>
<div class="snote">Pressure drop, viscosity, length and diameter feed both tabs.
Density is only used for the Reynolds-number check in the second tab.</div>
<script>
var KEY = 'hagenpoiseuille_params_v1';
var IDS = ['dp','mu','len','dia','rho'];
var DEFS = { dp:200, mu:1, len:5, dia:10, rho:1000 };
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
    v = p[k];
    out[k] = (typeof v === 'number' && isFinite(v)) ? v : DEFS[k];
  }
  return out;
}
function curParams(){
  var p = {}, i;
  for (i = 0; i < IDS.length; i++) p[IDS[i]] = parseFloat(el('s_'+IDS[i]).value);
  return p;
}
function publish(){
  var ls = store();
  if (!ls) return;
  try { ls.setItem(KEY, JSON.stringify(curParams())); } catch (e) {}
}
(function init(){
  var p = readParams(), i;
  for (i = 0; i < IDS.length; i++){
    el('s_'+IDS[i]).value = p[IDS[i]];
    refreshSlider(IDS[i]);
  }
  publish();
})();
IDS.forEach(function(id){
  el('s_'+id).addEventListener('input', function(){ refreshSlider(id); publish(); });
});
</script>
</body>
</html>
"""

# ---------------- Tab 1 widget: force balance, v(r), tau(r), cross-section ----------------
TAB1_HTML = """<!DOCTYPE html>
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
  .vtitle{ font-size:16px; font-weight:600; margin:10px 0 4px; }
  .note{ font-size:13px; color:var(--sub); margin-top:6px; line-height:1.45; }
  .plotrow{ display:flex; gap:8px; }
  .plotrow > div{ flex:1 1 0; min-width:0; }
  .vecrow{ display:flex; gap:18px; margin-top:14px; align-items:flex-start; flex-wrap:wrap; }
  #xsCanvas{ width:560px; max-width:100%; height:auto; }
  #fbCanvas{ width:940px; max-width:100%; height:auto; }
  .vecside{ flex:1 1 240px; min-width:240px; }
  .mgrid{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:130px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
</style>
</head>
<body>
<div class="vtitle">Force balance on an imaginary cylinder of fluid</div>
<canvas id="fbCanvas" width="940" height="300"></canvas>
<div class="note">Red: pressure pushes the two end faces (net push = pressure drop &times;
end-face area). Green: the slower fluid outside drags backward on the curved surface
(drag = shear stress &times; curved area). Steady flow means no acceleration, so the two
balance. Drag the sliders and watch the arrow lengths rescale.</div>
<div class="vtitle">What the balance implies: velocity and shear stress across the pipe</div>
<div class="plotrow"><div id="plotV"></div><div id="plotT"></div></div>
<div class="note">Shear stress grows linearly from zero at the center to its maximum at the
wall; integrating it (with the no-slip condition at the wall) gives the parabolic velocity
profile. The dotted line marks the average velocity, exactly half the maximum.</div>
<div class="vecrow">
  <canvas id="xsCanvas" width="560" height="300"></canvas>
  <div class="vecside">
    <div class="vtitle">Pipe cross-section (side view)</div>
    <div class="note">Arrows point downstream with length proportional to local speed.
    The dashed curve through the arrow tips is the parabola v(r) itself: fastest at the
    center, zero where the fluid sticks to the wall.</div>
    <div class="vtitle">Readouts</div>
    <div class="mgrid" id="m1"></div>
  </div>
</div>
<script>
var KEY = 'hagenpoiseuille_params_v1';
var DEFS = { dp:200, mu:1, len:5, dia:10, rho:1000 };
function el(id){ return document.getElementById(id); }
function store(){ try { return window.localStorage; } catch (e) { return null; } }
function readParams(){
  var p = {}, ls = store(), raw = null;
  if (ls) { try { raw = ls.getItem(KEY); } catch (e) {} }
  if (raw) { try { p = JSON.parse(raw); } catch (e) { p = {}; } }
  var out = {}, k, v;
  for (k in DEFS){
    v = p[k];
    out[k] = (typeof v === 'number' && isFinite(v)) ? v : DEFS[k];
  }
  return out;
}
// PHYS-BEGIN
function hpPhys(dp, mu_mPas, Lm, Dmm, rho){
  var mu = mu_mPas/1000;            /* Pa s */
  var D = Dmm/1000, R = D/2;        /* m */
  var vmax = dp*R*R/(4*mu*Lm);      /* m/s, center */
  var vavg = vmax/2;                /* m/s */
  var Q = Math.PI*dp*Math.pow(D,4)/(128*mu*Lm); /* m^3/s */
  var tauw = (D/4)*(dp/Lm);         /* Pa, wall shear */
  var Re = rho*vavg*D/mu;
  return { vmax:vmax, vavg:vavg, Q:Q, tauw:tauw, Re:Re, R:R, D:D };
}
function hpVel(r, dp, mu_mPas, Lm, R){   /* r in m, v in m/s */
  var mu = mu_mPas/1000;
  return dp/(4*mu*Lm)*(R*R - r*r);
}
function hpTau(r, dp, Lm){              /* r in m, tau in Pa */
  return (dp/(2*Lm))*r;
}
// PHYS-END
function isDark(){ return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; }
function themed(title){
  var d = isDark(), grid = d ? '#2e3138' : '#e5e7eb';
  return {
    title: title, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: '"Source Sans Pro",sans-serif', color: d ? '#e8eaf0' : '#31333f' },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
    margin: { l: 60, r: 10, t: 40, b: 45 }
  };
}
function head(ctx, x, y, ang, color, hl){
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x - hl*Math.cos(ang-0.42), y - hl*Math.sin(ang-0.42));
  ctx.lineTo(x - hl*Math.cos(ang+0.42), y - hl*Math.sin(ang+0.42));
  ctx.closePath(); ctx.fill();
}
function arrow(ctx, x1, y1, x2, y2, color, lw){
  ctx.strokeStyle = color; ctx.lineWidth = lw || 2;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  var a = Math.atan2(y2-y1, x2-x1);
  head(ctx, x2, y2, a, color, 8);
}
function drawForceBalance(P, dark){
  var cv = el('fbCanvas'), ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  ctx.clearRect(0, 0, W, H);
  var wallC = dark ? '#cbd5e1' : '#0f172a';
  var txtC  = dark ? '#e8eaf0' : '#31333f';
  var subC  = dark ? '#9aa0ae' : '#6b7280';
  var redC  = '#d62728', grnC = '#2ca02c';
  var liqC  = dark ? 'rgba(56,189,248,0.30)' : 'rgba(2,132,199,0.22)';
  /* pipe walls */
  ctx.lineWidth = 4; ctx.strokeStyle = wallC;
  ctx.beginPath();
  ctx.moveTo(40, 60); ctx.lineTo(900, 60);
  ctx.moveTo(40, 240); ctx.lineTo(900, 240);
  ctx.stroke();
  ctx.fillStyle = subC; ctx.font = '13px "Source Sans Pro",sans-serif'; ctx.textAlign = 'center';
  ctx.fillText('pipe wall (fluid sticks here: zero speed)', 470, 42);
  /* imaginary fluid cylinder */
  ctx.fillStyle = liqC;
  ctx.fillRect(320, 125, 300, 50);
  ctx.strokeStyle = dark ? '#7dd3fc' : '#0284c7'; ctx.lineWidth = 1.5;
  ctx.strokeRect(320, 125, 300, 50);
  ctx.fillStyle = txtC; ctx.font = '600 13px "Source Sans Pro",sans-serif';
  ctx.fillText('imaginary fluid cylinder', 470, 143);
  ctx.font = '13px "Source Sans Pro",sans-serif';
  ctx.fillText('radius r, length L', 470, 162);
  /* pressure arrows: scale length by pressure drop relative to slider max */
  var plen = 40 + 90*(P.dp/2000);
  var ys = [132, 146, 160, 168];
  var i;
  for (i = 0; i < ys.length; i++){
    arrow(ctx, 320-plen-70, ys[i], 320-4, ys[i], redC, 2.2);   /* pushing in from left */
    arrow(ctx, 620+plen+70, ys[i], 620+4, ys[i], redC, 2.2);   /* lower pressure pushes back */
  }
  ctx.fillStyle = redC; ctx.font = '600 13px "Source Sans Pro",sans-serif';
  ctx.fillText('higher pressure pushing in', 200, 110);
  ctx.fillText('lower pressure pushing back', 740, 110);
  ctx.font = '13px "Source Sans Pro",sans-serif';
  ctx.fillText('net push = pressure drop x end-face area', 470, 205);
  /* shear arrows along curved surface (drag backward = upstream) */
  var xs = [380, 440, 500, 560];
  for (i = 0; i < xs.length; i++){
    arrow(ctx, xs[i]+34, 125, xs[i], 125, grnC, 2);   /* top surface */
    arrow(ctx, xs[i]+34, 175, xs[i], 175, grnC, 2);   /* bottom surface */
  }
  ctx.fillStyle = grnC; ctx.font = '600 13px "Source Sans Pro",sans-serif';
  ctx.fillText('viscous drag on the curved surface', 470, 262);
  ctx.font = '13px "Source Sans Pro",sans-serif';
  ctx.fillText('drag = shear stress x curved area', 470, 280);
  /* flow direction note */
  ctx.fillStyle = subC;
  ctx.fillText('flow direction', 855, 200);
  arrow(ctx, 830, 215, 880, 215, subC, 2);
}
function drawCrossSection(P, Hh, dark){
  var cv = el('xsCanvas'), ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  ctx.clearRect(0, 0, W, H);
  var wallC = dark ? '#cbd5e1' : '#0f172a';
  var txtC  = dark ? '#e8eaf0' : '#31333f';
  var subC  = dark ? '#9aa0ae' : '#6b7280';
  var R = Hh.R, vmax = Hh.vmax;
  var yTop = 40, yBot = H - 40, mid = (yTop+yBot)/2;
  var half = (yBot-yTop)/2;
  function Y(r){ return mid - (r/R)*half; }
  /* walls */
  ctx.lineWidth = 4; ctx.strokeStyle = wallC;
  ctx.beginPath();
  ctx.moveTo(30, yTop); ctx.lineTo(W-30, yTop);
  ctx.moveTo(30, yBot); ctx.lineTo(W-30, yBot);
  ctx.stroke();
  /* velocity arrows at 9 stations */
  var N = 9, i, r, v, alen, maxLen = W-220;
  var tips = [];
  for (i = 0; i < N; i++){
    r = -R + 2*R*i/(N-1);
    v = hpVel(r, P.dp, P.mu, P.len, R);
    alen = vmax > 0 ? Math.max(2, (v/vmax)*maxLen) : 2;
    arrow(ctx, 90, Y(r), 90+alen, Y(r), '#1f77b4', 2.2);
    tips.push([90+alen, Y(r)]);
  }
  /* dashed parabola through tips */
  ctx.strokeStyle = dark ? '#7dd3fc' : '#0284c7'; ctx.lineWidth = 1.8;
  ctx.setLineDash([6,5]);
  ctx.beginPath();
  for (i = 0; i <= 60; i++){
    r = -R + 2*R*i/60;
    v = hpVel(r, P.dp, P.mu, P.len, R);
    alen = vmax > 0 ? Math.max(2, (v/vmax)*maxLen) : 2;
    if (i) ctx.lineTo(90+alen, Y(r)); else ctx.moveTo(90+alen, Y(r));
  }
  ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = txtC; ctx.font = '13px "Source Sans Pro",sans-serif'; ctx.textAlign = 'left';
  ctx.fillText('wall: v = 0 (no-slip)', 92, yTop-12);
  ctx.fillText('wall: v = 0 (no-slip)', 92, yBot+22);
  ctx.fillText('center: v = max', 92, mid-10);
  ctx.fillStyle = subC; ctx.textAlign = 'center';
  ctx.fillText('flow direction', W-70, mid+4);
  arrow(ctx, W-95, mid+18, W-45, mid+18, subC, 2);
}
function draw(){
  var p = readParams();
  var Hh = hpPhys(p.dp, p.mu, p.len, p.dia, p.rho);
  var dark = isDark();
  drawForceBalance(p, dark);
  drawCrossSection(p, Hh, dark);
  var N = 160, i, r, rm = [], vv = [], tt = [];
  for (i = 0; i < N; i++){
    r = -Hh.R + 2*Hh.R*i/(N-1);
    rm.push(r*1000);
    vv.push(hpVel(r, p.dp, p.mu, p.len, Hh.R));
    tt.push(hpTau(r, p.dp, p.len));
  }
  var cfg = { displayModeBar: true, responsive: true };
  var wallC = dark ? '#8a8f98' : 'gray';
  var L1 = themed('Velocity profile v(r): a parabola');
  L1.xaxis.title = 'v (m/s)'; L1.yaxis.title = 'r (mm)'; L1.height = 340;
  L1.shapes = [{ type: 'line', x0: Hh.vavg, x1: Hh.vavg, y0: -p.dia/2, y1: p.dia/2,
                 line: { dash: 'dot', color: wallC, width: 1.5 } }];
  Plotly.react('plotV', [{ x: vv, y: rm, mode: 'lines',
    line: { width: 3, color: '#1f77b4' }, name: 'v(r)' }], L1, cfg);
  var L2 = themed('Shear-stress magnitude |\\u03c4(r)|: linear');
  L2.xaxis.title = '|\\u03c4| (Pa)'; L2.yaxis.title = 'r (mm)'; L2.height = 340;
  Plotly.react('plotT', [{ x: tt.map(Math.abs), y: rm, mode: 'lines',
    line: { width: 3, color: '#ff7f0e' }, name: '|\\u03c4(r)|' }], L2, cfg);
  el('m1').innerHTML =
    '<div class="mbox"><div class="k">v_max (center)</div><div class="n">' + Hh.vmax.toFixed(3) +
    ' m/s</div><div class="d">\\u0394P R\\u00b2 / 4\\u03bcL</div></div>' +
    '<div class="mbox"><div class="k">v_avg</div><div class="n">' + Hh.vavg.toFixed(3) +
    ' m/s</div><div class="d">= \\u00bd v_max</div></div>' +
    '<div class="mbox"><div class="k">\\u03c4_wall</div><div class="n">' + Hh.tauw.toFixed(2) +
    ' Pa</div><div class="d">= (D/4)(\\u0394P/L)</div></div>';
}
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
window.addEventListener('storage', function(e){ if (e.key === KEY) draw(); });
draw();
</script>
</body>
</html>
"""

# ---------------- Tab 2 widget: Q vs D (D^4), Q vs dP, Re banner ----------------
TAB2_HTML = """<!DOCTYPE html>
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
  .note{ font-size:13px; color:var(--sub); margin-top:6px; line-height:1.45; }
  .plotrow{ display:flex; gap:8px; }
  .plotrow > div{ flex:1 1 0; min-width:0; }
  .banner{ padding:10px 12px; border-radius:8px; font-weight:600; font-size:14px; margin:12px 0 4px; line-height:1.4; }
  .banner.ok{ background:#d1fae5; color:#065f46; }
  .banner.warn{ background:#fef3c7; color:#92400e; }
  .banner.bad{ background:#fee2e2; color:#991b1b; }
  @media (prefers-color-scheme: dark){
    .banner.ok{ background:rgba(16,185,129,.16); color:#6ee7b7; }
    .banner.warn{ background:rgba(245,158,11,.16); color:#fcd34d; }
    .banner.bad{ background:rgba(239,68,68,.16); color:#fca5a5; }
  }
  .mgrid{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:150px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
</style>
</head>
<body>
<div class="plotrow"><div id="plotD"></div><div id="plotP"></div></div>
<div class="note">Left: on log-log axes the Q-vs-diameter curve is a straight line of slope 4
(the gray dashed line is an exact D&#8308; reference through your point). The amber marker
doubles your diameter: it sits 16&times; higher. Right: flow rate grows linearly with
pressure drop; the marker is your current setting.</div>
<div class="banner" id="reBanner"></div>
<div class="mgrid" id="m2"></div>
<div class="note">Re = (density &times; average velocity &times; diameter) / viscosity.
Below &asymp;2100 the flow stays laminar and everything derived here applies; between
&asymp;2100 and &asymp;4000 it is transitional; above &asymp;4000 expect turbulence.</div>
<script>
var KEY = 'hagenpoiseuille_params_v1';
var DEFS = { dp:200, mu:1, len:5, dia:10, rho:1000 };
function el(id){ return document.getElementById(id); }
function store(){ try { return window.localStorage; } catch (e) { return null; } }
function readParams(){
  var p = {}, ls = store(), raw = null;
  if (ls) { try { raw = ls.getItem(KEY); } catch (e) {} }
  if (raw) { try { p = JSON.parse(raw); } catch (e) { p = {}; } }
  var out = {}, k, v;
  for (k in DEFS){
    v = p[k];
    out[k] = (typeof v === 'number' && isFinite(v)) ? v : DEFS[k];
  }
  return out;
}
// PHYS-BEGIN
function hpPhys(dp, mu_mPas, Lm, Dmm, rho){
  var mu = mu_mPas/1000;            /* Pa s */
  var D = Dmm/1000, R = D/2;        /* m */
  var vmax = dp*R*R/(4*mu*Lm);      /* m/s, center */
  var vavg = vmax/2;                /* m/s */
  var Q = Math.PI*dp*Math.pow(D,4)/(128*mu*Lm); /* m^3/s */
  var tauw = (D/4)*(dp/Lm);         /* Pa, wall shear */
  var Re = rho*vavg*D/mu;
  return { vmax:vmax, vavg:vavg, Q:Q, tauw:tauw, Re:Re, R:R, D:D };
}
// PHYS-END
function isDark(){ return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; }
function themed(title){
  var d = isDark(), grid = d ? '#2e3138' : '#e5e7eb';
  return {
    title: title, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: '"Source Sans Pro",sans-serif', color: d ? '#e8eaf0' : '#31333f' },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
    margin: { l: 60, r: 10, t: 40, b: 45 }
  };
}
function draw(){
  var p = readParams();
  var Hh = hpPhys(p.dp, p.mu, p.len, p.dia, p.rho);
  var Qcur = Hh.Q*1e6;   /* mL/s */
  var dark = isDark(), wallC = dark ? '#8a8f98' : 'gray';
  var cfg = { displayModeBar: true, responsive: true };
  /* Q vs D, log-log */
  var N = 120, i, Dmm, Ds = [], Qs = [], Qref = [];
  for (i = 0; i < N; i++){
    Dmm = 2*Math.pow(50/2, i/(N-1));
    Ds.push(Dmm);
    Qs.push(hpPhys(p.dp, p.mu, p.len, Dmm, p.rho).Q*1e6);
    Qref.push(Qcur*Math.pow(Dmm/p.dia, 4));
  }
  var L1 = themed('Flow rate vs diameter (log-log): slope 4');
  L1.xaxis.title = 'D (mm)'; L1.yaxis.title = 'Q (mL/s)'; L1.height = 400;
  L1.xaxis.type = 'log'; L1.yaxis.type = 'log';
  var d2 = Math.min(50, p.dia*2), Qd2 = Qcur*Math.pow(d2/p.dia, 4);
  Plotly.react('plotD', [
    { x: Ds, y: Qs, mode: 'lines', line: { width: 3, color: '#1f77b4' }, name: 'Q(D)' },
    { x: Ds, y: Qref, mode: 'lines', line: { width: 1.5, dash: 'dash', color: wallC }, name: 'exact D^4 slope' },
    { x: [p.dia], y: [Qcur], mode: 'markers', marker: { size: 10, color: '#1f77b4' }, name: 'your D' },
    { x: [d2], y: [Qd2], mode: 'markers', marker: { size: 10, color: '#f59e0b' }, name: 'doubled D' }
  ], L1, cfg);
  /* Q vs pressure drop, linear */
  var M = 120, dps = [], Qp = [], j, dpv;
  for (j = 0; j < M; j++){
    dpv = 10 + (2000-10)*j/(M-1);
    dps.push(dpv);
    Qp.push(hpPhys(dpv, p.mu, p.len, p.dia, p.rho).Q*1e6);
  }
  var L2 = themed('Flow rate vs pressure drop: linear');
  L2.xaxis.title = '\\u0394P (Pa)'; L2.yaxis.title = 'Q (mL/s)'; L2.height = 400;
  Plotly.react('plotP', [
    { x: dps, y: Qp, mode: 'lines', line: { width: 3, color: '#2ca02c' }, name: 'Q(\\u0394P)' },
    { x: [p.dp], y: [Qcur], mode: 'markers', marker: { size: 10, color: '#2ca02c' }, name: 'your \\u0394P' }
  ], L2, cfg);
  /* 16x check: doubling diameter (halve instead if it would leave the slider range) */
  var rD = p.dia*2 <= 50 ? p.dia*2 : p.dia/2;
  var ratio = hpPhys(p.dp, p.mu, p.len, rD, p.rho).Q /
              hpPhys(p.dp, p.mu, p.len, p.dia, p.rho).Q;
  if (rD < p.dia) ratio = 1/ratio;
  /* readouts */
  var Qlmin = Hh.Q*60000;
  el('m2').innerHTML =
    '<div class="mbox"><div class="k">Q volumetric flow rate</div><div class="n">' + Qcur.toPrecision(4) +
    ' mL/s</div><div class="d">' + Qlmin.toPrecision(4) + ' L/min \\u00b7 \\u03c0\\u0394PD\\u2074/128\\u03bcL</div></div>' +
    '<div class="mbox"><div class="k">v_avg mean velocity</div><div class="n">' + Hh.vavg.toFixed(3) +
    ' m/s</div><div class="d">= Q / area</div></div>' +
    '<div class="mbox"><div class="k">\\u03c4_wall shear stress</div><div class="n">' + Hh.tauw.toFixed(2) +
    ' Pa</div><div class="d">= (D/4)(\\u0394P/L)</div></div>' +
    '<div class="mbox"><div class="k">Re</div><div class="n">' + Hh.Re.toPrecision(4) +
    '</div><div class="d">= \\u03c1 v_avg D / \\u03bc</div></div>' +
    '<div class="mbox"><div class="k">doubling-D check</div><div class="n">' + ratio.toFixed(2) +
    '\\u00d7</div><div class="d">expect exactly 16\\u00d7</div></div>';
  var bn = el('reBanner');
  if (Hh.Re < 2100){
    bn.className = 'banner ok';
    bn.textContent = 'LAMINAR (Re = ' + Hh.Re.toPrecision(4) + ' < 2100) \\u2014 smooth layers, ' +
      'the parabolic profile and the D\\u2074 law apply as drawn.';
  } else if (Hh.Re < 4000){
    bn.className = 'banner warn';
    bn.textContent = 'TRANSITIONAL (Re = ' + Hh.Re.toPrecision(4) + ') \\u2014 between laminar and ' +
      'turbulent; the laminar derivation is only approximate here.';
  } else {
    bn.className = 'banner bad';
    bn.textContent = 'TURBULENT likely (Re = ' + Hh.Re.toPrecision(4) + ' > 4000) \\u2014 eddies mix ' +
      'the layers, so the laminar derivation no longer describes the flow. Raise viscosity or ' +
      'lower the pressure drop / diameter to return to laminar.';
  }
}
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
window.addEventListener('storage', function(e){ if (e.key === KEY) draw(); });
draw();
</script>
</body>
</html>
"""

# ---------------- Page layout ----------------
with st.sidebar:
    components.html(SIDEBAR_HTML, height=430, scrolling=False)

tab1, tab2 = st.tabs(["Derivation from first principles", "The Hagen\u2013Poiseuille law"])

with tab1:
    st.header("Deriving laminar pipe flow from a force balance")
    st.markdown(
        "_A straight horizontal pipe, a steady push of pressure, and one imaginary cylinder "
        "of fluid. No Navier\u2013Stokes: just push-versus-drag, Newton's law of viscosity, "
        "and one integration. Drag the sidebar sliders; every graphic below updates live "
        "in your browser._"
    )

    st.subheader("1. The setup and the assumptions")
    st.markdown(
        "- **The pipe**: straight, circular, horizontal, of fixed diameter and length, "
        "completely full of liquid.\n"
        "- **Steady**: nothing changes with time; the flow pattern is the same at every "
        "cross-section along the pipe (fully developed).\n"
        "- **Incompressible**: the fluid's density is constant.\n"
        "- **Newtonian**: the fluid's shear stress is proportional to how fast neighboring "
        "layers slide past each other, with a constant viscosity.\n"
        "- **Laminar**: the fluid moves in smooth concentric layers (laminae) parallel to "
        "the pipe axis, with no swirling or mixing between layers.\n"
        "- **No-slip at the wall**: the fluid touching the pipe wall sticks to it, so its "
        "speed there is zero.\n"
        "- **Horizontal**: gravity has nothing to push along the flow direction, so the "
        "pressure drop is the only thing driving the fluid."
    )

    st.subheader("2. Carve out an imaginary cylinder of fluid")
    st.markdown(
        "Picture a cylinder of fluid centered on the pipe axis, with radius **r** (any value "
        "from zero up to the pipe's own radius) and length **L** (the full pipe length). It "
        "is not a real object \u2014 just a chunk of the flowing liquid we choose to analyze. "
        "Two kinds of force act on it, shown in the diagram below: pressure pushing on its "
        "two flat end faces, and viscous drag pulling back on its curved side surface."
    )
    st.markdown("**Try it live** \u2014 the force-balance diagram rescales as you drag the sliders:")

    st.subheader("3. Push versus drag: the force balance")
    st.markdown(
        "**The push.** Pressure at the pipe inlet is higher than at the outlet. Call the "
        "difference the **pressure drop** (a positive number: inlet pressure minus outlet "
        "pressure). It shoves the left end face downstream and the right end face upstream; "
        "the net shove is pressure drop \u00d7 the end-face area:"
    )
    st.latex(r"F_{\text{pressure}} = \Delta P\,\pi r^2")
    st.markdown(
        "**The drag.** The fluid just outside our cylinder moves more slowly (it is closer "
        "to the stationary wall), so it drags the cylinder's curved surface backward. That "
        "drag is the **shear stress** (drag force per unit area, call it \u03c4) times the "
        "curved surface area:"
    )
    st.latex(r"F_{\text{shear}} = \tau(r)\,2\pi r L")
    st.markdown(
        "**The balance.** The flow is steady, so our cylinder does not accelerate: total "
        "force zero, push equals drag:"
    )
    st.latex(r"\Delta P\,\pi r^2 = \tau(r)\,2\pi r L")

    st.subheader("4. What the balance says about the shear stress")
    st.markdown(
        "Cancel one factor of \u03c0r from both sides and solve for the shear stress:"
    )
    st.latex(r"\boxed{\tau(r) = \frac{\Delta P}{2L}\,r}")
    st.markdown(
        "The shear stress grows **linearly** with radius: zero at the center (nothing to "
        "drag against symmetrically) and largest at the wall. Conceptually: a fatter cylinder "
        "feels more pressure push (which grows with r\u00b2, the end-face area) but also offers "
        "more curved surface to be dragged (which grows with r); the ratio leaves one power "
        "of r."
    )

    st.subheader("5. Newton's viscosity law turns stress into a velocity slope")
    st.markdown(
        "For a Newtonian fluid, shear stress is viscosity times the rate at which the fluid "
        "speed changes across neighboring layers. Speed is highest at the center and falls "
        "toward the wall, so the slope dv/dr is negative and the stress is:"
    )
    st.latex(r"\tau(r) = -\mu\,\frac{dv}{dr}")
    st.markdown("Equate this with the linear stress from the force balance:")
    st.latex(r"-\mu\,\frac{dv}{dr} = \frac{\Delta P}{2L}\,r"
             r"\;\;\Longrightarrow\;\;"
             r"\frac{dv}{dr} = -\frac{\Delta P}{2\mu L}\,r")

    st.subheader("6. Integrate and apply no-slip at the wall")
    st.markdown("Integrate with respect to radius:")
    st.latex(r"v(r) = -\frac{\Delta P}{4\mu L}\,r^2 + C")
    st.markdown(
        "The constant C comes from the no-slip condition: at the pipe wall (r = pipe radius R) "
        "the speed is zero, so C = (\u0394P/4\u03bcL)R\u00b2:"
    )
    st.latex(r"\boxed{v(r) = \frac{\Delta P}{4\mu L}\,\left(R^2 - r^2\right)}")
    st.markdown(
        "A **parabola**: maximum speed at the center, zero at the wall, smooth in between. "
        "The center speed is v_max = \u0394PR\u00b2/4\u03bcL, and averaging the parabola over the "
        "circular cross-section gives v_avg = v_max/2 (the dotted line in the plot)."
    )

    st.subheader("7. Every variable, in words (not letters)")
    st.markdown(
        "- **Volumetric flow rate**: the volume of fluid crossing any cross-section of the "
        "pipe per unit time (cubic meters per second).\n"
        "- **Pressure drop**: how much higher the pressure is at the pipe inlet than at the "
        "outlet (pascals); the net push driving the flow.\n"
        "- **Viscosity**: the fluid's internal friction \u2014 its resistance to having "
        "neighboring layers slide past each other, its \u201ct thickness\u201d "
        "(pascal-seconds; the sliders use millipascal-seconds).\n"
        "- **Pipe length**: the distance the fluid travels from inlet to outlet (meters).\n"
        "- **Pipe diameter**: the width of the pipe's circular opening (millimeters on the "
        "sliders, converted to meters inside the formulas).\n"
        "- **Fluid density**: mass per unit volume (kilograms per cubic meter); not needed "
        "for the flow rate itself, only for checking whether the flow is laminar.\n"
        "- **Average velocity**: volumetric flow rate divided by the pipe's cross-sectional "
        "area (meters per second).\n"
        "- **Wall shear stress**: the drag force per unit area that the wall exerts on the "
        "fluid (pascals); largest stress in the whole pipe."
    )

    st.subheader("Try it live")
    st.markdown(
        "The parabola, the linear shear-stress profile, and the cross-section arrows all "
        "morph as you drag the sidebar sliders. Raise the viscosity and watch the whole "
        "parabola sink; raise the pressure drop and watch it grow."
    )
    components.html(TAB1_HTML, height=1180, scrolling=False)

with tab2:
    st.header("From the parabola to the Hagen\u2013Poiseuille law")
    st.markdown(
        "_The velocity profile is known; the flow rate is just the profile added up over the "
        "cross-section. Drag the sidebar sliders \u2014 the scaling plots, the readouts, and "
        "the regime banner all update live._"
    )

    st.subheader("1. Adding up the flow: integrate the parabola")
    st.markdown(
        "Slice the cross-section into thin rings. A ring at radius r has area "
        "dA = 2\u03c0r\u00b7dr and carries fluid at speed v(r), so its contribution to the "
        "volumetric flow rate is v(r)\u00b7dA. Add up all rings from the center to the wall:"
    )
    st.latex(r"Q = \int_0^R v(r)\,2\pi r\,dr"
             r"= \frac{\Delta P\,\pi}{2\mu L}\int_0^R \left(R^2 - r^2\right) r\,dr")
    st.markdown("The integral evaluates to R\u2074/4:")
    st.latex(r"Q = \frac{\pi\,\Delta P\,R^4}{8\,\mu L}")
    st.markdown(
        "Writing it with the pipe **diameter** (D = 2R, so R\u2074 = D\u2074/16) gives the "
        "form most textbooks quote:"
    )
    st.latex(r"\boxed{Q = \frac{\pi\,\Delta P\,D^4}{128\,\mu L}}")
    st.markdown(
        "**Reading it in words:** the volumetric flow rate equals \u03c0 times the pressure "
        "drop times the diameter-to-the-fourth-power, divided by 128 times the viscosity "
        "times the pipe length. Double the pressure drop \u2192 double the flow. Double the "
        "viscosity or the length \u2192 half the flow. And the diameter? Read on."
    )

    st.subheader("2. Why the diameter appears to the fourth power")
    st.markdown(
        "Doubling the diameter does **two** things at once. First, the pipe's cross-sectional "
        "area grows by 2\u00b2 = **4** (area goes as diameter squared). Second, the fluid has "
        "twice as far to travel from the wall to the center, so viscous drag constrains it "
        "less and the speeds everywhere grow by 2\u00b2 = **4** as well (speed goes as radius "
        "squared, from the parabola). Flow rate is area \u00d7 average speed, so it grows by "
        "4 \u00d7 4 = **16** = 2\u2074. The live \u201cdoubling-D check\u201d readout verifies "
        "this 16\u00d7 factor for your exact slider settings."
    )

    st.subheader("Try it live")
    st.markdown(
        "Left: on log-log axes the flow-rate-versus-diameter curve is a straight line of "
        "slope 4, with an exact D\u2074 reference through your point and an amber marker at "
        "double your diameter sitting 16\u00d7 higher. Right: flow rate versus pressure drop "
        "is a straight line through the origin."
    )
    components.html(TAB2_HTML, height=880, scrolling=False)

    st.subheader("3. Reading the flow regime")
    st.markdown(
        "Everything above assumed laminar flow \u2014 smooth concentric layers. Whether that "
        "holds is decided by the **Reynolds number**, the ratio of inertial to viscous "
        "effects:"
    )
    st.latex(r"\text{Re} = \frac{\rho\,v_{\text{avg}}\,D}{\mu}")
    st.markdown(
        "In words: density times average velocity times diameter, divided by viscosity. "
        "Below about 2100 the layers stay smooth and the derivation applies; around "
        "2100\u20134000 the flow is transitional; far above, eddies mix the layers and the "
        "parabolic profile no longer describes reality. The banner above the readouts tells "
        "you where your settings land."
    )

    st.subheader("The whole story, in one line")
    st.markdown(
        "**Pressure push balances viscous drag on every imaginary fluid cylinder \u2192 shear "
        "stress grows linearly with radius \u2192 Newton's viscosity law turns that into a "
        "velocity slope \u2192 no-slip integration gives a parabola \u2192 adding up the "
        "parabola over the cross-section gives Q \u221d \u0394PD\u2074/\u03bcL.**"
    )
