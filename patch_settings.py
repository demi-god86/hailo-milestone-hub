import os, subprocess, tempfile

p = os.path.expanduser('~/Claude/milestone-hub/frontend/admin.html')
with open(p,'r',encoding='utf-8') as f:
    h = f.read()

print('Original size:', len(h))
if 'saveSettings' in h:
    print('Already patched'); exit()

# ── 1. Add Settings button to tab nav ─────────────────────────────────────
old_nav = '<button class="tab-nav-btn" onclick="switchTab(\'comms\',this)">Comms</button></div>'
new_nav = '<button class="tab-nav-btn" onclick="switchTab(\'comms\',this)">Comms</button><button class="tab-nav-btn" onclick="switchTab(\'settings\',this)">Settings</button></div>'
h = h.replace(old_nav, new_nav)

# ── 2. Add Settings panel before toast ────────────────────────────────────
settings_panel = (
    '\n<div id="tab-settings" class="tab-panel">\n'
    '  <div class="wrap" style="max-width:600px">\n'
    '    <div class="section-title" style="margin-bottom:1.5rem">Site Copy</div>\n'
    '    <div class="add-card" style="margin-bottom:0">\n'
    '      <div class="edit-grid">\n'
    '        <div class="field full">\n'
    '          <label>Hub Title</label>\n'
    '          <input type="text" id="set-title" class="field-input" placeholder="The Homesearch Milestone Hub"/>\n'
    '        </div>\n'
    '        <div class="field full">\n'
    '          <label>Hub Subtitle</label>\n'
    '          <input type="text" id="set-sub" class="field-input" placeholder="Every time we hit something big..."/>\n'
    '        </div>\n'
    '      </div>\n'
    '      <button class="btn-save" onclick="saveSettings()" style="margin-top:1rem">Save Copy</button>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>\n'
)
h = h.replace('<div class="toast"', settings_panel + '<div class="toast"', 1)

# ── 3. Add settings JS before </script> ────────────────────────────────────
settings_js = """
function loadSettings(){
  var title = (_data.settings && _data.settings.heroTitle) || '';
  var sub   = (_data.settings && _data.settings.heroSub)   || '';
  var ti = document.getElementById('set-title');
  var si = document.getElementById('set-sub');
  if(ti) ti.value = title;
  if(si) si.value = sub;
}
async function saveSettings(){
  var title = document.getElementById('set-title').value.trim();
  var sub   = document.getElementById('set-sub').value.trim();
  if(!_data.settings) _data.settings = {};
  _data.settings.heroTitle = title;
  _data.settings.heroSub   = sub;
  await binSet(_data);
  showToast('Copy saved!');
}"""

# Also hook loadSettings into the existing load flow
# Find where _data is set after fetch and call loadSettings
old_render_call = 'render(record);'
new_render_call = 'render(record);loadSettings();'
h = h.replace(old_render_call, new_render_call, 1)

close_pos = h.rfind('</script>')
h = h[:close_pos] + settings_js + '\n</script>' + h[close_pos+9:]

# ── 4. Validate ─────────────────────────────────────────────────────────────
script_open = h.rfind('<script>') + 8
script_close = h.rfind('</script>')
js = h[script_open:script_close]
with tempfile.NamedTemporaryFile(mode='w',suffix='.js',delete=False,encoding='utf-8') as tf:
    tf.write(js); tname=tf.name
result = subprocess.run(['node','--check',tname],capture_output=True,text=True)
os.unlink(tname)
if result.returncode != 0:
    print('JS SYNTAX ERROR - not saving:')
    print(result.stderr[:400]); exit(1)

with open(p,'w',encoding='utf-8') as f:
    f.write(h)
print('Saved OK, size:', len(h))
print('Settings tab:', 'saveSettings' in h)
print('Tab count:', h.count('tab-nav-btn'))
