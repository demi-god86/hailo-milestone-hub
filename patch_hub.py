import os, subprocess, tempfile

p = os.path.expanduser('~/Claude/milestone-hub/frontend/index.html')
with open(p,'r',encoding='utf-8') as f:
    h = f.read()

print('Original size:', len(h))
if 'openMilestonesModal' in h:
    print('Already patched')
    exit()

# ── 1. CSS ─────────────────────────────────────────────────────────────────
css = """
/* Peek + expand */
.peek-wrap{position:relative;overflow:hidden;border-radius:14px;margin-bottom:4px}
.peek-fade{position:absolute;bottom:0;left:0;right:0;height:60px;background:linear-gradient(to bottom,transparent,#0A1628);pointer-events:none;border-radius:0 0 14px 14px}
.expand-btn{width:100%;padding:11px;border-radius:12px;border:1px solid rgba(77,163,255,0.2);background:rgba(77,163,255,0.04);color:rgba(77,163,255,0.6);font-size:12px;font-weight:700;cursor:pointer;font-family:Arial,sans-serif;transition:all 0.2s;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:6px}
.expand-btn:hover{border-color:rgba(77,163,255,0.45);color:#4DA3FF;background:rgba(30,111,255,0.08)}
/* History modals */
.hist-overlay{display:none;position:fixed;inset:0;background:rgba(5,12,28,0.88);z-index:500;align-items:flex-start;justify-content:center;padding:40px 20px;backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}
.hist-overlay.open{display:flex}
.hist-panel{background:#0D1F3C;border:1px solid rgba(77,163,255,0.25);border-radius:18px;width:100%;max-width:600px;max-height:calc(100vh - 80px);display:flex;flex-direction:column;animation:hpIn 0.25s ease;overflow:hidden}
@keyframes hpIn{from{opacity:0;transform:translateY(-14px) scale(0.97)}to{opacity:1;transform:translateY(0) scale(1)}}
.hist-header{display:flex;align-items:center;justify-content:space-between;padding:1.25rem 1.5rem;border-bottom:1px solid rgba(255,255,255,0.07);flex-shrink:0}
.hist-htitle{font-size:16px;font-weight:900;color:#fff}
.hist-hsub{font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px}
.hist-close{width:32px;height:32px;border-radius:50%;border:1px solid rgba(255,255,255,0.12);background:transparent;color:rgba(255,255,255,0.4);font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;flex-shrink:0}
.hist-close:hover{border-color:rgba(255,255,255,0.3);color:#fff;background:rgba(255,255,255,0.06)}
.hist-body{overflow-y:auto;padding:1.25rem 1.5rem;flex:1}
.hist-body::-webkit-scrollbar{width:4px}
.hist-body::-webkit-scrollbar-thumb{background:rgba(77,163,255,0.2);border-radius:2px}
.hist-footer{padding:1rem 1.5rem;border-top:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.hist-fnote{font-size:11px;color:rgba(255,255,255,0.2)}
.hist-collapse{padding:8px 18px;border-radius:50px;border:1px solid rgba(255,255,255,0.15);background:transparent;color:rgba(255,255,255,0.5);font-size:12px;font-weight:700;cursor:pointer;font-family:Arial,sans-serif;transition:all 0.15s}
.hist-collapse:hover{border-color:rgba(255,255,255,0.35);color:#fff}
/* Comms cards on hub */
.cc-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:14px;margin-bottom:8px;overflow:hidden;transition:border-color 0.15s}
.cc-card:hover{border-color:rgba(77,163,255,0.25)}
.cc-row{display:flex;align-items:stretch;cursor:pointer}
.cc-ds{background:rgba(77,163,255,0.12);border-right:1px solid rgba(77,163,255,0.2);padding:0 14px;min-width:56px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px}
.cc-inner{display:flex;align-items:center;gap:1rem;flex:1;padding:1rem 1.25rem}
.cc-body{flex:1;min-width:0}
.cc-type{font-size:16px;font-weight:700;color:#fff}
.cc-count{font-size:12px;color:rgba(255,255,255,0.3);margin-top:2px}
.cc-chev{font-size:11px;color:rgba(255,255,255,0.2);flex-shrink:0;transition:transform 0.2s}
.cc-chev.open{transform:rotate(180deg);color:rgba(77,163,255,0.6)}
.cc-tray{display:none;border-top:1px solid rgba(255,255,255,0.05);padding:8px 14px 10px 88px;flex-direction:column;gap:6px}
.cc-tray.open{display:flex}
.cc-entry{display:flex;align-items:center;gap:8px;font-size:13px;color:rgba(255,255,255,0.75)}
.cc-link{font-size:11px;color:#4DA3FF;margin-left:auto;text-decoration:none;white-space:nowrap}
.cc-link:hover{text-decoration:underline}
"""
h = h.replace('</style>', css + '\n</style>', 1)

