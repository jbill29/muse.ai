"""THF GPC Explorer: an interactive visual guide to the THF gel permeation chromatography instrument."""
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
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

WIDGET_CSS = """:root{
  --track:#dfe1e6; --lab:#31333f; --val:#31333f; --sub:#6b7280;
  --accent:#ff4b4b; --box:#f1f5f9;
}
@media (prefers-color-scheme: dark){
  :root{ --track:#3a3d46; --lab:#e8eaf0; --val:#e8eaf0; --sub:#9aa0ae; --box:#232838; }
}
html, body{ background:transparent; }
body{
  font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif;
  margin:0; color:var(--lab);
}
.wrap{ display:flex; gap:18px; align-items:flex-start; }
.side{ width:232px; flex:0 0 232px; padding:6px 2px 0 6px; }
.main{ flex:1 1 auto; min-width:0; }
.sld{ margin-bottom:14px; }
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
.cap{ font-size:12px; color:var(--sub); margin:-6px 0 12px; line-height:1.4; }
.chk{ display:flex; align-items:center; gap:8px; font-size:14px; margin:2px 0 12px; cursor:pointer; color:var(--lab); }
.chk input{ accent-color:var(--accent); width:16px; height:16px; cursor:pointer; }
.pbtn{
  font-family:inherit; font-size:14px; padding:6px 16px; border-radius:6px;
  border:1px solid var(--track); background:var(--box); color:var(--lab);
  cursor:pointer; margin:2px 0 12px;
}
.pbtn:hover{ border-color:var(--accent); }
.mgrid{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }
.mbox{ background:var(--box); border-radius:8px; padding:8px 12px; min-width:118px; }
.mbox .k{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--sub); }
.mbox .n{ font-size:17px; font-weight:600; color:var(--val); font-variant-numeric:tabular-nums; }
.mbox .d{ font-size:12px; color:var(--sub); }
.note{ font-size:13.5px; color:var(--lab); margin-top:10px; line-height:1.5; }
/* separation column graphic */
.sepmain{ display:flex; gap:16px; align-items:stretch; }
.colwrap{ flex:0 0 148px; }
.coltitle{ text-align:center; font-weight:600; font-size:14px; margin-bottom:4px; }
.colbody{ position:relative; height:380px; background:var(--box); border:2px solid #475569; border-radius:6px; }
.band{ position:absolute; left:10%; width:80%; height:18px; border-radius:4px; opacity:.92; }
.blab{ position:absolute; left:calc(100% + 5px); font-size:12px; font-weight:600; white-space:nowrap; }
.colflow{ text-align:center; color:var(--sub); font-size:13px; margin-top:6px; }
.flexplot{ flex:1 1 auto; min-width:0; }
/* calibration two-plot row */
.calmain{ display:flex; gap:8px; }
.calmain > div{ flex:1 1 0; min-width:0; }
"""


SHARED_JS = """/* Shared helpers included at the top of every widget script. */
function sval(id) { return parseFloat(document.getElementById('s_' + id).value); }
function refreshSlider(id) {
  var el = document.getElementById('s_' + id);
  var dec = parseInt(el.getAttribute('data-dec') || '2', 10);
  document.getElementById('o_' + id).textContent = parseFloat(el.value).toFixed(dec);
  el.style.setProperty('--p', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
}
function bindSlider(id) { document.getElementById('s_' + id).addEventListener('input', draw); }
function isDark() { return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; }
function themed(title) {
  var d = isDark();
  var grid = d ? '#2e3138' : '#e5e7eb';
  return {
    title: title,
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: '"Source Sans Pro",sans-serif', color: d ? '#e8eaf0' : '#31333f' },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
    margin: { l: 55, r: 10, t: 45, b: 45 }
  };
}
function vline(x, color, dash, w) {
  return { type: 'line', x0: x, x1: x, y0: 0, y1: 1, yref: 'paper',
           line: { dash: dash, color: color, width: w || 1.2 } };
}
function fmtInt(v) { return Math.round(v).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); }
function onThemeChange() {
  if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
}
"""


