"""Rotating-fluid visualizer: a cup of liquid spun on a turntable at constant
angular velocity. Derives the paraboloid free surface from pressure balances
(no Navier-Stokes), locates it with conservation of volume, and finds the
spin rate at which liquid spills over the rim.

All graphics run as JavaScript in the browser at 60 fps: the real Streamlit
sidebar publishes slider values through localStorage, and each tab's widget
redraws on the storage event. No server round-trip while dragging.
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Rotating Fluid: the Spilling Cup", layout="wide")

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
<div class="sld"><div class="labrow"><span class="t">R cup radius (cm)</span><span class="v" id="o_rad"></span></div>
  <input id="s_rad" type="range" min="2" max="10" step="0.1" value="5" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">L initial depth (cm)</span><span class="v" id="o_dep"></span></div>
  <input id="s_dep" type="range" min="2" max="15" step="0.1" value="8" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">H rim gap (cm)</span><span class="v" id="o_gap"></span></div>
  <input id="s_gap" type="range" min="1" max="10" step="0.1" value="4" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">&omega; spin rate (rad/s)</span><span class="v" id="o_om"></span></div>
  <input id="s_om" type="range" min="0" max="40" step="0.5" value="12" data-dec="1"></div>
<div class="sld"><div class="labrow"><span class="t">g gravity (m/s&sup2;)</span><span class="v" id="o_grav"></span></div>
  <input id="s_grav" type="range" min="1.6" max="24.8" step="0.1" value="9.81" data-dec="2"></div>
<div class="snote">R, L, H, &omega;, g feed both tabs. Lengths are entered in cm and
converted to m inside the formulas; g stays in m/s&sup2;.</div>
<script>
var KEY = 'rotatingfluid_params_v1';
var IDS = ['rad','dep','gap','om','grav'];
var DEFS = { rad:5, dep:8, gap:4, om:12, grav:9.81 };
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

# ---------------- Tab 1 widget: stationary vs rotating cup, A/B/C, volume shading ----------------
TAB1_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
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
  .togs{ display:flex; gap:18px; flex-wrap:wrap; margin:8px 0 2px; font-size:13.5px; }
  .togs label{ display:flex; gap:6px; align-items:center; cursor:pointer; }
  .togs input{ accent-color:#ff4b4b; }
  .flexrow{ display:flex; gap:18px; margin-top:12px; align-items:flex-start; flex-wrap:wrap; }
  #topCanvas{ width:300px; max-width:100%; height:auto; }
  .sidecol{ flex:1 1 260px; min-width:260px; }
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
  .mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:120px; }
  .mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
  .mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
  .mbox .d{ font-size:12px; color:var(--sub); margin-top:2px; }
</style>
</head>
<body>
<canvas id="cupCanvas" width="940" height="500"></canvas>
<div class="togs">
  <label><input type="checkbox" id="t_labels" checked> labels (rim, axis, R, d, h(r))</label>
  <label><input type="checkbox" id="t_points" checked> points A / B / C + pressure paths</label>
  <label><input type="checkbox" id="t_vol" checked> volume-conservation shading</label>
  <label><input type="checkbox" id="t_frame"> rotating-frame view (top inset)</label>
</div>
<div class="flexrow">
  <div>
    <canvas id="topCanvas" width="300" height="300"></canvas>
    <div class="note" style="max-width:300px">Top view of the cup. Blue: tangential velocity
    v&nbsp;=&nbsp;&omega;r. Red: the real inward centripetal acceleration. Tick
    &ldquo;rotating-frame view&rdquo; to see the apparent outward centrifugal effect instead.</div>
  </div>
  <div class="sidecol">
    <div class="vtitle">Readouts (drawn state)</div>
    <div class="mgrid" id="m1"></div>
    <div class="banner" id="limBanner" style="display:none"></div>
    <div class="note">The widget draws the surface only up to the first physical limit:
    wall at the rim, or center at the bottom. Drag &omega; past it and the drawing freezes
    at the limit while this banner says which one you hit.</div>
  </div>
</div>
<script>
var KEY = 'rotatingfluid_params_v1';
var DEFS = { rad:5, dep:8, gap:4, om:12, grav:9.81 };
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
/* Core physics: cm in, SI inside. Never draws liquid below z=0 or above the rim. */
function phys(Rcm, Lcm, Hcm, w, g){
  var R = Rcm/100, L = Lcm/100, H = Hcm/100;
  var RR = R*R;
  var d = w*w*RR/(4*g);              /* center drop at requested w */
  var hR = w*w*RR/(2*g);             /* surface height at wall above lowest point = 2d */
  var wspill = 2*Math.sqrt(g*H)/R;   /* valid when L >= H */
  var wdry = 2*Math.sqrt(g*L)/R;     /* center reaches bottom */
  var wlim = Math.min(wspill, wdry);
  var wdraw = Math.min(w, wlim);     /* clamped spin actually drawn */
  var dd = wdraw*wdraw*RR/(4*g);
  var k2 = wdraw*wdraw/(2*g);
  return { R:R, L:L, H:H, g:g, w:w, d:d, hR:hR, gap:H-d,
    wspill:wspill, wdry:wdry, spillFirst:(wspill<=wdry),
    wlim:wlim, wdraw:wdraw, dd:dd, k2:k2,
    zc:L-dd, ze:L+dd, rim:L+H, limited:(w>wlim+1e-12) };
}
function zs(x, P){ return P.L - P.dd + P.k2*x*x; }
function isDark(){ return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; }
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
function arrowBoth(ctx, x1, y1, x2, y2, color, lw){
  ctx.strokeStyle = color; ctx.lineWidth = lw || 2;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  var a = Math.atan2(y2-y1, x2-x1);
  head(ctx, x2, y2, a, color, 7);
  head(ctx, x1, y1, a+Math.PI, color, 7);
}
function drawCups(){
  var p = readParams(), P = phys(p.rad, p.dep, p.gap, p.om, p.grav);
  var dark = isDark();
  var cv = el('cupCanvas'), ctx = cv.getContext('2d'), W = cv.width, Hh = cv.height;
  ctx.clearRect(0, 0, W, Hh);
  var wallC = dark ? '#cbd5e1' : '#0f172a';
  var liqC  = dark ? 'rgba(56,189,248,0.28)' : 'rgba(2,132,199,0.20)';
  var surfC = dark ? '#7dd3fc' : '#0284c7';
  var txtC  = dark ? '#e8eaf0' : '#31333f';
  var subC  = dark ? '#9aa0ae' : '#6b7280';
  var redC  = '#ef4444', ambC = 'rgba(245,158,11,0.35)';
  var R = P.R, rim = P.rim;
  var cx1 = 235, cx2 = 705;
  var s = Math.min((Hh-110)/rim, 380/(2*R));
  function Y(z){ return Hh-55 - z*s; }
  function X(cx, x){ return cx + x*s; }
  ctx.font = '13px "Source Sans Pro",sans-serif';
  var showL = el('t_labels').checked, showP = el('t_points').checked, showV = el('t_vol').checked;
  /* cup walls + titles */
  [[cx1, 'stationary', 'surface flat'], [cx2, 'rotating', 'ω = ' + p.om.toFixed(1) + ' rad/s']].forEach(function(c){
    var cx = c[0];
    ctx.lineWidth = 5; ctx.strokeStyle = wallC;
    ctx.beginPath();
    ctx.moveTo(X(cx,-R), Y(0)); ctx.lineTo(X(cx,-R), Y(rim));
    ctx.moveTo(X(cx, R), Y(0)); ctx.lineTo(X(cx, R), Y(rim));
    ctx.moveTo(X(cx,-R), Y(0)); ctx.lineTo(X(cx, R), Y(0));
    ctx.stroke();
    ctx.fillStyle = txtC; ctx.textAlign = 'center';
    ctx.font = '600 15px "Source Sans Pro",sans-serif';
    ctx.fillText(c[1], cx, 26);
    ctx.font = '13px "Source Sans Pro",sans-serif'; ctx.fillStyle = subC;
    ctx.fillText(c[2], cx, 44);
    if (showL){
      ctx.fillStyle = txtC;
      ctx.fillText('rim', X(cx,-R)-6, Y(rim)-8); ctx.textAlign = 'left';
      ctx.fillText('rim', X(cx, R)+8, Y(rim)-8); ctx.textAlign = 'center';
    }
  });
  /* stationary liquid: flat */
  ctx.fillStyle = liqC;
  ctx.fillRect(X(cx1,-R), Y(P.L), 2*R*s, Y(0)-Y(P.L));
  ctx.strokeStyle = surfC; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.moveTo(X(cx1,-R), Y(P.L)); ctx.lineTo(X(cx1,R), Y(P.L)); ctx.stroke();
  /* rotating liquid: paraboloid z_s(x) */
  var N = 61, i, x, pts = [];
  for (i = 0; i < N; i++){ x = -R + 2*R*i/(N-1); pts.push([x, zs(x, P)]); }
  ctx.fillStyle = liqC;
  ctx.beginPath();
  ctx.moveTo(X(cx2, pts[0][0]), Y(pts[0][1]));
  pts.forEach(function(q){ ctx.lineTo(X(cx2, q[0]), Y(q[1])); });
  ctx.lineTo(X(cx2, R), Y(0)); ctx.lineTo(X(cx2, -R), Y(0));
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle = surfC; ctx.lineWidth = 2.5;
  ctx.beginPath();
  pts.forEach(function(q, k){ if (k) ctx.lineTo(X(cx2, q[0]), Y(q[1])); else ctx.moveTo(X(cx2, q[0]), Y(q[1])); });
  ctx.stroke();
  /* original level (dashed) + axis on the rotating cup */
  if (showL){
    ctx.strokeStyle = subC; ctx.lineWidth = 1.5; ctx.setLineDash([6,5]);
    ctx.beginPath(); ctx.moveTo(X(cx2,-R), Y(P.L)); ctx.lineTo(X(cx2,R), Y(P.L)); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx2, Y(0)); ctx.lineTo(cx2, Y(rim)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = txtC; ctx.textAlign = 'left';
    ctx.fillText('original level', X(cx2, R)+8, Y(P.L)+4);
    ctx.fillText('rotation axis', cx2+8, Y(rim)+18);
    /* R arrow under the stationary cup */
    arrowBoth(ctx, cx1, Y(0)+30, X(cx1, R), Y(0)+30, txtC, 1.8);
    ctx.textAlign = 'center'; ctx.fillText('R', cx1 + R*s/2, Y(0)+48);
    /* d arrow: original level down to the new lowest point */
    if (P.dd > 1e-9){
      arrowBoth(ctx, cx2-0.62*R*s, Y(P.L), cx2-0.62*R*s, Y(P.zc), txtC, 1.8);
      ctx.fillText('d', cx2-0.62*R*s-12, (Y(P.L)+Y(P.zc))/2+4);
    }
  }
  /* h(r) arrow + points A, B, C with pressure paths */
  var r0 = 0.62*R, hrise = zs(r0, P) - P.zc;
  if (showL && hrise > 1e-9){
    arrowBoth(ctx, X(cx2, r0), Y(P.zc), X(cx2, r0), Y(zs(r0, P)), txtC, 1.8);
    ctx.fillStyle = txtC; ctx.textAlign = 'left';
    ctx.fillText('h(r)', X(cx2, r0)+10, (Y(P.zc)+Y(zs(r0, P)))/2+4);
  }
  if (showP){
    var A = [cx2, Y(P.zc)], B = [X(cx2, r0), Y(P.zc)], C = [X(cx2, r0), Y(zs(r0, P))];
    ctx.strokeStyle = redC; ctx.lineWidth = 1.6; ctx.setLineDash([5,4]);
    ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
    if (hrise > 1e-9){ ctx.beginPath(); ctx.moveTo(C[0], C[1]); ctx.lineTo(B[0], B[1]); ctx.stroke(); }
    ctx.setLineDash([]);
    [[A,'A'],[B,'B'],[C,'C']].forEach(function(q){
      ctx.fillStyle = redC;
      ctx.beginPath(); ctx.arc(q[0][0], q[0][1], 4.5, 0, 2*Math.PI); ctx.fill();
      ctx.fillStyle = txtC; ctx.textAlign = 'left';
      ctx.fillText(q[1], q[0][0]+8, q[0][1]-6);
    });
    ctx.fillStyle = subC; ctx.textAlign = 'center';
    ctx.fillText('P = 0 (gauge) at A and C; P at B from either path', cx2, Y(0)+48);
  }
  /* volume-conservation shading: cylinder πR²d vs region under the paraboloid */
  if (showV && P.dd > 1e-9){
    ctx.fillStyle = ambC;
    ctx.fillRect(X(cx1,-R), Y(P.L), 2*R*s, Y(P.L-P.dd)-Y(P.L));
    ctx.beginPath();
    pts.forEach(function(q, k){ if (k) ctx.lineTo(X(cx2, q[0]), Y(q[1])); else ctx.moveTo(X(cx2, q[0]), Y(q[1])); });
    ctx.lineTo(X(cx2, R), Y(P.L-P.dd)); ctx.lineTo(X(cx2, -R), Y(P.L-P.dd));
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = txtC; ctx.textAlign = 'center';
    ctx.fillText('equal volumes = πR²d', cx2, Y(0)+30);
  }
  drawTop(P, dark);
  /* readouts + limit banner */
  el('m1').innerHTML =
    mbox('d · center drop', (P.dd*100).toFixed(2)+' cm', 'ω²R²/4g') +
    mbox('wall rise', (P.dd*100).toFixed(2)+' cm', '= d, above original level') +
    mbox('gap to rim', (Math.max(0,(P.rim-P.ze))*100).toFixed(2)+' cm', 'H − d') +
    mbox('z center', (P.zc*100).toFixed(2)+' cm', 'L − d') +
    mbox('z edge', (P.ze*100).toFixed(2)+' cm', 'L + d') +
    mbox('ω drawn', P.wdraw.toFixed(1)+' rad/s', 'clamped at the limit');
  var bn = el('limBanner');
  if (P.limited){
    bn.style.display = 'block';
    if (P.spillFirst){ bn.className = 'banner bad'; bn.textContent = 'SPILL LIMIT — the wall reached the rim at ω_spill = ' + P.wspill.toFixed(2) + ' rad/s. The drawing is frozen there.'; }
    else { bn.className = 'banner warn'; bn.textContent = 'DRY LIMIT — the center reached the bottom at ω_dry = ' + P.wdry.toFixed(2) + ' rad/s. The drawing is frozen there.'; }
  } else bn.style.display = 'none';
}
function mbox(k, n, d){
  return '<div class="mbox"><div class="k">'+k+'</div><div class="n">'+n+'</div><div class="d">'+d+'</div></div>';
}
function drawTop(P, dark){
  var cv = el('topCanvas'), ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, cv.width, cv.height);
  var cx = 150, cy = 150, Rc = 110;
  var txtC = dark ? '#e8eaf0' : '#31333f', subC = dark ? '#9aa0ae' : '#6b7280';
  ctx.strokeStyle = dark ? '#cbd5e1' : '#0f172a'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.arc(cx, cy, Rc, 0, 2*Math.PI); ctx.stroke();
  ctx.fillStyle = 'rgba(56,189,248,0.10)';
  ctx.beginPath(); ctx.arc(cx, cy, Rc, 0, 2*Math.PI); ctx.fill();
  var a = -0.6, pr = 70;
  var px = cx + pr*Math.cos(a), py = cy + pr*Math.sin(a);
  ctx.fillStyle = txtC;
  ctx.beginPath(); ctx.arc(px, py, 5, 0, 2*Math.PI); ctx.fill();
  ctx.beginPath(); ctx.arc(cx, cy, 3, 0, 2*Math.PI); ctx.fill();
  var wfrac = Math.min(1, P.w/40);
  var vl = 34 + 46*wfrac, al = 30 + 40*wfrac;
  var tx = -Math.sin(a), ty = Math.cos(a);           /* tangential */
  arrow(ctx, px, py, px+tx*vl, py+ty*vl, '#1f77b4', 2.5);
  ctx.fillStyle = '#1f77b4'; ctx.textAlign = 'left';
  ctx.fillText('v', px+tx*vl+6, py+ty*vl+4);
  var rotFrame = el('t_frame').checked;
  if (!rotFrame){
    var ix = cx-px, iy = cy-py, il = Math.hypot(ix, iy);   /* inward */
    arrow(ctx, px, py, px+ix/il*al, py+iy/il*al, '#ef4444', 2.5);
    ctx.fillStyle = '#ef4444';
    ctx.fillText('a inward', px+ix/il*al-58, py+iy/il*al-8);
    ctx.fillStyle = subC; ctx.textAlign = 'center';
    ctx.fillText('lab frame: real inward force', cx, 292);
  } else {
    var ox = px-cx, oy = py-cy, ol = Math.hypot(ox, oy);   /* outward */
    ctx.setLineDash([5,4]);
    arrow(ctx, px, py, px+ox/ol*al, py+oy/ol*al, '#f59e0b', 2.5);
    ctx.setLineDash([]);
    ctx.fillStyle = '#f59e0b'; ctx.textAlign = 'left';
    ctx.fillText('apparent', px+ox/ol*al+6, py+oy/ol*al-2);
    ctx.fillText('centrifugal', px+ox/ol*al+6, py+oy/ol*al+12);
    ctx.fillStyle = subC; ctx.textAlign = 'center';
    ctx.fillText('rotating frame: liquid at rest', cx, 292);
  }
}
function draw(){ drawCups(); }
['t_labels','t_points','t_vol','t_frame'].forEach(function(id){
  el(id).addEventListener('change', draw);
});
if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
window.addEventListener('storage', function(e){ if (e.key === KEY) draw(); });
draw();
</script>
</body>
</html>
"""

