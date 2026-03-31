"""
Replace single demo section with two demos.
Demo #1 and Demo #2 with orange icon labels.
Both below the visualization section.

Run from ~/Desktop/files/: python3 patch_demos.py
"""

filepath = "index.html"

with open(filepath, "r") as f:
    content = f.read()

old = '''<!-- PRODUCT DEMO -->
<section id="demo" style="background:var(--dark);border-top:1px solid var(--border);padding:72px 48px;">
  <div class="container" style="max-width:920px;">
    <div class="section-label">Product Demo</div>
    <div class="section-title brand-heading" style="">See Surfit in Action</div>
    <p class="section-body" style="max-width:640px;">Surfit evaluates and controls every agent action across your systems... before it executes.<br>Lower-risk actions flow automatically... higher-risk actions are held for approval.<br>Every decision is logged, traceable, and enforced in real time.</p>
    <div style="margin-top:40px;position:relative;padding-bottom:56.25%;height:0;border-radius:12px;overflow:hidden;border:1px solid var(--border);box-shadow:0 16px 48px rgba(0,0,0,0.4);">
      <iframe
        src="https://www.loom.com/embed/13572a5d0d754e9fa0162d51dbc07064"
        frameborder="0"
        webkitallowfullscreen
        mozallowfullscreen
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;">
      </iframe>
    </div>
  </div>
</section>'''

new = '''<!-- PRODUCT DEMO -->
<section id="demo" style="background:var(--dark);border-top:1px solid var(--border);padding:72px 48px;">
  <div class="container" style="max-width:920px;">
    <div class="section-label">Product Demo</div>
    <div class="section-title brand-heading" style="">See Surfit in Action</div>
    <p class="section-body" style="max-width:640px;">Surfit evaluates and controls every agent action across your systems — before it executes.<br>Lower-risk actions flow automatically. Higher-risk actions are held for context.<br>Every decision is logged, traceable, and enforced in real time.</p>

    <div style="margin-top:40px;">
      <div style="display:inline-block;background:var(--orange);color:#000;font-size:10px;font-weight:700;padding:4px 14px;border-radius:6px;letter-spacing:0.08em;margin-bottom:14px;">DEMO #1</div>
      <div style="position:relative;padding-bottom:56.25%;height:0;border-radius:12px;overflow:hidden;border:1px solid var(--border);box-shadow:0 16px 48px rgba(0,0,0,0.4);">
        <iframe
          src="https://www.loom.com/embed/911266e987dd49e6821e4348baf99341"
          frameborder="0"
          webkitallowfullscreen
          mozallowfullscreen
          allowfullscreen
          style="position:absolute;top:0;left:0;width:100%;height:100%;">
        </iframe>
      </div>
    </div>

    <div style="margin-top:40px;">
      <div style="display:inline-block;background:var(--orange);color:#000;font-size:10px;font-weight:700;padding:4px 14px;border-radius:6px;letter-spacing:0.08em;margin-bottom:14px;">DEMO #2</div>
      <div style="position:relative;padding-bottom:56.25%;height:0;border-radius:12px;overflow:hidden;border:1px solid var(--border);box-shadow:0 16px 48px rgba(0,0,0,0.4);">
        <iframe
          src="https://www.loom.com/embed/db833c83807a442ab0e948b062f2fa89"
          frameborder="0"
          webkitallowfullscreen
          mozallowfullscreen
          allowfullscreen
          style="position:absolute;top:0;left:0;width:100%;height:100%;">
        </iframe>
      </div>
    </div>

  </div>
</section>'''

if old in content:
    content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)
    print("✅ Demo section replaced with Demo #1 and Demo #2")
    print("git add index.html && git commit -m 'two demos with orange labels' && git push")
else:
    print("❌ Demo section not found — exact string mismatch")
