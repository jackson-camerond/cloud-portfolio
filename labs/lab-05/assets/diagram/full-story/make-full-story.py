#!/usr/bin/env python3
"""
make-full-story.py, Lab 05 "full story" demo: Fluency Sheet (teach) -> Lab
Guide (build it out) -> Shoot Script (walkthrough), chaptered into one
continuous animated video.

Audio: 100% the existing ElevenLabs narration (Fluency-Sheet, Lab-Guide,
Shoot-Script-Walkthrough) plus two short AI-drafted / ElevenLabs-voiced
transition lines bridging the seams. Combined audio already built at
combined-audio.m4a (see concat_audio.txt in this folder).

Visual stage timestamps were found by locally transcribing each of the three
source narration files with mlx-whisper (word timestamps) and locating the
phrase that opens each beat -- no guessing, no extra TTS cost for timing.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                      "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(OUT, "frames")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
AUDIO = os.path.join(OUT, "combined-audio.m4a")
FINAL_MP4 = os.path.join(OUT, "Lab05-Full-Story.mp4")

os.makedirs(FRAMES, exist_ok=True)

ICON_FILES = {
    "rg": "general/10007-icon-service-Resource-Groups.svg",
    "users": "identity/10230-icon-service-Users.svg",
    "policy": "management + governance/10316-icon-service-Policy.svg",
    "budget": "general/10793-icon-service-Cost-Budgets.svg",
    "defender": "security/10241-icon-service-Microsoft-Defender-for-Cloud.svg",
}

def data_uri(rel):
    with open(os.path.join(ICONS, rel), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"

ic = {k: data_uri(v) for k, v in ICON_FILES.items()}

OFFSET_GUIDE = 537.355011
OFFSET_SCRIPT = 936.151020
END = 1385.828662

STAGES = [
    # (time, chapter, kind, payload)
    (0.0,                     "fluency", "concept", dict(rbac=False, policy=False, budget=False, lock=False, click=False, score=False, wrap=False)),
    (129.38,                  "fluency", "concept", dict(rbac=True,  policy=False, budget=False, lock=False, click=False, score=False, wrap=False)),
    (216.06,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=False, lock=False, click=False, score=False, wrap=False)),
    (302.68,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=True,  lock=False, click=False, score=False, wrap=False)),
    (338.30,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=True,  lock=True,  click=False, score=False, wrap=False)),
    (380.82,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=True,  lock=True,  click=True,  score=False, wrap=False)),
    (425.16,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=True,  lock=True,  click=True,  score=True,  wrap=False)),
    (492.88,                  "fluency", "concept", dict(rbac=True,  policy=True,  budget=True,  lock=True,  click=True,  score=True,  wrap=True)),

    (OFFSET_GUIDE + 0.0,      "guide",   "build",   dict(rg=False, rbac=False, denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 34.10,    "guide",   "build",   dict(rg=True,  rbac=False, denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 61.64,    "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 112.78,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 142.42,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=1, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 191.04,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 222.50,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 258.84,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=False, denial_b=False, final=False)),
    (OFFSET_GUIDE + 302.06,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=False, final=False)),
    (OFFSET_GUIDE + 329.70,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=True,  final=False)),
    (OFFSET_GUIDE + 368.18,   "guide",   "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=True,  final=True)),

    (OFFSET_SCRIPT + 0.0,     "script",  "build",   dict(rg=False, rbac=False, denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 33.92,   "script",  "build",   dict(rg=True,  rbac=False, denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 64.74,   "script",  "build",   dict(rg=True,  rbac=True,  denial_a=False, policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 98.90,   "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=0, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 130.48,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=1, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 170.26,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=False, lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 222.12,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=False, score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 251.28,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=False, denial_b=False, final=False)),
    (OFFSET_SCRIPT + 288.56,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=False, final=False)),
    (OFFSET_SCRIPT + 317.12,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=True,  final=False)),
    (OFFSET_SCRIPT + 413.68,  "script",  "build",   dict(rg=True,  rbac=True,  denial_a=True,  policy=2, budget=True,  lock=True,  score=True,  denial_b=True,  final=True)),
]

CHAPTER_TITLE = {
    "fluency": "Chapter 1 · Understand the four levers",
    "guide":   "Chapter 2 · The assignment, step by step",
    "script":  "Chapter 3 · How the build actually went",
}

def card(key, title, sub, lit, extra_cls=""):
    cls = "card lit" if lit else "card"
    if extra_cls:
        cls += " " + extra_cls
    icon_html = f'<img src="{ic[key]}">' if key in ic else f'<span class="emoji">{key}</span>'
    return (f'<div class="{cls}">{icon_html}'
            f'<div class="ctitle">{title}</div><div class="csub">{sub}</div></div>')

BASE_CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
html,body { width:100%; height:100%; overflow:hidden; background:#0e1116;
  font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }
body { display:flex; align-items:center; justify-content:center; }
.canvas { position:relative; flex:none; width:1600px; height:900px; padding:34px 40px; }
h1 { font-size:24px; color:#fff; font-weight:800; }
.chapter { font-size:14px; color:#7fb0ff; font-weight:700; margin-top:4px; letter-spacing:.02em; }
.card { flex:1; background:#161b22; border:1.5px solid #2a313c; border-radius:10px;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:10px 8px; text-align:center; opacity:0.35; filter:grayscale(1); max-width:180px; }
.card.lit { opacity:1; filter:none; border-color:#3fb95055; box-shadow:0 0 0 1px #3fb95022; }
.card.concept { opacity:0.75; filter:none; border-color:#7fb0ff55; border-style:dashed; }
.card.ghost { border-style:dashed; opacity:0.15; }
.card img { width:34px; height:34px; }
.card .emoji { font-size:30px; line-height:1; }
.ctitle { font-size:12.5px; font-weight:700; color:#e6edf3; margin-top:6px; }
.csub { font-size:10.5px; color:#7d8da0; margin-top:2px; line-height:1.3; }
"""