# ---------------- Tab 2 widget: sweep of center/edge vs omega, critical speeds ----------------
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
<div id="plotS"></div>
<div class="banner" id="regBanner"></div>
<div class="mgrid" id="m2"></div>
<div class="note">The curves freeze at their limits: the edge never crosses the rim line and
the center never goes below the bottom. Vertical dashed lines mark &omega;_spill and
&omega;_dry; the solid gray line is your current &omega;. If a dashed line sits beyond the
plot edge, its value is printed in the readout boxes.</div>
<script>
var KEY = 'rotatingfluid_params_v1';
var DEFS = { rad:5, dep:8, gap:4, om:12, grav:9.81 };
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
function rpm(w){ return w*60/(2*Math.PI); }
function draw(){
  var p = readParams();
  var R = p.rad/100, L = p.dep/100, H = p.gap/100, g = p.grav;
  var wspill = 2*Math.sqrt(g*H)/R, wdry = 2*Math.sqrt(g*L)/R;
  var xmax = Math.min(Math.max(40, wspill, wdry), 120);
  var N = 220, ws = [], zc = [], ze = [], i, w, d;
  for (i = 0; i < N; i++){
    w = xmax*i/(N-1); d = w*w*R*R/(4*g);
    ws.push(w);
    zc.push(Math.max(0, L-d)*100);
    ze.push(Math.min(L+H, L+d)*100);
  }
  var dark = isDark(), wallC = dark ? '#8a8f98' : 'gray';
  var LO = themed('Center depth and edge height vs spin rate');
  LO.xaxis.title = 'omega (rad/s)'; LO.yaxis.title = 'z (cm)'; LO.height = 400;
  LO.yaxis.range = [0, (L+H)*100*1.08];
  LO.xaxis.range = [0, xmax];
  LO.shapes = [
    { type:'line', x0:0, x1:1, xref:'paper', y0:(L+H)*100, y1:(L+H)*100,
      line:{ dash:'dash', color:'#ef4444', width:1.5 } },
    { type:'line', x0:0, x1:1, xref:'paper', y0:L*100, y1:L*100,
      line:{ dash:'dot', color:wallC, width:1.5 } },
    { type:'line', x0:0, x1:1, xref:'paper', y0:0, y1:0,
      line:{ color:wallC, width:1.5 } }
  ];
  var annot = [
    { x:1.0, xref:'paper', y:(L+H)*100, text:'rim', showarrow:false,
      font:{ color:'#ef4444', size:12 }, xanchor:'right' },
    { x:1.0, xref:'paper', y:L*100, text:'original level', showarrow:false,
      font:{ color:wallC, size:12 }, xanchor:'right' }
  ];
  function vline(xv, color, dash, label){
    if (xv > xmax) return;
    LO.shapes.push({ type:'line', x0:xv, x1:xv, y0:0, y1:1, yref:'paper',
      line:{ dash:dash, color:color, width:1.8 } });
    annot.push({ x:xv, y:1.0, yref:'paper', text:label, showarrow:false,
      font:{ color:color, size:12 }, yanchor:'bottom' });
  }
  vline(wspill, '#ef4444', 'dash', 'omega_spill');
  vline(wdry, '#f59e0b', 'dash', 'omega_dry');
  vline(p.om, wallC, 'solid', 'your omega');
  LO.annotations = annot;
  Plotly.react('plotS', [
    { x:ws, y:zc, mode:'lines', line:{ width:3, color:'#1f77b4' }, name:'center z(0) = L - d' },
    { x:ws, y:ze, mode:'lines', line:{ width:3, color:'#ff7f0e' }, name:'edge z(R) = L + d' }
  ], LO, { displayModeBar:true, responsive:true });
  var bn = el('regBanner'), frac = p.om/wspill;
  if (wspill <= wdry){
    bn.className = 'banner ok';
    bn.textContent = 'SPILL-FIRST REGIME (L \u2265 H) \u2014 the wall reaches the rim at \u03c9_spill = ' +
      wspill.toFixed(2) + ' rad/s before the center could dry out (\u03c9_dry = ' + wdry.toFixed(2) + ' rad/s).';
  } else {
    bn.className = 'banner warn';
    bn.textContent = 'DRY-FIRST REGIME (L < H) \u2014 the center would reach the bottom at \u03c9_dry = ' +
      wdry.toFixed(2) + ' rad/s before any spilling. The annular dry-center shape needs a different ' +
      'geometric model and is out of scope here; the drawing stops at the dry limit.';
  }
  el('m2').innerHTML =
    '<div class="mbox"><div class="k">\u03c9_spill</div><div class="n">' + wspill.toFixed(2) +
    ' rad/s</div><div class="d">' + rpm(wspill).toFixed(0) + ' rpm \u00b7 2\u221a(gH)/R' +
    (wspill > xmax ? ' \u2014 beyond plot edge' : '') + '</div></div>' +
    '<div class="mbox"><div class="k">\u03c9_dry</div><div class="n">' + wdry.toFixed(2) +
    ' rad/s</div><div class="d">' + rpm(wdry).toFixed(0) + ' rpm \u00b7 2\u221a(gL)/R' +
    (wdry > xmax ? ' \u2014 beyond plot edge' : '') + '</div></div>' +
    '<div class="mbox"><div class="k">your \u03c9</div><div class="n">' + p.om.toFixed(1) +
    ' rad/s</div><div class="d">' + rpm(p.om).toFixed(0) + ' rpm</div></div>' +
    '<div class="mbox"><div class="k">\u03c9 / \u03c9_spill</div><div class="n">' + (frac*100).toFixed(1) +
    ' %</div><div class="d">' + (frac >= 1 ? 'at or past spilling' : 'headroom to spilling') + '</div></div>';
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
    components.html(SIDEBAR_HTML, height=480, scrolling=False)

tab1, tab2 = st.tabs(["The paraboloid", "When it spills"])

with tab1:
    st.header("Why the surface becomes a paraboloid")
    st.markdown(
        "_An open cup on a turntable, spun at constant angular velocity ω. After the sloshing "
        "settles, the liquid rotates with the cup — rigid-body rotation — and the surface "
        "dips at the center and climbs at the wall. No Navier–Stokes: just pressure forces, "
        "Newton's second law, and geometry. Drag the sidebar sliders; every graphic below "
        "updates live in your browser._"
    )

    st.subheader("1. The setup")
    st.markdown(
        "- **R**: fixed inside radius of the cup; **r**: radial distance from the axis (0 to R); "
        "**x**: signed coordinate across a full cross-section (−R to R), so r² becomes x².\n"
        "- **L**: initial liquid depth; **H**: initial vertical gap between the resting surface "
        "and the rim (fixed by how full you filled it — not the changing gap once spinning).\n"
        "- **d**: how far the center of the surface drops below its original level.\n"
        "- **h(r)**: height of the rotating surface at radius r, measured **above its lowest point**.\n"
        "- Assumptions: constant density ρ, steady rigid-body rotation, atmospheric pressure "
        "above the liquid, negligible surface tension."
    )

    st.subheader("2. Why pressure changes vertically")
    st.markdown(
        "Take a thin vertical slab of fluid that isn't accelerating up or down. Pressure below "
        "pushes it up; pressure above plus its weight pushes it down. With z positive upward:"
    )
    st.latex(r"\frac{\partial P}{\partial z} = -\rho g")
    st.markdown(
        "Pressure falls as you rise. For constant density, the gauge pressure (relative to the "
        "atmosphere, so zero at the free surface) a depth h below the surface is simply:"
    )
    st.latex(r"P = \rho g h")

    st.subheader("3. Circular motion needs inward acceleration")
    st.markdown(
        "A fluid particle circling at radius r with constant angular velocity ω has constant "
        "speed but ever-changing direction — so it accelerates. Write its position as"
    )
    st.latex(r"\mathbf{p} = r\cos\theta\,\hat{\mathbf{i}} + r\sin\theta\,\hat{\mathbf{j}}")
    st.markdown("Differentiate once (velocity), twice (acceleration), with ω = dθ/dt constant:")
    st.latex(r"\mathbf{v} = r\omega(-\sin\theta\,\hat{\mathbf{i}} + \cos\theta\,\hat{\mathbf{j}})"
             r"\qquad\Longrightarrow\qquad"
             r"\mathbf{a} = -r\omega^2(\cos\theta\,\hat{\mathbf{i}} + \sin\theta\,\hat{\mathbf{j}})")
    st.markdown(
        "The acceleration points **inward** with magnitude ω²r. With outward as positive radial "
        "direction, a_r = −ω²r. This is **centripetal** acceleration — the real, inward one. "
        "An observer spinning with the cup may instead call the liquid stationary and invoke an "
        "apparent outward **centrifugal** effect; same motion, different frame. Note: constant ω "
        "means zero *angular* acceleration, not zero centripetal acceleration — the toggle under "
        "the top-view inset shows both descriptions."
    )

    st.subheader("4. Why pressure increases outward")
    st.markdown(
        "At one height, the pressure must be higher farther out: that pressure difference is "
        "what shoves each particle inward to keep it circling. Radial force balance:"
    )
    st.latex(r"-\frac{\partial P}{\partial r} = \rho(-\omega^2 r)"
             r"\;\;\Longrightarrow\;\;"
             r"\frac{\partial P}{\partial r} = \rho\omega^2 r")
    st.markdown("Integrate at fixed height between two radii:")
    st.latex(r"P_2 - P_1 = \frac{\rho\omega^2}{2}\,(r_2^2 - r_1^2)")

    st.subheader("5. One point, two pressure calculations")
    st.markdown(
        "Put **A** at the lowest point of the rotating surface (on the axis, r = 0 — exposed, "
        "so gauge pressure zero). Put **B** inside the liquid at radius r, at A's height. "
        "Radially outward from A to B:"
    )
    st.latex(r"P_B = \frac{\rho\omega^2 r^2}{2}")
    st.markdown(
        "Now climb vertically from **B** to **C**, directly above B on the free surface. "
        "That column has height h(r), so:"
    )
    st.latex(r"P_B = \rho g\,h(r)")
    st.markdown("Same point, same pressure — equate and cancel ρ:")
    st.latex(r"\boxed{h(r) = \frac{\omega^2 r^2}{2g}}")
    st.markdown(
        "Height grows with r²: the cross-section is a parabola, the 3D surface a paraboloid. "
        "Toggle the A/B/C overlay in the widget to see the two paths."
    )

    st.subheader("Try it live")
    st.markdown(
        "The cup pair shows the resting and spinning states side by side. Raise ω and watch "
        "the center sink while the edges climb — the liquid volume never changes, only its shape."
    )
    components.html(TAB1_HTML, height=980, scrolling=False)

with tab2:
    st.header("How fast before it spills?")
    st.markdown(
        "_The parabola's shape is known; volume conservation pins down where it sits, and the "
        "rim height decides when the party ends. Drag the sidebar sliders — the sweep plot, "
        "the critical speeds, and the regime banner all update live._"
    )

    st.subheader("1. Conservation of volume finds the center drop")
    st.markdown(
        "h(r) is measured from the new lowest point, but how far did that point sink? Slice a "
        "horizontal plane through it. Before spinning, the liquid above that plane was a "
        "cylinder of height d:"
    )
    st.latex(r"V_{\text{before}} = \pi R^2 d")
    st.markdown(
        "After spinning, the liquid above that plane hugs the paraboloid. Add it up in thin "
        "rings — a ring at radius r has area dA = 2πr·dr and local height h(r):"
    )
    st.latex(r"\pi R^2 d = \int_0^R h(r)\,2\pi r\,dr"
             r" = \frac{\pi\omega^2}{g}\int_0^R r^3\,dr"
             r" = \frac{\pi\omega^2 R^4}{4g}")
    st.latex(r"\boxed{d = \frac{\omega^2 R^2}{4g}}")
    st.markdown(
        "At the wall, h(R) = ω²R²/2g = **2d**. So the wall climbs above the original level by "
        "exactly the same distance d that the center drops below it — the rise mirrors the dip. "
        "Toggle the amber shading in the first tab's widget: the two equal volumes, live."
    )

    st.subheader("2. The spill condition")
    st.markdown(
        "The wall's rise above the original level is h(R) − d = d. Spilling starts when that "
        "rise eats the whole initial rim gap H:"
    )
    st.latex(r"h(R) - d = H \;\;\Longleftrightarrow\;\;"
             r"\frac{\omega^2R^2}{2g} - \frac{\omega^2R^2}{4g} = H")
    st.latex(r"\boxed{\omega_{\text{spill}} = \frac{2\sqrt{gH}}{R}}")
    st.markdown(
        "The square root covers gH only; R sits outside it. Double the rim gap and the spill "
        "speed rises by √2; double the cup radius and it halves."

    )

    st.subheader("3. A caveat: which limit comes first?")
    st.markdown(
        "This assumed liquid still covers the bottom center when the wall reaches the rim — "
        "true when **L ≥ H** (at L = H both limits arrive together). If **L < H**, the center "
        "hits the bottom first, at ω_dry = 2√(gL)/R, leaving a dry central disk whose annular "
        "shape needs a different geometric model — out of scope here. The widgets refuse to "
        "draw past either limit and tell you which one you hit."
    )

    st.subheader("Try it live")
    st.markdown(
        "The sweep plot draws the center and edge heights against ω, frozen at their limits. "
        "Push the ω slider past the red dashed line and watch the first tab's cup freeze at "
        "the rim."
    )
    components.html(TAB2_HTML, height=730, scrolling=False)

    st.subheader("The whole story, in one line")
    st.markdown(
        "**Circular motion demands inward acceleration → a radial pressure difference supplies "
        "the inward force → vertical and radial pressure calculations fix the surface shape → "
        "conservation of volume locates that surface → the rim height decides when spilling "
        "begins.**"
    )