CHROM_JS = """/* Chromatogram lab widget: log-normal MWD -> RI chromatogram, live. */
var IDS = ['logMnA', 'DA', 'logMnB', 'DB'];
function sample(logMn, D) {
  var Mn = Math.pow(10, logMn), Mw = Mn * D;
  var s2 = Math.log(D), mu = Math.log(Mn) - s2 / 2, sig = Math.sqrt(s2);
  var xmean = (mu + sig * sig) / Math.log(10), xsd = sig / Math.log(10);
  var N = 400, t = [], w = [], i, ti, x;
  for (i = 0; i < N; i++) {
    ti = 2 + 14 * i / (N - 1); t.push(ti);
    x = 7 - 0.25 * ti;
    w.push(Math.exp(-0.5 * Math.pow((x - xmean) / xsd, 2)));
  }
  var mx = Math.max.apply(null, w);
  for (i = 0; i < N; i++) w[i] /= mx;
  return { t: t, w: w, Mn: Mn, Mw: Mw, D: D,
           tMn: (7 - Math.log10(Mn)) / 0.25, tMw: (7 - Math.log10(Mw)) / 0.25 };
}
function metricHtml(tag, s) {
  function box(k, n) {
    return '<div class="mbox"><div class="k">' + k + '</div><div class="n">' + n + '</div></div>';
  }
  return box(tag + ' Mn', fmtInt(s.Mn) + ' g/mol') +
         box(tag + ' Mw', fmtInt(s.Mw) + ' g/mol') +
         box(tag + ' Đ', s.D.toFixed(2));
}
function draw() {
  IDS.forEach(refreshSlider);
  var showB = document.getElementById('c_showB').checked;
  document.getElementById('rowB').style.display = showB ? 'block' : 'none';
  var A = sample(sval('logMnA'), sval('DA'));
  var traces = [{ x: A.t, y: A.w, mode: 'lines',
                  line: { width: 3, color: '#3b82f6' }, name: 'Sample A' }];
  var shapes = [vline(A.tMn, '#3b82f6', 'dash', 1.2), vline(A.tMw, '#3b82f6', 'dot', 1.6)];
  var annot = [
    { x: A.tMn, y: 1.03, text: 'Mn', showarrow: false, font: { color: '#3b82f6', size: 11 } },
    { x: A.tMw, y: 0.94, text: 'Mw', showarrow: false, font: { color: '#3b82f6', size: 11 } }
  ];
  var B = null;
  if (showB) {
    B = sample(sval('logMnB'), sval('DB'));
    traces.push({ x: B.t, y: B.w, mode: 'lines',
                  line: { width: 3, color: '#f59e0b' }, name: 'Sample B' });
    shapes.push(vline(B.tMn, '#f59e0b', 'dash', 1.2));
  }
  var L = themed('Simulated chromatogram');
  L.xaxis.title = 'elution time (min) →'; L.xaxis.range = [2, 16];
  L.yaxis.title = 'RI signal (normalized)'; L.yaxis.range = [0, 1.32];
  L.shapes = shapes; L.annotations = annot; L.showlegend = true; L.height = 420;
  Plotly.react('plotC', traces, L, { displayModeBar: true, responsive: true });
  document.getElementById('mA').innerHTML = metricHtml('Sample A', A);
  document.getElementById('mB').innerHTML = showB ? metricHtml('Sample B', B) : '';
  document.getElementById('capA').textContent = 'Sample A Mn = ' + fmtInt(A.Mn) + ' g/mol';
  document.getElementById('capB').textContent = showB ? 'Sample B Mn = ' + fmtInt(B.Mn) + ' g/mol' : '';
}
IDS.forEach(bindSlider);
document.getElementById('c_showB').addEventListener('change', draw);
onThemeChange();
draw();
"""


