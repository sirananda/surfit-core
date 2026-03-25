#!/usr/bin/env python3
"""Wave 3 clarification — website copy only"""
import shutil

FILE = "index.html"
shutil.copy(FILE, FILE + ".wave3")

with open(FILE, "r") as f:
    html = f.read()

# 1. Update the flow section wave description
html = html.replace(
    'Wave 1–3: execute automatically with logging. Wave 4–5: require approval. Most actions never need a human. Automatic does not mean unrestricted — execution is still constrained and logged.',
    'Wave 1–3: execute automatically with logging. Wave 4–5: require approval. Most actions never need a human. Risk is computed per action — not predefined by action type. Content, destination, and context determine the final risk level.'
)

with open(FILE, "w") as f:
    f.write(html)

print("✅ Wave 3 refinement applied")
print("Deploy: git add index.html && git commit -m 'Wave 3 refinement' && git push")
