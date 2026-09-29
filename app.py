"""Falling-film flow visualizer: velocity profile and flow-rate/thickness relation
for a steady laminar liquid film flowing down a vertical wall (Nusselt film flow).

Derivations are done by shell (force) balance - no Navier-Stokes formalism.
All graphics run as JavaScript in the browser at 60 fps: the real Streamlit
sidebar publishes slider values through localStorage, and each tab's widget
redraws on the storage event. No server round-trip while dragging.
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Falling Film Flow", layout="wide")

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
<div class="sld"><div class="labrow"><span class="t">&delta; film thickness (mm)</span><span class="v" id="o_delta"></span></div>
  <input id="s_delta" type="range" min="0.2" max="3" step="0.05" value="1" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">&mu; viscosity (mPa&middot;s)</span><span class="v" id="o_mu"></span></div>
  <input id="s_mu" type="range" min="1" max="200" step="1" value="10" data-dec="0"></div>
<div class="sld"><div class="labrow"><span class="t">&rho; density (kg/m&sup3;)</span><span class="v" id="o_rho"></span></div>
  <input id="s_rho" type="range" min="700" max="1300" step="10" value="1000" data-dec="0"></div>
<div class="sld"><div class="labrow"><span class="t">g gravity (m/s&sup2;)</span><span class="v" id="o_grav"></span></div>
  <input id="s_grav" type="range" min="1.6" max="24.8" step="0.1" value="9.81" data-dec="2"></div>
<div class="sld"><div class="labrow"><span class="t">q flow rate (cm&sup2;/s)</span><span class="v" id="o_qrate"></span></div>
  <input id="s_qrate" type="range" min="0.1" max="30" step="0.1" value="3.27" data-dec="2"></div>
<div class="snote">&delta;, &mu;, &rho;, g feed both tabs. q is the target flow rate used in the Flow-rate tab (per unit width of wall).</div>
<script>
var KEY = 'fallingfilm_params_v1';
var IDS = ['delta','mu','rho','grav','qrate'];
var DEFS = { delta:1, mu:10, rho:1000, grav:9.81, qrate:3.27 };
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

# ---------------- Tab 1 widget: velocity profile v(y), shear stress, film diagram ----------------
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
  .plotrow{ display:flex; gap:8px; }
  .plotrow > div{ flex:1 1 0; min-width:0; }
  .note{ font-size:13px; color:var(--sub); margin-top:6px; line-height:1.45; }
  .vecrow{ display:flex; gap:18px; margin-top:14px; align-items:flex-start; flex-wrap:wrap; }
  #filmCanvas{ width:560px; max-width:100%; height:auto; }
  .vecside{ flex:1 1 240px; min-width:240px; }
  .vtitle{ font-size:16px; font-weight:600; margin-bottom:4px; }
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
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:130px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
  .sec{ font-size:14px; font-weight:600; margin:14px 0 2px; }
</style>
</head>
<body>
<div class="plotrow"><div id="plotV"></div><div id="plotT"></div></div>
<div class="note">The dotted line marks the average velocity v&#772; = &#8532;v<sub>max</sub>.
Shear stress is shown as a magnitude; its sign says the wall drags the film upward.</div>
<div class="vecrow">
  <canvas id="filmCanvas" width="560" height="300"></canvas>
  <div class="vecside">
    <div class="vtitle">Film cross-section (side view)</div>
    <div class="note">Arrows point down the wall with length proportional to local speed.
    The dashed curve through the arrow tips is the parabola v(y) itself.</div>
    <div class="sec">Readouts</div>
    <div class="mgrid" id="m1"></div>
    <div class="sec">Flow regime</div>
    <div class="banner" id="reBanner"></div>
    <div class="note">Re = 4&rho;q/&mu; with q from your &delta;. Smooth laminar below &asymp;20,
    wavy laminar beyond; the derivation assumes laminar flow.</div>
  </div>
</div>
<script>
var KEY = 'fallingfilm_params_v1';
var DEFS = { delta:1, mu:10, rho:1000, grav:9.81, qrate:3.27 };
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
  var dm = p.delta / 1000, mu = p.mu / 1000, rho = p.rho, g = p.grav;
  var K = rho * g / mu;
  var vmax = K * dm * dm / 2, vavg = K * dm * dm / 3, tauw = rho * g * dm;
  var qSI = rho * g * dm * dm * dm / (3 * mu);
  var Re = 4 * rho * qSI / mu;
  var N = 220, ym = [], vv = [], tt = [], i, y;
  for (i = 0; i < N; i++){
    y = dm * i / (N - 1);
    ym.push(y * 1000);
    vv.push(K * (dm * y - y * y / 2));
    tt.push(rho * g * (dm - y));
  }
  var dark = isDark(), wallC = dark ? '#8a8f98' : 'gray';
  var cfg = { displayModeBar: true, responsive: true };
  var L1 = themed('Velocity profile across the film');
  L1.xaxis.title = 'v_x (m/s)'; L1.yaxis.title = 'y (mm)'; L1.height = 330;
  L1.shapes = [{ type: 'line', x0: vavg, x1: vavg, y0: 0, y1: p.delta,
                 line: { dash: 'dot', color: wallC, width: 1.5 } }];
  Plotly.react('plotV', [{ x: vv, y: ym, mode: 'lines',
    line: { width: 3, color: '#1f77b4' }, name: 'v_x(y)' }], L1, cfg);
  var L2 = themed('Shear-stress magnitude across the film');
  L2.xaxis.title = '|tau| (Pa)'; L2.yaxis.title = 'y (mm)'; L2.height = 330;
  Plotly.react('plotT', [{ x: tt, y: ym, mode: 'lines',
    line: { width: 3, color: '#ff7f0e' }, name: '|tau(y)|' }], L2, cfg);
  drawFilm(dark);
  el('m1').innerHTML =
    '<div class="mbox"><div class="k">v_max (surface)</div><div class="n">' + vmax.toFixed(3) +
    ' m/s</div><div class="d">&rho;g&delta;&sup2;/2&mu;</div></div>' +
    '<div class="mbox"><div class="k">v_avg</div><div class="n">' + vavg.toFixed(3) +
    ' m/s</div><div class="d">= &#8532; v_max</div></div>' +
    '<div class="mbox"><div class="k">&tau;_wall</div><div class="n">' + tauw.toFixed(2) +
    ' Pa</div><div class="d">= &rho;g&delta; (whole film&#8217;s weight)</div></div>' +
    '<div class="mbox"><div class="k">Re</div><div class="n">' + Re.toPrecision(3) +
    '</div><div class="d">= 4&rho;q/&mu;</div></div>';
  var bn = el('reBanner');
  if (Re < 20){
    bn.className = 'banner ok';
    bn.textContent = 'SMOOTH LAMINAR \u2014 the parabolic profile applies as drawn.';
  } else if (Re < 1500){
    bn.className = 'banner warn';
    bn.textContent = 'WAVY LAMINAR \u2014 the surface ripples; the profile is still about right on average.';
  } else {
    bn.className = 'banner bad';
    bn.textContent = 'TURBULENT likely \u2014 the laminar derivation no longer describes the flow.';
  }
}
function drawFilm(dark){
  var cv = el('filmCanvas'), ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
  ctx.clearRect(0, 0, W, H);
  var wallX = 80, top = 46, FW = 300, surfX = wallX + FW;
  ctx.lineWidth = 6; ctx.strokeStyle = dark ? '#cbd5e1' : '#0f172a';
  ctx.beginPath(); ctx.moveTo(wallX, 20); ctx.lineTo(wallX, H - 20); ctx.stroke();
  ctx.fillStyle = dark ? 'rgba(56,189,248,0.08)' : 'rgba(2,132,199,0.07)';
  ctx.fillRect(wallX, 20, FW, H - 40);
  ctx.lineWidth = 2; ctx.setLineDash([6, 5]);
  ctx.strokeStyle = dark ? '#7dd3fc' : '#0284c7';
  ctx.beginPath(); ctx.moveTo(surfX, 20); ctx.lineTo(surfX, H - 20); ctx.stroke();
  ctx.setLineDash([]);
  var n = 14, i, frac, px, len, tips = [];
  var Lmax = H - 20 - top - 14;
  for (i = 0; i < n; i++){
    frac = i / (n - 1); px = wallX + frac * FW;
    var vf = 2 * frac - frac * frac;
    len = Math.max(2, Lmax * vf);
    var y1 = top, y2 = top + len;
    ctx.strokeStyle = '#1f77b4'; ctx.lineWidth = 2.2;
    ctx.beginPath(); ctx.moveTo(px, y1); ctx.lineTo(px, y2); ctx.stroke();
    var hl = 7;
    ctx.beginPath();
    ctx.moveTo(px, y2); ctx.lineTo(px - hl * 0.45, y2 - hl);
    ctx.moveTo(px, y2); ctx.lineTo(px + hl * 0.45, y2 - hl);
    ctx.stroke();
    tips.push([px, y2]);
  }
  ctx.strokeStyle = dark ? 'rgba(125,211,252,0.85)' : 'rgba(2,132,199,0.75)';
  ctx.lineWidth = 1.5; ctx.setLineDash([4, 3]);
  ctx.beginPath();
  tips.forEach(function(t, k){ if (k) ctx.lineTo(t[0], t[1]); else ctx.moveTo(t[0], t[1]); });
  ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = dark ? '#e8eaf0' : '#31333f';
  ctx.font = '13px "Source Sans Pro",sans-serif';
  ctx.fillText('wall (no slip)', 4, 24);
  ctx.fillText('free surface (no shear)', surfX + 8, 24);
  ctx.strokeStyle = dark ? '#94a3b8' : '#64748b'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(34, 60); ctx.lineTo(34, 112); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(34, 112); ctx.lineTo(29, 103);
  ctx.moveTo(34, 112); ctx.lineTo(39, 103); ctx.stroke();
  ctx.fillText('g', 28, 132);
}
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
window.addEventListener('storage', function(e){ if (e.key === KEY) draw(); });
draw();
</script>
</body>
</html>
"""