# ── 2. Add modal overlays + section divider before </body> ─────────────────
modals = """
<!-- Milestones history modal -->
<div class="hist-overlay" id="ms-modal" onclick="if(event.target===this)closeMsModal()">
  <div class="hist-panel">
    <div class="hist-header">
      <div><div class="hist-htitle">All Milestones</div><div class="hist-hsub" id="ms-modal-sub"></div></div>
      <button class="hist-close" onclick="closeMsModal()">&#x2715;</button>
    </div>
    <div class="hist-body" id="ms-modal-body"></div>
    <div class="hist-footer">
      <span class="hist-fnote" id="ms-modal-note"></span>
      <button class="hist-collapse" onclick="closeMsModal()">&#8593; Collapse</button>
    </div>
  </div>
</div>

<!-- Comms history modal -->
<div class="hist-overlay" id="cc-modal" onclick="if(event.target===this)closeCcModal()">
  <div class="hist-panel">
    <div class="hist-header">
      <div><div class="hist-htitle">Comms History</div><div class="hist-hsub" id="cc-modal-sub"></div></div>
      <button class="hist-close" onclick="closeCcModal()">&#x2715;</button>
    </div>
    <div class="hist-body" id="cc-modal-body"></div>
    <div class="hist-footer">
      <span class="hist-fnote" id="cc-modal-note"></span>
      <button class="hist-collapse" onclick="closeCcModal()">&#8593; Collapse</button>
    </div>
  </div>
</div>
</body>"""
h = h.replace('</body>', modals)

# ── 3. Patch render() to show 4 milestones + peek + expand button ──────────
# Add section divider + comms section after the milestone list div
old_footer = '<div class="footer">'
new_footer = (
    '<div class="section-label" id="comms-label" style="display:none">Communications</div>\n'
    '<div class="milestone-list" id="comms-list" style="padding-bottom:0"></div>\n'
    '<div class="milestone-list" style="padding-top:0;padding-bottom:4rem" id="comms-expand-wrap" style="display:none"></div>\n'
    '<div class="footer">'
)
h = h.replace(old_footer, new_footer, 1)

# ── 4. Patch the render() function to add peek + expand for milestones ─────
old_render_end = """  list.innerHTML='';
  ms.forEach(function(m,i){"""

new_render_end = """  list.innerHTML='';
  var SHOW=4;
  ms.forEach(function(m,i){"""

h = h.replace(old_render_end, new_render_end)

# After list.appendChild(a), add peek logic
old_append = '    list.appendChild(a);\n  });'
new_append = """    a.style.display = (i < SHOW) ? '' : 'none';
    list.appendChild(a);
  });
  // Peek card (the one just after the 4 visible)
  var peekWrap = document.getElementById('ms-peek');
  if(peekWrap) peekWrap.remove();
  if(ms.length > SHOW){
    var pw = document.createElement('div');
    pw.id = 'ms-peek';
    pw.className = 'milestone-list';
    pw.style.cssText = 'padding:0 2rem 0;';
    var peekCard = ms[SHOW];
    var pd = new Date(peekCard.date);
    var pday = pd.getDate();
    var pmon = pd.toLocaleDateString('en-GB',{month:'short'});
    var pyr = pd.getFullYear();
    var pscores = countPlayers(scores, peekCard.id);
    var pa = document.createElement('div');
    pa.className = 'peek-wrap';
    var inner = document.createElement('a');
    inner.href = 'game.html?id='+encodeURIComponent(peekCard.id);
    inner.className = 'card';
    inner.style.cssText = 'opacity:0.3;pointer-events:none;margin-bottom:0';
    inner.innerHTML =
      '<div class="date-stripe">'+
        '<div class="ds-day">'+pday+'</div>'+
        '<div class="ds-mon">'+pmon+'</div>'+
        '<div class="ds-yr">'+pyr+'</div>'+
      '</div>'+
      '<div class="card-inner">'+
        '<div class="card-icon">&#9989;</div>'+
        '<div class="card-body">'+
          '<div class="card-cat">'+peekCard.category+'</div>'+
          (pscores ? '<div class="card-players">'+pscores+' player'+(pscores!==1?'s':'')+' solved this</div>' : '')+
        '</div>'+
        '<div class="btn">'+(peekCard.cta||'Crack It')+'</div>'+
      '</div>';
    pa.appendChild(inner);
    var fade = document.createElement('div');
    fade.className = 'peek-fade';
    pa.appendChild(fade);
    pw.appendChild(pa);
    var expandBtn = document.createElement('button');
    expandBtn.className = 'expand-btn';
    expandBtn.innerHTML = '&#128081; View all milestones &nbsp;&middot;&nbsp; '+(ms.length-SHOW)+' more';
    expandBtn.onclick = function(){ openMsModal(ms, scores); };
    pw.appendChild(expandBtn);
    list.parentNode.insertBefore(pw, list.nextSibling);
  }"""
