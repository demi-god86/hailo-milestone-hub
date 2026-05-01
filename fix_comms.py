
import os, subprocess, tempfile

p = os.path.expanduser('~/Claude/milestone-hub/frontend/admin.html')
with open(p,'r',encoding='utf-8') as f:
    h = f.read()

# Fix 1: btn-del -> btn-delete (matches existing admin CSS)
h = h.replace('class=\\"btn-del\\"', 'class=\\"btn-delete\\"')

# Fix 2: Remove inline max-width override on comms wrap
h = h.replace('<div class="wrap" style="max-width:700px">', '<div class="wrap">')

# Validate
script_open = h.rfind('<script>') + 8
script_close = h.rfind('</script>')
js = h[script_open:script_close]
with tempfile.NamedTemporaryFile(mode='w',suffix='.js',delete=False,encoding='utf-8') as tf:
    tf.write(js); tname=tf.name
result = subprocess.run(['node','--check',tname],capture_output=True,text=True)
os.unlink(tname)
if result.returncode != 0:
    print('JS ERROR:', result.stderr[:200]); exit(1)

with open(p,'w',encoding='utf-8') as f:
    f.write(h)
print('Fixed OK')
