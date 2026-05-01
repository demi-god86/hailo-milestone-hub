import os, subprocess, tempfile

p = os.path.expanduser('~/Claude/milestone-hub/frontend/admin.html')
with open(p,'r',encoding='utf-8') as f:
    h = f.read()

if 'switchTab' in h:
    print('Already patched')
    exit()

print('Original size:', len(h))

# ── 1. CSS ────────────────────────────────────────────────────────────────
css = [
    '.tab-nav{display:flex;gap:4px;padding:1rem 1.5rem 0;border-bottom:1px solid rgba(255,255,255,0.08)}',
    '.tab-nav-btn{padding:10px 22px;border-radius:8px 8px 0 0;border:1px solid rgba(255,255,255,0.08);border-bottom:none;background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.4);font-size:13px;font-weight:700;cursor:pointer;font-family:Arial,sans-serif;transition:all 0.15s;position:relative;bottom:-1px}',
    '.tab-nav-btn:hover{background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.7)}',
    '.tab-nav-btn.active{background:#0D1F3C;border-color:rgba(77,163,255,0.35);color:#4DA3FF}',
    '.tab-panel{display:none}',
    '.tab-panel.active{display:block}',
    '.cg-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin-bottom:12px;overflow:hidden}',
    '.cg-head{display:flex;align-items:center;gap:1rem;padding:1rem 1.25rem}',
    '.cg-info{flex:1;min-width:0}',
    '.cg-date{font-size:15px;font-weight:700;color:#fff}',
    '.cg-type{font-size:12px;color:#4DA3FF;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-top:2px}',
    '.cg-acts{display:flex;gap:8px;flex-shrink:0}',
    '.ce-list{border-top:1px solid rgba(255,255,255,0.06);padding:0.5rem 1.25rem}',
    '.ce-row{display:flex;align-items:center;gap:0.75rem;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)}',
    '.ce-row:last-child{border-bottom:none}',
    '.ce-title{flex:1;font-size:13px;color:rgba(255,255,255,0.8)}',
    '.ce-acts{display:flex;gap:6px;flex-shrink:0}',
    '.ce-add{padding:0.5rem 1.25rem 0.75rem}',
    '.ce-add-btn{padding:5px 14px;border-radius:50px;background:transparent;border:1px dashed rgba(77,163,255,0.3);color:rgba(77,163,255,0.55);font-size:11px;font-weight:700;cursor:pointer;font-family:Arial,sans-serif;transition:all 0.15s}',
    '.ce-add-btn:hover{border-color:#4DA3FF;color:#4DA3FF}',
    '.cg-empty{text-align:center;color:rgba(255,255,255,0.25);font-size:13px;padding:2rem}',
]
h = h.replace('</style>', '\n' + '\n'.join(css) + '\n</style>', 1)

# ── 2. Tab nav + wrap milestones panel ───────────────────────────────────
tab_nav = (
    '<div class="tab-nav">'
    '<button class="tab-nav-btn active" onclick="switchTab(\'milestones\',this)">Milestones</button>'
    '<button class="tab-nav-btn" onclick="switchTab(\'comms\',this)">Comms</button>'
    '</div>'
    '<div id="tab-milestones" class="tab-panel active">'
)
h = h.replace('<div class="wrap">', tab_nav + '<div class="wrap">', 1)

# ── 3. Close milestones panel + add comms panel before <script> ──────────
comms_panel = (
    '</div></div>\n'
    '<div id="tab-comms" class="tab-panel">\n'
    '  <div class="wrap" style="max-width:700px">\n'
    '    <div class="section-title" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem">'
    '<span>Comms</span>'
    '<button class="btn-save" style="width:auto;padding:10px 20px" onclick="openCG(null)">+ New Date</button>'
    '</div>\n'
    '    <div id="comms-list"><div class="loading"><div class="spinner"></div></div></div>\n'
    '  </div>\n'
    '</div>\n'
)
script_pos = h.rfind('<script>')
h = h[:script_pos] + comms_panel + h[script_pos:]