DET_JS = """/* Detectors widget: RI / MALS / viscometer traces vs Mark-Houwink exponent, live. */
var IDS = ['mhA'];
function draw() {
  IDS.forEach(refreshSlider);
  var a = sval('mhA');
  var Mn = 1e5, D = 1.6;
  var s2 = Math.log(D), mu = Math.log(Mn) - s2 / 2, sig = Math.sqrt(s2);
  var xm = (mu + sig * sig) / Math.log(10), xs = sig / Math.log(10);
  var N = 500, td = [], wd = [], i, t, x;
  for (i = 0; i < N; i++) {
    t = 2 + 14 * i / (N - 1); td.push(t);
    x = 7 - 0.25 * t;
    wd.push(Math.exp(-0.5 * Math.pow((x - xm) / xs, 2)));
  }
  var mx = Math.max.apply(null, wd);
  var ri = [], mals = [], visc = [];
  for (i = 0; i < N; i++) {
    var w = wd[i] / mx, m = Math.pow(10, 7 - 0.25 * td[i]);
    ri.push(w); mals.push(w * m); visc.push(w * Math.pow(m, a));
  }
  function norm(arr) {
    var m2 = Math.max.apply(null, arr);
    return arr.map(function(v) { return v / m2; });
  }
  mals = norm(mals); visc = norm(visc);
  function pk(arr) {
    var bi = 0, j;
    for (j = 1; j < arr.length; j++) if (arr[j] > arr[bi]) bi = j;
    return td[bi];
  }
  var pRI = pk(ri), pM = pk(mals);
  var rows = [
    { y: ri,   c: '#3b82f6', xa: 'x',  ya: 'y',  yr: 'y',
      t: 'RI (Optilab rEX): concentration → how MUCH elutes when', p: pRI },
    { y: mals, c: '#ef4444', xa: 'x2', ya: 'y2', yr: 'y2',
      t: 'MALS (miniDAWN TREOS): ∝ concentration × mass → HOW BIG it is', p: pM },
    { y: visc, c: '#10b981', xa: 'x3', ya: 'y3', yr: 'y3',
      t: 'Viscometer (Viscostar II): ∝ concentration × viscosity → chain SHAPE', p: pk(visc) }
  ];
  var traces = rows.map(function(r) {
    return { x: td, y: r.y, mode: 'lines', line: { width: 2.6, color: r.c },
             xaxis: r.xa, yaxis: r.ya, showlegend: false };
  });
  var shapes = rows.map(function(r) {
    return { type: 'line', x0: r.p, x1: r.p, y0: 0, y1: 1.15, yref: r.yr,
             line: { dash: 'dash', color: r.c, width: 1.2 } };
  });
  var annot = [
    { x: 0, y: 1.0,   xref: 'paper', yref: 'paper', text: rows[0].t, showarrow: false,
      xanchor: 'left', font: { color: '#3b82f6', size: 12 } },
    { x: 0, y: 0.665, xref: 'paper', yref: 'paper', text: rows[1].t, showarrow: false,
      xanchor: 'left', font: { color: '#ef4444', size: 12 } },
    { x: 0, y: 0.33,  xref: 'paper', yref: 'paper', text: rows[2].t, showarrow: false,
      xanchor: 'left', font: { color: '#10b981', size: 12 } }
  ];
  var L = themed('');
  var d = isDark(), grid = d ? '#2e3138' : '#e5e7eb';
  L.height = 620;
  L.xaxis  = { domain: [0, 1], anchor: 'y',  showticklabels: false, gridcolor: grid, zerolinecolor: grid };
  L.xaxis2 = { domain: [0, 1], anchor: 'y2', showticklabels: false, gridcolor: grid, zerolinecolor: grid };
  L.xaxis3 = { domain: [0, 1], anchor: 'y3', title: 'elution time (min) →', gridcolor: grid, zerolinecolor: grid };
  L.yaxis  = { domain: [0.70, 1],      title: 'normalized', range: [0, 1.15], gridcolor: grid, zerolinecolor: grid };
  L.yaxis2 = { domain: [0.355, 0.655],  title: 'normalized', range: [0, 1.15], gridcolor: grid, zerolinecolor: grid };
  L.yaxis3 = { domain: [0.01, 0.31],    title: 'normalized', range: [0, 1.15], gridcolor: grid, zerolinecolor: grid };
  L.shapes = shapes; L.annotations = annot;
  Plotly.react('plotD', traces, L, { displayModeBar: true, responsive: true });
  document.getElementById('detNote').innerHTML =
    'See how the peaks shift: the <b>MALS peak (t = ' + pM.toFixed(1) +
    ' min)</b> comes out earlier than the <b>RI peak (t = ' + pRI.toFixed(1) +
    ' min)</b>, because light scattering weights each slice by its mass — the heavy chains ' +
    'dominate. That skew is exactly the extra information triple detection buys you.';
}
IDS.forEach(bindSlider);
onThemeChange();
draw();
"""


