#!/usr/bin/env python3
"""
make-architecture-animation.py, Lab 05 architecture diagram, animated to build
up in sync with the existing Shoot-Script-Walkthrough narration audio.

No new TTS is generated here, this reuses labs/lab-05/audio/Lab05-Shoot-Script-Walkthrough.m4a
as-is. Timestamps for each build stage were found by locally transcribing that
audio with mlx-whisper (word-level timestamps) and locating the phrase that
opens each step, so the visual always lands on the beat the narration is
actually saying it.

Produces:
  frames/stage-XX.png   (1600x900 dark-theme diagram, one per build stage)
  Lab05-Architecture-Build.mp4  (final video, audio muxed in)
"""
import os, base64, subprocess, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                      "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(OUT, "frames")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
AUDIO = os.path.join(REPO, "labs/lab-05/audio/Lab05-Shoot-Script-Walkthrough.m4a")
FINAL_MP4 = os.path.join(OUT, "Lab05-Architecture-Build.mp4")

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

# Stage index -> narration timestamp (seconds) it should appear at.
# Found via mlx-whisper word timestamps on the existing narration audio,
# anchored on "step N was ..." openers (see scratch find_anchors.py).
STAGE_TIMES = [
    0.0,      # 0  intro / empty subscription
    33.92,    # 1  resource group appears
    64.74,    # 2  RBAC: junior dev + Reader role
    98.90,    # 3  Denial A: storage account create blocked
    130.48,   # 4  Policy concept (if/then) introduced
    170.26,   # 5  Initiative assigned + lit (3 rules)
    222.12,   # 6  Budget card lit
    251.28,   # 7  Lock card lit
    288.56,   # 8  Secure Score chip lit
    317.12,   # 9  Denial B: VM create blocked by policy
    413.68,   # 10 wrap-up / fully governed state
]

def card(key, title, sub, lit, extra_cls=""):
    cls = "card lit" if lit else "card"
    if extra_cls:
        cls += " " + extra_cls
    icon_html = f'<img src="{ic[key]}">' if key in ic else f'<span class="emoji">{key}</span>'
    return (f'<div class="{cls}">{icon_html}'
            f'<div class="ctitle">{title}</div><div class="csub">{sub}</div></div>')

def render_html(stage):
    rg_visible   = stage >= 1
    rbac_lit     = stage >= 2
    denial_a     = stage >= 3
    policy_intro = stage >= 4
    policy_lit   = stage >= 5
    budget_lit   = stage >= 6
    lock_lit     = stage >= 7
    score_lit    = stage >= 8
    denial_b     = stage >= 9
    final        = stage >= 10

    rg_block = ""
    if rg_visible:
        cards = []
        cards.append(card("users", "RBAC, Reader", "junior-dev-cam · scope: this RG", rbac_lit))
        if policy_lit:
            cards.append(card("policy", "Policy, Initiative", "Restrict-VM-Sizes · locations · owner tag", True))
        elif policy_intro:
            cards.append(card("policy", "Policy", "if VM size not allowed → deny", False, "concept"))
        else:
            cards.append('<div class="card ghost"></div>')
        cards.append(card("budget", "Budget", "$50/mo · alert @ 80% actual", budget_lit) if budget_lit or True else "")
        if not budget_lit:
            cards[-1] = '<div class="card ghost"></div>'
        cards.append(card("\U0001F512", "Lock", "CanNotDelete", lock_lit) if lock_lit else '<div class="card ghost"></div>')
        rg_block = f'''
        <div class="rg">
          <div class="tag"><img src="{ic['rg']}"> rg-lab05-gov-cam</div>
          <div class="cardrow">{''.join(cards)}</div>
          {f'<div class="score"><img src="{ic["defender"]}"> Secure Score <b>72%</b></div>' if score_lit else ""}
        </div>'''

    denial_a_html = ""
    if denial_a:
        settled = " settled" if stage > 3 else ""
        denial_a_html = f'''
        <div class="testpanel left{settled}">
          <div class="ttitle">Incognito, junior-dev-cam</div>
          <div class="tattempt">Create → Storage Account</div>
          <div class="tresult deny">❌ Unauthorized</div>
        </div>'''

    denial_b_html = ""
    if denial_b:
        denial_b_html = f'''
        <div class="testpanel right">
          <div class="ttitle">Owner, vm-policy-test</div>
          <div class="tattempt">Create → VM · Standard_D2s_v3</div>
          <div class="tresult deny">❌ Policy check failed, Restrict-VM-Sizes</div>
        </div>'''

    title_suffix = ", governed ✓" if final else ""

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
  font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