# ── 4. Build comms JS using list of lines (no triple-quote issues) ────────
# Use double quotes throughout JS to avoid any single-quote escaping conflicts
js_lines = [
    'function switchTab(n,b){',
    '  document.querySelectorAll(".tab-panel").forEach(function(p){p.classList.remove("active");});',
    '  document.querySelectorAll(".tab-nav-btn").forEach(function(x){x.classList.remove("active");});',
    '  document.getElementById("tab-"+n).classList.add("active");',
    '  b.classList.add("active");',
    '  if(n==="comms")renderCG();',
    '}',
    'var _cgId=null,_ceId=null,_ceGId=null;',
    'function escH(s){return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}',
    'function renderCG(){',
    '  var gs=(_data.commsGroups||[]).slice().sort(function(a,b){return new Date(b.date)-new Date(a.date);});',
    '  var el=document.getElementById("comms-list");',
    '  if(!gs.length){el.innerHTML="<div class=\\"cg-empty\\">No comms yet.</div>";return;}',
    '  el.innerHTML="";',
    '  gs.forEach(function(g){',
    '    var en=g.entries||[];',
    '    var ds=new Date(g.date).toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"});',
    '    var card=document.createElement("div");',
    '    card.className="cg-card";',
    '    var rows=en.map(function(e){',
    '      return "<div class=\\"ce-row\\">"',
    '        +"<div class=\\"ce-title\\">"+escH(e.title)+"</div>"',
    '        +(e.url?"<a href=\\""+escH(e.url)+"\\" target=\\"_blank\\" style=\\"font-size:11px;color:#4DA3FF;text-decoration:none;white-space:nowrap;margin-right:6px\\">View PDF</a>":"")',
    '        +"<div class=\\"ce-acts\\">"',
    '        +"<button class=\\"btn-edit\\" onclick=\\"openCE(\'"+g.id+"\',\'"+e.id+"\')\\" >Edit</button>"',
    '        +"<button class=\\"btn-del\\" onclick=\\"delCE(\'"+g.id+"\',\'"+e.id+"\')\\" >Del</button>"',
    '        +"</div></div>";',
    '    }).join("");',
    '    card.innerHTML=',
    '      "<div class=\\"cg-head\\">"',
    '      +"<div class=\\"cg-info\\"><div class=\\"cg-date\\">"+escH(ds)+"</div><div class=\\"cg-type\\">"+escH(g.type)+"</div></div>"',
    '      +"<div class=\\"cg-acts\\">"',
    '      +"<button class=\\"btn-edit\\" onclick=\\"openCG(\'"+g.id+"\')\\" >Edit</button>"',
    '      +"<button class=\\"btn-del\\" onclick=\\"delCG(\'"+g.id+"\')\\" >Delete</button>"',
    '      +"</div></div>"',
    '      +(en.length?"<div class=\\"ce-list\\">"+rows+"</div>":"")',
    '      +"<div class=\\"ce-add\\"><button class=\\"ce-add-btn\\" onclick=\\"openCE(\'"+g.id+"\',null)\\" >+ Add document</button></div>";',
    '    el.appendChild(card);',
    '  });',
    '}',
    'function openCG(id){',
    '  _cgId=id;',
    '  var g=id?(_data.commsGroups||[]).find(function(x){return x.id===id;}):null;',
    '  var m=document.createElement("div");',
    '  m.className="modal-overlay";m.id="cmodal";',
    '  m.innerHTML="<div class=\\"modal-box\\" style=\\"max-width:420px\\">"',
    '    +"<div class=\\"modal-title\\">"+(g?"Edit":"New")+" Comms Date</div>"',
    '    +"<div class=\\"field\\"><label class=\\"field-label\\">Date</label>"',
    '    +"<input type=\\"date\\" id=\\"cgd\\" class=\\"field-input\\" value=\\"'
    '"+(g?g.date:new Date().toISOString().slice(0,10))+"\\">"',
    '    +"<div class=\\"field\\"><label class=\\"field-label\\">Comms Type</label>"',
    '    +"<input type=\\"text\\" id=\\"cgt\\" class=\\"field-input\\" placeholder=\\"e.g. Regular Update\\" value=\\""+escH(g?g.type:"")+"\\">"',
    '    +"<div class=\\"modal-btns\\">"',
    '    +"<button class=\\"modal-cancel\\" onclick=\\"rmCM()\\">Cancel</button>"',
    '    +"<button class=\\"modal-save\\" onclick=\\"saveCG()\\">Save</button>"',
    '    +"</div></div>";',
    '  m.addEventListener("click",function(e){if(e.target===m)rmCM();});',
    '  document.body.appendChild(m);',
    '}',
    'function rmCM(){var m=document.getElementById("cmodal");if(m)m.remove();}',
    'async function saveCG(){',
    '  var d=document.getElementById("cgd").value;',
    '  var t=document.getElementById("cgt").value.trim();',
    '  if(!d||!t){alert("Fill in both fields.");return;}',
    '  if(!_data.commsGroups)_data.commsGroups=[];',
    '  if(_cgId){',
    '    var g=_data.commsGroups.find(function(x){return x.id===_cgId;});',
    '    if(g){g.date=d;g.type=t;}',
    '  } else {',
    '    _data.commsGroups.push({id:"cg-"+Date.now(),date:d,type:t,entries:[]});',
    '  }',
    '  await save();rmCM();renderCG();toast("Saved!");',
    '}',
    'async function delCG(id){',
    '  if(!confirm("Delete this date and all documents?"))return;',
    '  _data.commsGroups=(_data.commsGroups||[]).filter(function(g){return g.id!==id;});',
    '  await save();renderCG();toast("Deleted");',
    '}',
    'function openCE(gId,eId){',
    '  _ceGId=gId;_ceId=eId;',
    '  var g=(_data.commsGroups||[]).find(function(x){return x.id===gId;});',
    '  var e=eId&&g?(g.entries||[]).find(function(x){return x.id===eId;}):null;',
    '  var m=document.createElement("div");',
    '  m.className="modal-overlay";m.id="cmodal";',
    '  m.innerHTML="<div class=\\"modal-box\\" style=\\"max-width:420px\\">"',
    '    +"<div class=\\"modal-title\\">"+(e?"Edit":"Add")+" Document</div>"',
    '    +"<div class=\\"field\\"><label class=\\"field-label\\">Title</label>"',
    '    +"<input type=\\"text\\" id=\\"cet\\" class=\\"field-input\\" placeholder=\\"e.g. Live Customers\\" value=\\""+escH(e?e.title:"")+"\\">"',
    '    +"<div class=\\"field\\"><label class=\\"field-label\\">Google Drive Link</label>"',
    '    +"<input type=\\"url\\" id=\\"ceu\\" class=\\"field-input\\" placeholder=\\"https://drive.google.com/...\\" value=\\""+escH(e&&e.url?e.url:"")+"\\">"',
    '    +"<div class=\\"modal-btns\\">"',
    '    +"<button class=\\"modal-cancel\\" onclick=\\"rmCM()\\">Cancel</button>"',
    '    +"<button class=\\"modal-save\\" onclick=\\"saveCE()\\">Save</button>"',
    '    +"</div></div>";',
    '  m.addEventListener("click",function(e){if(e.target===m)rmCM();});',
    '  document.body.appendChild(m);',
    '}',
    'async function saveCE(){',
    '  var t=document.getElementById("cet").value.trim();',
    '  var u=document.getElementById("ceu").value.trim();',
    '  if(!t){alert("Add a title.");return;}',
    '  var g=(_data.commsGroups||[]).find(function(x){return x.id===_ceGId;});',
    '  if(!g)return;',
    '  if(!g.entries)g.entries=[];',
    '  if(_ceId){',
    '    var e=g.entries.find(function(x){return x.id===_ceId;});',
    '    if(e){e.title=t;e.url=u;}',
    '  } else {',
    '    g.entries.push({id:"ce-"+Date.now(),title:t,url:u});',
    '  }',
    '  await save();rmCM();renderCG();toast("Saved!");',
    '}',
    'async function delCE(gId,eId){',
    '  if(!confirm("Delete?"))return;',
    '  var g=(_data.commsGroups||[]).find(function(x){return x.id===gId;});',
    '  if(g)g.entries=(g.entries||[]).filter(function(e){return e.id!==eId;});',
    '  await save();renderCG();toast("Deleted");',
    '}',
]
comms_js = '\n'.join(js_lines)

close_pos = h.rfind('</script>')
h = h[:close_pos] + '\n' + comms_js + '\n</script>' + h[close_pos+9:]

# ── 5. Validate JS ────────────────────────────────────────────────────────
script_open = h.rfind('<script>') + 8
script_close = h.rfind('</script>')
js_content = h[script_open:script_close]

with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as tf:
    tf.write(js_content)
    tname = tf.name

result = subprocess.run(['node', '--check', tname], capture_output=True, text=True)
os.unlink(tname)

if result.returncode != 0:
    print('JS SYNTAX ERROR - not saving:')
    print(result.stderr[:400])
    exit(1)

with open(p, 'w', encoding='utf-8') as f:
    f.write(h)

print('Saved OK, size:', len(h))
print('Script tags:', h.count('<script>'), h.count('</script>'))
print('switchTab present:', 'switchTab' in h)
print('renderCG present:', 'renderCG' in h)
