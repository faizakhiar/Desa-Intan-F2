import json, html, sys
W=json.load(open(sys.argv[1]))
fix={"Krayong":"Kerayong","Kapa":"Kapar","Saya":"Saiz","setanah":"tanah","Nak":"Ke","kestialam":"Setia Alam","menit,":"minit,","menit.":"minit.","Bandasha":"Bandar Shah","buking":"booking","kemaju":"pemaju","Nijang":"Dijangka","kesiap":"siap","ribu":"ribu"}
words=[dict(w, w=fix.get(w["w"],w["w"])) for w in W]
# drop "ringgit" after 405 ribu / 500 -> keep spoken, it's fine
# phrase grouping: break on punctuation or max 4 words
clauses=[];cur=[]
for w in words:
    cur.append(w)
    if w["w"][-1] in ",.?": clauses.append(cur);cur=[]
if cur: clauses.append(cur)
import math
phr=[]
for c in clauses:
    n=math.ceil(len(c)/4); k=math.ceil(len(c)/n)
    for i in range(0,len(c),k): phr.append(c[i:i+k])
END=54.42
out=[]; js=[]
for i,p in enumerate(phr):
    if i==len(phr)-1: p[-1]=dict(p[-1],w=p[-1]["w"].rstrip(".")+"?")
    s=p[0]["s"]; e=(phr[i+1][0]["s"] if i+1<len(phr) else END)
    e=min(e, p[-1]["e"]+0.6) if i+1<len(phr) else e
    spans="".join(f'<span class="cw" id="cw{i}_{j}">{html.escape(w["w"].rstrip(",."))}</span> ' for j,w in enumerate(p))
    hid=' data-hidden' if 27.85<=s<34.35 else ''
    out.append(f'    <div class="cap clip"{hid} id="cap{i}" data-start="{s:.2f}" data-duration="{e-s:.2f}" data-track-index="0"><div class="cap-in" id="capin{i}">{spans.strip()}</div></div>')
    for j,w in enumerate(p):
        js.append(f'    tl.fromTo("#cw{i}_{j}", {{ opacity: 0, y: 18, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.12, ease: "back.out(2.5)" }}, {w["s"]:.2f});')
open("compositions/captions.html","w").write(f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; pointer-events: none; font-family: "Montserrat", sans-serif; }}
    .cap {{ position: absolute; left: 120px; top: 1150px; width: 768px; height: 100px; display: flex; align-items: center; justify-content: center; }}
    .cap-in {{ font-weight: 900; font-size: 42px; line-height: 1.1; color: #FFD23F; text-align: center; white-space: nowrap; text-transform: uppercase; -webkit-text-stroke: 3px #000; paint-order: stroke fill; text-shadow: 0 4px 0 #000, 0 6px 16px rgba(0,0,0,.75); }}
    .cw {{ display: inline-block; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(out)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
    window.__timelines["captions"] = tl;
  </script>
</template>
''')
print(len(phr),"phrases")
for p in phr: print(f'{p[0]["s"]:6.2f}', " ".join(w["w"] for w in p))