CAL_JS = """/* Calibration widget: conventional vs true MW and the universal line, live. */
var IDS = ['calA'];
function draw() {
  IDS.forEach(refreshSlider);
  var as = sval('calA');
  var Au = 9.17, Bu = 0.51, K = 1.2e-4, a_ps = 0.7;
  var N = 300, tc = [], lMapp = [], lMtrue = [], lVh = [], i, t, lvh;
  for (i = 0; i < N; i++) {
    t = 4 + 10 * i / (N - 1); tc.push(t);
    lvh = Au - Bu * t; lVh.push(lvh);
    lMapp.push((Au - Math.log10(K)) / (1 + a_ps) - Bu * t / (1 + a_ps));
    lMtrue.push((lvh - Math.log10(K)) / (1 + as));
  }
  var ts = [5, 7, 9, 11, 13];
  var stdY = ts.map(function(tt) {
    return (Au - Math.log10(K)) / (1 + a_ps) - Bu * tt / (1 + a_ps);
  });
  var L1 = themed('Level 1 — conventional: misreads the sample');
  L1.xaxis.title = 'elution time (min)'; L1.yaxis.title = 'log\\u2081\\u2080 M';
  L1.height = 400; L1.showlegend = true; L1.legend = { font: { size: 10 } };
  Plotly.react('plotC1', [
    { x: tc, y: lMapp, mode: 'lines', line: { width: 2.6, color: '#3b82f6' },
      name: 'PS conventional calibration' },
    { x: tc, y: lMtrue, mode: 'lines', line: { width: 2.6, color: '#ef4444', dash: 'dash' },
      name: 'Sample true MW', fill: 'tonexty', fillcolor: 'rgba(239,68,68,0.12)' },
    { x: ts, y: stdY, mode: 'markers', marker: { color: '#3b82f6', size: 8 },
      name: 'PS standards' }
  ], L1, { displayModeBar: true, responsive: true });
  var L2 = themed('Level 2 — universal: one line fits all');
  L2.xaxis.title = 'elution time (min)'; L2.yaxis.title = 'log\\u2081\\u2080([\\u03b7]·M)';
  L2.height = 400; L2.showlegend = false;
  Plotly.react('plotC2', [
    { x: tc, y: lVh, mode: 'lines', line: { width: 2.6, color: '#10b981' } }
  ], L2, { displayModeBar: true, responsive: true });
  var t0 = 9.0;
  var mApp = Math.pow(10, (Au - Math.log10(K)) / (1 + a_ps) - Bu * t0 / (1 + a_ps));
  var mTrue = Math.pow(10, (Au - Bu * t0 - Math.log10(K)) / (1 + as));
  var err = (mApp / mTrue - 1) * 100;
  document.getElementById('calM').innerHTML =
    '<div class="mbox"><div class="k">At t = 9 min, conventional reads</div>' +
    '<div class="n">' + fmtInt(mApp) + ' g/mol</div></div>' +
    '<div class="mbox"><div class="k">True molecular weight there</div>' +
    '<div class="n">' + fmtInt(mTrue) + ' g/mol</div>' +
    '<div class="d">' + (err >= 0 ? '+' : '') + err.toFixed(0) + '% error</div></div>';
}
IDS.forEach(bindSlider);
onThemeChange();
draw();
"""