h = h.replace(old_append, new_append)

# ── 5. Add comms rendering after milestones ────────────────────────────────
old_render_close = "  list.innerHTML='';\n  if(!ms.length){"
# Find the end of the render function — after the confetti/modal JS
# Insert commsRender call at the end of the main fetch callback
old_fetch_render = 'render(cached.d);\n      fetchFresh(function(fresh){render(fresh);});\n      return;'
new_fetch_render = 'render(cached.d);\n      fetchFresh(function(fresh){render(fresh);renderComms(fresh);});\n      return;'
h = h.replace(old_fetch_render, new_fetch_render)

old_fresh = 'fetchFresh(function(data){render(data);});'
new_fresh = 'fetchFresh(function(data){render(data);renderComms(data);});'
h = h.replace(old_fresh, new_fresh)

# ── 6. Add new JS functions before </script> ──────────────────────────────
new_js = """
// ── Comms on hub ───────────────────────────────────────────────────────────
function renderComms(record){
  var groups = (record && record.commsGroups||[]).slice().sort(function(a,b){return new Date(b.date)-new Date(a.date);});
  var lbl = document.getElementById('comms-label');
  var list = document.getElementById('comms-list');
  var wrap = document.getElementById('comms-expand-wrap');
  if(!groups.length){ if(lbl)lbl.style.display='none'; return; }
  if(lbl)lbl.style.display='';

  // Section divider
  list.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin:4px 0 12px"><div style="flex:1;height:1px;background:rgba(255,255,255,0.06)"></div><div style="font-size:9px;font-weight:700;color:rgba(255,255,255,0.2);text-transform:uppercase;letter-spacing:2px;padding:2px 10px;border:1px solid rgba(255,255,255,0.07);border-radius:50px;white-space:nowrap">Latest Comms</div><div style="flex:1;height:1px;background:rgba(255,255,255,0.06)"></div></div>';

  var SHOW = 4;
  var shown = groups.slice(0, SHOW);
  shown.forEach(function(g){ list.appendChild(buildCcCard(g)); });

  // Peek + expand
  wrap.innerHTML = '';
  if(groups.length > SHOW){
    var peek = groups[SHOW];
    var pw = document.createElement('div');
    pw.className = 'peek-wrap';
    var pc = buildCcCard(peek);
    pc.style.cssText = 'opacity:0.3;pointer-events:none;margin-bottom:0';
    pw.appendChild(pc);
    var fade = document.createElement('div');
    fade.className = 'peek-fade';
    pw.appendChild(fade);
    wrap.appendChild(pw);
    var btn = document.createElement('button');
    btn.className = 'expand-btn';
    btn.innerHTML = '&#128240; View full comms history &nbsp;&middot;&nbsp; '+(groups.length-SHOW)+' more';
    btn.onclick = function(){ openCcModal(groups); };
    wrap.appendChild(btn);
    wrap.style.display = '';
  } else {
    wrap.style.display = 'none';
  }
}

function buildCcCard(g){
  var dt = new Date(g.date);
  var day = dt.getDate();
  var mon = dt.toLocaleDateString('en-GB',{month:'short'});
  var yr = dt.getFullYear();
  var entries = g.entries||[];
  var card = document.createElement('div');
  card.className = 'cc-card';
  var rowHtml = entries.map(function(e){
    return '<div class="cc-entry">&#128196; '+escHtml(e.title)+(e.url?'<a class="cc-link" href="'+escHtml(e.url)+'" target="_blank" rel="noopener">View PDF</a>':'')+'</div>';
  }).join('');
  card.innerHTML =
    '<div class="cc-row" onclick="toggleCcCard(this)">'+
      '<div class="cc-ds">'+
        '<div class="ds-day">'+day+'</div>'+
        '<div class="ds-mon">'+mon+'</div>'+
        '<div class="ds-yr">'+yr+'</div>'+
      '</div>'+
      '<div class="cc-inner">'+
        '<div class="cc-body">'+
          '<div class="cc-type">'+escHtml(g.type)+'</div>'+
          '<div class="cc-count">'+entries.length+' document'+(entries.length!==1?'s':'')+'</div>'+
        '</div>'+
        '<span class="cc-chev">&#9660;</span>'+
      '</div>'+
    '</div>'+
    '<div class="cc-tray">'+rowHtml+'</div>';
  return card;
}

function toggleCcCard(row){
  var tray = row.parentElement.querySelector('.cc-tray');
  var chev = row.querySelector('.cc-chev');
  if(!tray) return;
  var open = tray.classList.contains('open');
  tray.classList.toggle('open',!open);
  if(chev) chev.classList.toggle('open',!open);
}

function escHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

// ── Milestones modal ────────────────────────────────────────────────────────
function openMsModal(ms, scores){
  var body = document.getElementById('ms-modal-body');
  var sub = document.getElementById('ms-modal-sub');
  var note = document.getElementById('ms-modal-note');
  sub.textContent = 'All ' + ms.length + ' milestones';
  note.textContent = ms.length + ' milestones total';
  body.innerHTML = '';
  ms.forEach(function(m,i){
    var players = countPlayers(scores, m.id);
    var d = new Date(m.date);
    var day = d.getDate();
    var mon = d.toLocaleDateString('en-GB',{month:'short'});
    var yr = d.getFullYear();
    var a = document.createElement('a');
    a.href = 'game.html?id='+encodeURIComponent(m.id);
    a.className = 'card';
    a.style.marginBottom = '10px';
    a.innerHTML =
      '<div class="date-stripe">'+
        '<div class="ds-day">'+day+'</div>'+
        '<div class="ds-mon">'+mon+'</div>'+
        '<div class="ds-yr">'+yr+'</div>'+
      '</div>'+
      '<div class="card-inner">'+
        '<div class="card-icon">'+(i===0?'&#128274;':'&#9989;')+'</div>'+
        '<div class="card-body">'+
          '<div class="card-cat">'+m.category+(i===0?'<span class="badge">New</span>':'')+'</div>'+
          (players?'<div class="card-players">'+players+' player'+(players!==1?'s':'')+' solved this</div>':'<div class="card-players">Be the first to crack it</div>')+
        '</div>'+
        '<div class="btn">'+(m.cta||'Crack It')+'</div>'+
      '</div>'+
      '<div class="skip-stripe" data-num="'+encodeURIComponent(m.number||'')+'" data-lbl="'+encodeURIComponent(m.label||m.category||'')+'" onclick="event.preventDefault();event.stopPropagation();quickReveal(this)">'+
        '<div class="skip-flag">&#127987;</div>'+
        '<div class="skip-txt">Just<br/>tell me</div>'+
      '</div>';
    body.appendChild(a);
  });
  document.getElementById('ms-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeMsModal(){
  document.getElementById('ms-modal').classList.remove('open');
  document.body.style.overflow = '';
}

// ── Comms modal ─────────────────────────────────────────────────────────────
function openCcModal(groups){
  var body = document.getElementById('cc-modal-body');
  var sub = document.getElementById('cc-modal-sub');
  var note = document.getElementById('cc-modal-note');
  sub.textContent = 'All communications · ' + groups.length + ' total';
  note.textContent = groups.length + ' communications total';
  body.innerHTML = '';
  groups.forEach(function(g){ body.appendChild(buildCcCard(g)); });
  document.getElementById('cc-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeCcModal(){
  document.getElementById('cc-modal').classList.remove('open');
  document.body.style.overflow = '';
}"""

close_pos = h.rfind('</script>')
h = h[:close_pos] + new_js + '\n</script>' + h[close_pos+9:]

# ── 7. Validate JS ──────────────────────────────────────────────────────────
script_open = h.rfind('<script>') + 8
script_close = h.rfind('</script>')
js = h[script_open:script_close]
with tempfile.NamedTemporaryFile(mode='w',suffix='.js',delete=False,encoding='utf-8') as tf:
    tf.write(js); tname=tf.name
result = subprocess.run(['node','--check',tname],capture_output=True,text=True)
os.unlink(tname)
if result.returncode != 0:
    print('JS SYNTAX ERROR - not saving:')
    print(result.stderr[:400])
    exit(1)

with open(p,'w',encoding='utf-8') as f:
    f.write(h)
print('Saved OK, size:', len(h))
print('openMsModal:', 'openMsModal' in h)
print('openCcModal:', 'openCcModal' in h)
print('peek-wrap:', 'peek-wrap' in h)
print('hist-overlay:', 'hist-overlay' in h)