def render_concept(p):
    cards = [
        card("users", "RBAC", "governs who", p["rbac"]),
        card("policy", "Policy", "governs what", p["policy"]),
        card("budget", "Budget", "governs how much", p["budget"]),
        card("\U0001F512", "Lock", "governs permanence", p["lock"]),
    ]
    click_html = ""
    if p["click"]:
        click_html = '''
        <div class="compare">
          <div class="cbox"><b>RBAC</b><span>denies the person</span></div>
          <div class="cbox"><b>Policy</b><span>denies the resource</span></div>
        </div>'''
    score_html = f'<div class="score"><img src="{ic["defender"]}"> Secure Score <b>72%</b></div>' if p["score"] else ""
    wrap = ", you understand it. now let's build it" if p["wrap"] else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
.stage {{ position:absolute; left:40px; right:40px; top:170px; bottom:60px;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:56px; }}
.cardrow {{ display:flex; gap:22px; justify-content:center; width:100%; }}
.cardrow .card {{ height:170px; }}
.compare {{ display:flex; gap:40px; }}
.cbox {{ background:#161b22; border:1.5px solid #2a313c; border-radius:10px; padding:18px 28px;
  text-align:center; }}
.cbox b {{ display:block; font-size:16px; color:#e6edf3; }}
.cbox span {{ font-size:12.5px; color:#9fb3c8; }}
.score {{ display:flex; gap:8px; align-items:center; font-size:15px; color:#9fb3c8; font-weight:700; }}
.score img {{ width:22px; height:22px; }} .score b {{ color:#3fb950; }}
</style></head><body><div class="canvas">
  <h1>Lab 05, Governance &amp; Security Hardening{wrap}</h1>
  <div class="chapter">{CHAPTER_TITLE["fluency"]}</div>
  <div class="stage">
    <div class="cardrow">{''.join(cards)}</div>
    {click_html}
    {score_html}
  </div>
</div></body></html>"""

def render_build(chapter, p):
    rg_block = ""
    if p["rg"]:
        cards = [card("users", "RBAC, Reader", "junior-dev-cam · scope: this RG", p["rbac"])]
        if p["policy"] == 2:
            cards.append(card("policy", "Policy, Initiative", "Restrict-VM-Sizes · locations · owner tag", True))
        elif p["policy"] == 1:
            cards.append(card("policy", "Policy", "if VM size not allowed &rarr; deny", False, "concept"))
        else:
            cards.append('<div class="card ghost"></div>')
        cards.append(card("budget", "Budget", "$50/mo · alert @ 80% actual", True) if p["budget"] else '<div class="card ghost"></div>')
        cards.append(card("\U0001F512", "Lock", "CanNotDelete", True) if p["lock"] else '<div class="card ghost"></div>')
        score_html = f'<div class="score"><img src="{ic["defender"]}"> Secure Score <b>72%</b></div>' if p["score"] else ""
        rg_block = f'''
        <div class="rg">
          <div class="tag"><img src="{ic['rg']}"> rg-lab05-gov-cam</div>
          <div class="cardrow">{''.join(cards)}</div>
          {score_html}
        </div>'''

    denial_a_html = ""
    if p["denial_a"]:
        settled = " settled" if p["denial_b"] or p["final"] else ""
        denial_a_html = f'''
        <div class="testpanel left{settled}">
          <div class="ttitle">Incognito, junior-dev-cam</div>
          <div class="tattempt">Create &rarr; Storage Account</div>
          <div class="tresult deny">❌ Unauthorized</div>
        </div>'''

    denial_b_html = ""
    if p["denial_b"]:
        denial_b_html = f'''
        <div class="testpanel right">
          <div class="ttitle">Owner, vm-policy-test</div>
          <div class="tattempt">Create &rarr; VM &middot; Standard_D2s_v3</div>
          <div class="tresult deny">❌ Policy check failed, Restrict-VM-Sizes</div>
        </div>'''

    title_suffix = ", governed ✓" if p["final"] else ""

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
.sub {{ position:absolute; left:40px; top:130px; right:40px; bottom:40px;
  border:1.5px dashed #3a4658; border-radius:16px; padding:40px; }}
.subtag {{ position:absolute; top:-13px; left:24px; background:#0e1116; padding:0 10px;
  font-weight:700; color:#7d8da0; font-size:13px; }}
.owner {{ position:absolute; left:24px; top:118px; text-align:center; width:110px; }}
.owner .emoji {{ font-size:40px; }}
.owner .lbl {{ font-size:12px; color:#9fb3c8; margin-top:4px; font-weight:700; }}
.rg {{ position:absolute; left:190px; right:380px; top:130px; bottom:70px;
  border:1.5px solid #2f4159; border-radius:14px; background:#10161f; padding:44px 24px 20px; }}
.rg .tag {{ position:absolute; top:-13px; left:20px; background:#10161f; padding:0 10px;
  display:flex; align-items:center; gap:8px; font-weight:700; color:#7fb0ff; font-size:13px; }}
.rg .tag img {{ width:20px; height:20px; }}
.cardrow {{ display:flex; gap:14px; justify-content:center; align-items:stretch; height:150px; }}
.score {{ position:absolute; bottom:16px; left:24px; right:24px; display:flex; gap:8px;
  align-items:center; font-size:13px; color:#9fb3c8; font-weight:700; }}
.score img {{ width:20px; height:20px; }} .score b {{ color:#3fb950; }}
.testpanel {{ position:absolute; right:40px; width:320px; background:#161b22;
  border:1.5px solid #f7768e55; border-radius:10px; padding:14px 16px; }}
.testpanel.left {{ top:150px; }} .testpanel.right {{ top:400px; }}
.testpanel.settled {{ opacity:0.55; }}
.ttitle {{ font-size:12px; color:#9fb3c8; font-weight:700; }}
.tattempt {{ font-size:12.5px; color:#e6edf3; margin-top:6px; font-family:ui-monospace,Menlo,monospace; }}
.tresult {{ margin-top:8px; font-size:12.5px; font-weight:700; }}
.tresult.deny {{ color:#f78f8f; }}
</style></head><body><div class="canvas">
  <h1>Lab 05, Governance &amp; Security Hardening{title_suffix}</h1>
  <div class="chapter">{CHAPTER_TITLE[chapter]}</div>
  <div class="sub">
    <div class="subtag">Subscription &middot; Azure subscription 1</div>
    <div class="owner"><div class="emoji">\U0001F464</div><div class="lbl">Owner &middot; cam</div></div>
    {rg_block}
    {denial_a_html}
    {denial_b_html}
  </div>
</div></body></html>"""

def screenshot(html, png_path):
    html_path = png_path.replace(".png", ".html")
    with open(html_path, "w") as f:
        f.write(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                     "--force-device-scale-factor=1", "--window-size=1600,900",
                     f"--screenshot={png_path}", f"file://{html_path}"],
                    check=True, capture_output=True, text=True)

def main():
    times = [s[0] for s in STAGES] + [END]
    seg_paths = []
    for i, (t, chapter, kind, payload) in enumerate(STAGES):
        html = render_concept(payload) if kind == "concept" else render_build(chapter, payload)
        png = os.path.join(FRAMES, f"stage-{i:02d}.png")
        screenshot(html, png)
        seg_dur = times[i + 1] - t
        seg_mp4 = os.path.join(FRAMES, f"seg-{i:02d}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{seg_dur:.3f}",
                         "-i", png, "-vf", "format=yuv420p", "-r", "30", seg_mp4], check=True)
        seg_paths.append(seg_mp4)
        print(f"stage {i:02d} [{chapter}]: {t:.2f}s -> {times[i+1]:.2f}s ({seg_dur:.2f}s)")

    concat_list = os.path.join(FRAMES, "concat.txt")
    with open(concat_list, "w") as f:
        for p in seg_paths:
            f.write(f"file '{p}'\n")

    combined = os.path.join(FRAMES, "combined-video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                     "-i", concat_list, "-c", "copy", combined], check=True)

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", combined, "-i", AUDIO,
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", FINAL_MP4],
                    check=True)
    print(f"\nDONE -> {FINAL_MP4}")

if __name__ == "__main__":
    main()