SEP_JS = """/* Separation widget: bands moving down the column + chromatogram drawn live. */
var IDS = ['etime'];
var BAND_V = [0.95, 0.62, 0.38];
var BAND_C = ['#ef4444', '#f59e0b', '#3b82f6'];
var BAND_N = ['large', 'medium', 'small'];
var TMAX = 3.4;
var NT = 600, tg = [], trace = [];
(function init() {
  var tel = BAND_V.map(function(v) { return 1 / v; });
  for (var i = 0; i < NT; i++) {
    var t = TMAX * i / (NT - 1); tg.push(t);
    var s = 0, j;
    for (j = 0; j < tel.length; j++) s += Math.exp(-0.5 * Math.pow((t - tel[j]) / 0.13, 2));
    trace.push(s);
  }
})();
var playing = false;
function draw() {
  IDS.forEach(refreshSlider);
  var t = sval('etime');
  var bh = '';
  BAND_V.forEach(function(v, i) {
    var y = 1 - v * t;
    if (y > 0.02) {
      var pct = ((1 - y) * 100).toFixed(2);
      bh += '<div class="band" style="top:calc(' + pct + '% - 9px);background:' + BAND_C[i] + '"></div>' +
            '<div class="blab" style="top:calc(' + pct + '% - 9px);color:' + BAND_C[i] + '">' +
            BAND_N[i] + '</div>';
    }
  });
  document.getElementById('colBands').innerHTML = bh;
  var rev = trace.map(function(v, i) { return tg[i] <= t ? v : null; });
  var annot = [];
  BAND_V.forEach(function(v, i) {
    var te = 1 / v;
    if (t >= te - 0.03) annot.push({ x: te, y: 1.22, text: BAND_N[i] + ' chains',
      showarrow: false, font: { color: BAND_C[i], size: 11 } });
  });
  var ink = isDark() ? '#e8eaf0' : '#0f172a';
  var L = themed('Chromatogram being recorded');
  L.xaxis.title = 'time →'; L.xaxis.range = [0, TMAX];
  L.yaxis.title = 'detector signal'; L.yaxis.range = [0, 1.4];
  L.height = 400;
  L.shapes = [{ type: 'line', x0: t, x1: t, y0: 0, y1: 1.4,
                line: { dash: 'dash', color: ink, width: 1 } }];
  L.annotations = annot;
  Plotly.react('plotS', [
    { x: tg, y: trace, mode: 'lines', line: { width: 1.4, color: '#94a3b8' },
      opacity: 0.55, showlegend: false },
    { x: tg, y: rev, mode: 'lines', line: { width: 2.6, color: ink },
      fill: 'tozeroy', fillcolor: 'rgba(120,130,150,0.15)', showlegend: false }
  ], L, { displayModeBar: true, responsive: true });
}
function setPlaying(p) {
  playing = p;
  document.getElementById('playBtn').innerHTML = playing ? '\\u23F8 Pause' : '\\u25B6 Play';
  if (playing) requestAnimationFrame(tick);
}
function tick() {
  if (!playing) return;
  var el = document.getElementById('s_etime');
  var t = parseFloat(el.value) + TMAX / 220;
  if (t >= TMAX) { el.value = TMAX; draw(); setPlaying(false); return; }
  el.value = t; draw();
  requestAnimationFrame(tick);
}
document.getElementById('playBtn').addEventListener('click', function() {
  if (!playing && parseFloat(document.getElementById('s_etime').value) >= TMAX)
    document.getElementById('s_etime').value = 0;
  setPlaying(!playing);
});
IDS.forEach(bindSlider);
IDS.forEach(function(id) {
  document.getElementById('s_' + id).addEventListener('input', function() { setPlaying(false); });
});
onThemeChange();
draw();
"""


# ----------------------------------------------------------------------------
# Live widget scaffolding.
# Each widget below is a self-contained HTML page (sliders + Plotly.js plots)
# rendered with components.html. Dragging a slider recomputes and redraws the
# plots inside the browser at 60 fps with no server round-trip. The sliders
# mimic the native Streamlit style, and every widget follows the OS
# light/dark mode via prefers-color-scheme.
# ----------------------------------------------------------------------------

def wslider(sid, label, vmin, vmax, step, value, dec):
    """One Streamlit-styled slider row for a live widget side panel."""
    return (
        '<div class="sld"><div class="labrow"><span class="t">' + label + "</span>"
        '<span class="v" id="o_' + sid + '"></span></div>'
        '<input id="s_' + sid + '" type="range" min="' + str(vmin) + '" max="' + str(vmax)
        + '" step="' + str(step) + '" value="' + str(value) + '" data-dec="' + str(dec) + '"></div>'
    )


def widget_page(side, main, script):
    """Wrap side-panel HTML, main-plot HTML, and JS into a full widget page."""
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap"'
        ' rel="stylesheet">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        "<style>" + WIDGET_CSS + "</style></head><body>"
        '<div class="wrap"><div class="side">' + side + "</div>"
        '<div class="main">' + main + "</div></div>"
        "<script>" + SHARED_JS + script + "</script></body></html>"
    )


