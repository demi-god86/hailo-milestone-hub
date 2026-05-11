import os, subprocess, tempfile

p = os.path.expanduser('~/Claude/milestone-hub/frontend/index.html')
with open(p,'r',encoding='utf-8') as f:
    h = f.read()

print('Original size:', len(h))
if 'applySettings' in h:
    print('Already patched'); exit()

# ── 1. Make title and subtitle have IDs so JS can update them ─────────────
old_title = '<div class="hero-title">The Homesearch<span>Milestone Hub</span></div>'
new_title = '<div class="hero-title" id="hero-title">The Homesearch<span id="hero-title-span">Milestone Hub</span></div>'
h = h.replace(old_title, new_title)

old_sub = '<div class="hero-sub">Every time we hit something big, it gets locked inside a puzzle. Crack it, claim your place on the leaderboard.</div>'
new_sub = '<div class="hero-sub" id="hero-sub">Every time we hit something big, it gets locked inside a puzzle. Crack it, claim your place on the leaderboard.</div>'
h = h.replace(old_sub, new_sub)

# ── 2. Add applySettings function and call it in render ────────────────────
settings_js = """
function applySettings(record){
  var s = record && record.settings;
  if(!s) return;
  if(s.heroTitle){
    var parts = s.heroTitle.split(' ');
    // Put last 2 words in the span (coloured), rest in main text
    if(parts.length >= 2){
      var span = parts.slice(-2).join(' ');
      var main = parts.slice(0,-2).join(' ');
      var el = document.getElementById('hero-title');
      var sp = document.getElementById('hero-title-span');
      if(el && sp){ el.childNodes[0].textContent = main; sp.textContent = span; }
    } else {
      var el = document.getElementById('hero-title');
      if(el) el.textContent = s.heroTitle;
    }
  }
  if(s.heroSub){
    var sub = document.getElementById('hero-sub');
    if(sub) sub.textContent = s.heroSub;
  }
}"""

# Hook into both fetch paths
old_fresh1 = 'render(cached.d);\n      fetchFresh(function(fresh){render(fresh);renderComms(fresh);});\n      return;'
new_fresh1 = 'render(cached.d);applySettings(cached.d);\n      fetchFresh(function(fresh){render(fresh);renderComms(fresh);applySettings(fresh);});\n      return;'
h = h.replace(old_fresh1, new_fresh1)

old_fresh2 = 'fetchFresh(function(data){render(data);renderComms(data);});'
new_fresh2 = 'fetchFresh(function(data){render(data);renderComms(data);applySettings(data);});'
h = h.replace(old_fresh2, new_fresh2)

close_pos = h.rfind('</script>')
h = h[:close_pos] + settings_js + '\n</script>' + h[close_pos+9:]

# ── 3. Validate ─────────────────────────────────────────────────────────────
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
print('applySettings:', 'applySettings' in h)
print('hero-title id:', 'id="hero-title"' in h)