# ---------------- Tab 2 widget: q vs delta cubic, consistency check ----------------
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
  .banner{ padding:10px 12px; border-radius:8px; font-weight:600; font-size:14px; margin:12px 0 4px; line-height:1.4; }
  .banner.ok{ background:#d1fae5; color:#065f46; }
  .banner.warn{ background:#fef3c7; color:#92400e; }
  @media (prefers-color-scheme: dark){
    .banner.ok{ background:rgba(16,185,129,.16); color:#6ee7b7; }
    .banner.warn{ background:rgba(245,158,11,.16); color:#fcd34d; }
  }
  .mgrid{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:150px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
</style>
</head>
<body>
<div id="plotQ"></div>
<div class="banner" id="consBanner"></div>
<div class="mgrid" id="m2"></div>
<div class="note">Red dot: the flow rate your &delta; produces. Green diamond: the thickness &delta;*
your target q demands, &delta;* = (3&mu;q/&rho;g)<sup>1/3</sup>. One film cannot have
both unless the two markers coincide &mdash; that is the cubic constraint, live.</div>
<script>
var KEY = 'fallingfilm_params_v1';
var DEFS = { delta:1, mu:10, rho:1000, grav:9.81, qrate:3.27 };
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
  var mu = p.mu / 1000, rho = p.rho, g = p.grav;
  var qS = p.qrate / 1e4;
  var dstar = Math.cbrt(3 * mu * qS / (rho * g)) * 1000;
  var dm = p.delta / 1000;
  var qAtDelta = rho * g * dm * dm * dm / (3 * mu) * 1e4;
  var N = 160, xs = [], ys = [], i, d, dmm;
  for (i = 0; i < N; i++){
    d = 0.1 + (6 - 0.1) * i / (N - 1); dmm = d / 1000;
    xs.push(d); ys.push(rho * g * dmm * dmm * dmm / (3 * mu) * 1e4);
  }
  var dark = isDark(), wallC = dark ? '#8a8f98' : 'gray';
  var L = themed('Flow rate vs film thickness');
  L.xaxis.title = 'delta (mm)'; L.yaxis.title = 'q (cm^2/s)'; L.height = 380;
  L.shapes = [
    { type: 'line', x0: p.delta, x1: p.delta, y0: 0, y1: 1, yref: 'paper',
      line: { dash: 'dash', color: wallC, width: 1.5 } },
    { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: p.qrate, y1: p.qrate,
      line: { dash: 'dash', color: wallC, width: 1.5 } }
  ];
  var dstarC = Math.max(0.1, Math.min(6, dstar));
  Plotly.react('plotQ', [
    { x: xs, y: ys, mode: 'lines', line: { width: 3, color: '#1f77b4' }, name: 'q = rho*g*delta^3/(3*mu)' },
    { x: [p.delta], y: [qAtDelta], mode: 'markers',
      marker: { size: 11, color: '#ff4b4b' }, name: 'your delta -> q(delta)' },
    { x: [dstarC], y: [p.qrate], mode: 'markers',
      marker: { size: 11, color: '#2ca02c', symbol: 'diamond' }, name: 'your q -> delta*' }
  ], L, { displayModeBar: true, responsive: true });
  var rel = Math.abs(qAtDelta - p.qrate) / Math.max(qAtDelta, p.qrate, 1e-9);
  var bn = el('consBanner');
  if (rel < 0.03){
    bn.className = 'banner ok';
    bn.textContent = 'CONSISTENT \u2014 your \u03b4 and q satisfy q = \u03c1g\u03b4\u00b3/3\u03bc.';
  } else {
    bn.className = 'banner warn';
    bn.textContent = 'MISMATCH \u2014 one film cannot have both: your \u03b4 gives q = ' +
      qAtDelta.toFixed(2) + ' cm\u00b2/s, while your q needs \u03b4* = ' + dstar.toFixed(2) + ' mm.';
  }
  el('m2').innerHTML =
    '<div class="mbox"><div class="k">q from your &delta;</div><div class="n">' + qAtDelta.toFixed(2) +
    ' cm&sup2;/s</div><div class="d">&rho;g&delta;&sup3;/3&mu;</div></div>' +
    '<div class="mbox"><div class="k">&delta;* for your q</div><div class="n">' + dstar.toFixed(2) +
    ' mm</div><div class="d">(3&mu;q/&rho;g)<sup>1/3</sup>' +
    (dstar > 6 ? ' \u2014 off the plot&#8217;s right edge' : '') + '</div></div>' +
    '<div class="mbox"><div class="k">v_avg = q/&delta;</div><div class="n">' +
    (qAtDelta / 1e4 / dm).toFixed(3) + ' m/s</div><div class="d">= &#8532; v_max</div></div>' +
    '<div class="mbox"><div class="k">The 8&times; rule</div><div class="n">q(2&delta;) = ' +
    (8 * qAtDelta).toFixed(2) + '</div><div class="d">8 &times; q(&delta;) = 8 &times; ' +
    qAtDelta.toFixed(2) + ' cm&sup2;/s</div></div>';
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
    components.html(SIDEBAR_HTML, height=470, scrolling=False)

tab1, tab2 = st.tabs(["Velocity profile v(y)", "Flow rate vs film thickness"])

with tab1:
    st.header("Where the parabola comes from: a force balance on a fluid slab")
    st.markdown(
        "_No Navier–Stokes equations. We balance forces on a thin slice of fluid, "
        "use Newton's law of viscosity, and integrate. Drag the sidebar sliders — "
        "every graphic below updates live in your browser._"
    )

    st.subheader("1. The setup")
    st.markdown(
        "A liquid film of thickness δ flows down a vertical wall. Measure **y** outward "
        "from the wall (y = 0 at the wall, y = δ at the free surface) and **x** downward, "
        "with the flow. Assumptions: steady flow, fully developed (nothing changes with x, "
        "so v = v_x(y) only), laminar, incompressible Newtonian liquid. The air above can't "
        "tug the surface, and the pressure is atmospheric everywhere, so there is no "
        "pressure gradient pushing the fluid — gravity does all the driving."
    )

    st.subheader("2. Balance the forces on a thin slab")
    st.markdown(
        "Cut out the slab between y and y + Δy (width W into the page, length L down the wall). "
        "In steady flow it doesn't accelerate, so the x-direction forces sum to zero: its "
        "**weight** pulling down, the **shear force** on its wall-side face, and the shear "
        "force on its air-side face:"
    )
    st.latex(r"0 = \tau_{yx}(y)\,WL - \tau_{yx}(y+\Delta y)\,WL + \rho g\,WL\,\Delta y")
    st.markdown("Divide by WLΔy and let Δy → 0:")
    st.latex(r"\frac{d\tau_{yx}}{dy} = \rho g")
    st.markdown(
        "In words: moving outward through the film, the shear stress grows at exactly the rate "
        "needed to hold up each new slice of fluid weight. Integrate:"
    )
    st.latex(r"\tau_{yx}(y) = \rho g\,y + C")

    st.subheader("3. The free surface sets the constant")
    st.markdown(
        "Air can't pull on the liquid, so the shear stress vanishes at the free surface:"
    )
    st.latex(r"\tau_{yx}(\delta) = 0 \;\;\Longrightarrow\;\; \boxed{\tau_{yx}(y) = -\rho g\,(\delta - y)}")
    st.markdown(
        "**Read it physically:** |τ(y)| = ρg(δ − y) is exactly the weight per unit area of all "
        "the fluid *above* the level y. At the wall (y = 0) the shear τ_w = ρgδ carries the "
        "entire film's weight; at the surface there is nothing above, so the shear is zero. "
        "The linear stress profile is just 'cumulative weight'."
    )

    st.subheader("4. Newton's law turns stress into a velocity gradient")
    st.latex(r"\tau_{yx} = -\mu\,\frac{dv_x}{dy} \;\;\Longrightarrow\;\; "
             r"\frac{dv_x}{dy} = \frac{\rho g}{\mu}\,(\delta - y)")
    st.markdown(
        "The velocity gradient is steepest at the wall and flattens to zero slope at the free "
        "surface — the fastest fluid sits at the top, arriving there with zero gradient because "
        "nothing tugs it."
    )

    st.subheader("5. Integrate, and no-slip the wall")
    st.markdown("Integrate once more, and kill the constant with no-slip (v = 0 at y = 0):")
    st.latex(r"\boxed{v_x(y) = \frac{\rho g}{\mu}\left(\delta y - \frac{y^2}{2}\right)}")
    st.markdown(
        f"Maximum at the free surface: v_max = ρgδ²/2μ. The average over the film is "
        "v̄ = ρgδ²/3μ = ⅔v_max — the ⅔ is just the average value of the parabola shape."
    )

    st.subheader("6. Sanity checks (purely physical)")
    st.markdown(
        "- **δ → 0:** everything vanishes — no film, no flow. ✓\n"
        "- **Global balance:** wall shear τ_w = ρgδ equals the whole film's weight per unit "
        "area — the wall holds up everything. ✓\n"
        "- **Units:** [ρgδ²/μ] = m/s. ✓\n"
        "- **Shape:** zero slope at the surface, steepest at the wall — exactly what the "
        "stress picture demanded. ✓"
    )

    st.subheader("Try it live")
    st.markdown(
        "Drag any sidebar slider: the profile, the stress curve, and the cross-section arrows "
        "all morph continuously. Watch what happens to the parabola when you raise the viscosity."
    )
    components.html(TAB1_HTML, height=880, scrolling=False)

with tab2:
    st.header("From the profile to the flow rate: why thickness wins cubically")
    st.markdown(
        "_We integrate the parabola from the first tab. Drag the sidebar sliders — the cubic "
        "curve, your operating point, and the consistency check all update live._"
    )

    st.subheader("1. Add up the ribbons of fluid")
    st.markdown(
        "The volume flow rate per unit width of wall, q, is the profile stacked up across "
        "the film — each ribbon v_x(y)·dy contributes its share:"
    )
    st.latex(r"q = \int_0^{\delta} v_x(y)\,dy \qquad \text{(per unit width)}")

    st.subheader("2. Integrate the parabola")
    st.latex(r"q = \frac{\rho g}{\mu}\left(\frac{\delta^3}{2} - \frac{\delta^3}{6}\right)"
             r" = \boxed{q = \frac{\rho g\,\delta^3}{3\mu}}")

    st.subheader("3. Why cubic? Thickness wins twice")
    st.markdown(
        "Double the thickness δ → 2δ and two things happen at once: there is **twice the "
        "cross-section** carrying fluid, and **every layer moves 4× faster** (because v ∝ δ²). "
        "2 × 4 = 8. That compounding — more area times more speed — is the whole cubic."
    )

    st.subheader("4. Average velocity, for free")
    st.latex(r"\bar{v} = \frac{q}{\delta} = \frac{\rho g\,\delta^2}{3\mu} = \tfrac{2}{3}\,v_{\max}")

    st.subheader("5. Flip it: the design equation")
    st.markdown(
        "Solve the cubic for δ. Now you specify the flow rate you *want*, and it tells you "
        "the thickness you'll *get*:"
    )
    st.latex(r"\boxed{\delta = \left(\frac{3\mu q}{\rho g}\right)^{1/3}}")
    st.markdown(
        "Cube roots are forgiving: pushing **8× more flow** only **doubles** the thickness. "
        "Try it in the widget — set a target q in the sidebar and read off the δ* it demands."
    )

    st.subheader("6. When to trust it")
    st.markdown(
        "This all assumes laminar flow. The film Reynolds number Re = 4ρq/μ tells you: smooth "
        "laminar below ≈ 20, wavy laminar beyond that, turbulent much higher. The first tab's "
        "widget shows your live Re."
    )

    st.subheader("Try it live")
    st.markdown(
        "The curve is q(δ) for your fluid. The **red dot** is the flow rate your δ produces; "
        "the **green diamond** is the thickness your target q demands. Drag δ and q apart and "
        "watch the banner complain — one film can't have both unless the markers coincide."
    )
    components.html(TAB2_HTML, height=720, scrolling=False)