W_SEP = widget_page(
    wslider("etime", "Time", 0.0, 3.4, 0.02, 0.0, 2)
    + '<button id="playBtn" class="pbtn">\u25b6 Play</button>',
    '<div class="sepmain"><div class="colwrap"><div class="coltitle">column</div>'
    '<div class="colbody" id="colBands"></div><div class="colflow">flow \u2193</div></div>'
    '<div id="plotS" class="flexplot"></div></div>',
    SEP_JS,
)

W_CHROM = widget_page(
    wslider("logMnA", "Sample A: Mn (log\u2081\u2080 g/mol)", 3.0, 6.5, 0.05, 5.0, 2)
    + '<div class="cap" id="capA"></div>'
    + wslider("DA", "Sample A: dispersity \u00d0 = Mw/Mn", 1.05, 3.0, 0.05, 1.5, 2)
    + '<label class="chk"><input type="checkbox" id="c_showB"> Compare with sample B</label>'
    + '<div id="rowB" style="display:none">'
    + wslider("logMnB", "Sample B: Mn (log\u2081\u2080 g/mol)", 3.0, 6.5, 0.05, 4.7, 2)
    + '<div class="cap" id="capB"></div>'
    + wslider("DB", "Sample B: dispersity \u00d0 = Mw/Mn", 1.05, 3.0, 0.05, 2.2, 2)
    + "</div>"
    + '<div class="mgrid" id="mA"></div>'
    + '<div class="mgrid" id="mB"></div>',
    '<div id="plotC"></div>',
    CHROM_JS,
)

W_DET = widget_page(
    wslider("mhA", "Mark\u2013Houwink exponent a (chain stiffness)", 0.3, 1.0, 0.05, 0.7, 2)
    + '<div class="cap">a \u2248 0.5: compact coil \u00b7 a \u2248 0.7\u20130.8: expanded coil in a good '
    "solvent \u00b7 a \u2192 1: stiff rod</div>",
    '<div id="plotD"></div><div class="note" id="detNote"></div>',
    DET_JS,
)

W_CAL = widget_page(
    wslider(
        "calA",
        "Sample's Mark\u2013Houwink exponent a (polystyrene standards: a = 0.7)",
        0.5, 0.95, 0.05, 0.6, 2,
    )
    + '<div class="cap">Move the slider: the further your polymer\u2019s coil behavior is from '
    "polystyrene\u2019s, the more conventional calibration misreads it. (K held equal for "
    "illustration.)</div>"
    + '<div class="mgrid" id="calM" style="flex-direction:column"></div>',
    '<div class="calmain"><div id="plotC1"></div><div id="plotC2"></div></div>',
    CAL_JS,
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


@st.fragment
def frag_tab_sep():
        st.header("Separation: big = fast, small = slow")
        st.write(
            "The beads are full of pores, and ideally nothing sticks — separation is purely by size. "
            "Chains too big for the pores stay in the fast lane; chains that fit take the scenic route."
        )
        st.pyplot(pore_figure())
        st.subheader("Watch it happen")
        st.write(
            "Scrub through time \u2014 the bands separate inside the column while the detector "
            "draws the chromatogram, all in real time. Hit play to animate it."
        )
        components.html(W_SEP, height=520, scrolling=False)
        st.info(
            "Notice the elution order: **large → medium → small**. "
            "This is backwards from most chromatography, where bigger things usually come out later."
        )


with tab_sep:
    frag_tab_sep()

# ----------------------------------------------------------------------------
# Tab 3: Chromatogram lab
# ----------------------------------------------------------------------------
@st.fragment
def frag_tab_chrom():
        st.header("Chromatogram lab")
        st.write(
            "Dial in a molecular-weight distribution and watch the chromatogram it produces. "
            "The distribution is log-normal — the standard model for polymer samples."
        )
        components.html(W_CHROM, height=520, scrolling=False)
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
        components.html(W_DET, height=800, scrolling=False)



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
        components.html(W_CAL, height=560, scrolling=False)
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