body {{ display:flex; align-items:center; justify-content:center; }}
.canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:34px 40px; }}
h1 {{ font-size:24px; color:#fff; font-weight:800; }}
h1 span {{ color:#5c6b7a; font-weight:500; font-size:15px; }}
.sub {{ position:absolute; left:40px; top:90px; right:40px; bottom:40px;
  border:1.5px dashed #3a4658; border-radius:16px; padding:40px; }}
.subtag {{ position:absolute; top:-13px; left:24px; background:#0e1116; padding:0 10px;
  font-weight:700; color:#7d8da0; font-size:13px; }}
.owner {{ position:absolute; left:64px; top:118px; text-align:center; width:110px; }}
.owner .emoji {{ font-size:40px; }}
.owner .lbl {{ font-size:12px; color:#9fb3c8; margin-top:4px; font-weight:700; }}
.rg {{ position:absolute; left:230px; right:380px; top:130px; bottom:70px;
  border:1.5px solid #2f4159; border-radius:14px; background:#10161f; padding:44px 24px 20px; }}
.rg .tag {{ position:absolute; top:-13px; left:20px; background:#10161f; padding:0 10px;
  display:flex; align-items:center; gap:8px; font-weight:700; color:#7fb0ff; font-size:13px; }}
.rg .tag img {{ width:20px; height:20px; }}
.cardrow {{ display:flex; gap:14px; justify-content:center; align-items:stretch; height:150px; }}
.card {{ flex:1; background:#161b22; border:1.5px solid #2a313c; border-radius:10px;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:10px 8px; text-align:center; opacity:0.35; filter:grayscale(1); }}
.card.lit {{ opacity:1; filter:none; border-color:#3fb95055; box-shadow:0 0 0 1px #3fb95022; }}
.card.concept {{ opacity:0.75; filter:none; border-color:#7fb0ff55; border-style:dashed; }}
.card.ghost {{ border-style:dashed; opacity:0.15; }}
.card img {{ width:34px; height:34px; }}
.card .emoji {{ font-size:30px; line-height:1; }}
.ctitle {{ font-size:12.5px; font-weight:700; color:#e6edf3; margin-top:6px; }}
.csub {{ font-size:10.5px; color:#7d8da0; margin-top:2px; line-height:1.3; }}
.score {{ position:absolute; bottom:16px; left:24px; right:24px; display:flex; gap:8px;
  align-items:center; font-size:13px; color:#9fb3c8; font-weight:700; }}
.score img {{ width:20px; height:20px; }}
.score b {{ color:#3fb950; }}
.testpanel {{ position:absolute; right:40px; width:320px; background:#161b22;
  border:1.5px solid #f7768e55; border-radius:10px; padding:14px 16px; }}
.testpanel.left {{ top:150px; }}
.testpanel.right {{ top:400px; }}
.testpanel.settled {{ opacity:0.55; }}
.ttitle {{ font-size:12px; color:#9fb3c8; font-weight:700; }}
.tattempt {{ font-size:12.5px; color:#e6edf3; margin-top:6px; font-family:ui-monospace,Menlo,monospace; }}
.tresult {{ margin-top:8px; font-size:12.5px; font-weight:700; }}
.tresult.deny {{ color:#f78f8f; }}
</style></head><body><div class="canvas">
  <h1>Lab 05, Governance &amp; Security Hardening{title_suffix}</h1>
  <div class="sub">
    <div class="subtag">Subscription · Azure subscription 1</div>
    <div class="owner"><div class="emoji">\U0001F464</div><div class="lbl">Owner · cam</div></div>
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
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", AUDIO],
        capture_output=True, text=True).stdout.strip())
    times = STAGE_TIMES + [dur]

    seg_paths = []
    for i in range(len(STAGE_TIMES)):
        png = os.path.join(FRAMES, f"stage-{i:02d}.png")
        screenshot(render_html(i), png)
        seg_dur = times[i + 1] - times[i]
        seg_mp4 = os.path.join(FRAMES, f"seg-{i:02d}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{seg_dur:.3f}",
                         "-i", png, "-vf", "format=yuv420p", "-r", "30", seg_mp4], check=True)
        seg_paths.append(seg_mp4)
        print(f"stage {i}: {times[i]:.2f}s -> {times[i+1]:.2f}s ({seg_dur:.2f}s)")

    concat_list = os.path.join(FRAMES, "concat.txt")
    with open(concat_list, "w") as f:
        for p in seg_paths:
            f.write(f"file '{p}'\n")

    combined = os.path.join(FRAMES, "combined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                     "-i", concat_list, "-c", "copy", combined], check=True)

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", combined, "-i", AUDIO,
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", FINAL_MP4],
                    check=True)
    print(f"\nDONE -> {FINAL_MP4}")

if __name__ == "__main__":
    main()
