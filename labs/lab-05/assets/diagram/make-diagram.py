#!/usr/bin/env python3
"""
make-diagram.py, Lab 05 architecture diagram from REAL Azure service icons.

Lab 05 builds almost no infrastructure, it proves CONTROL of an existing
resource group with four guardrails: RBAC (who), Azure Policy (what),
Budgets (how much) and Resource Locks (permanence). This diagram shows the
two "deny" money-shots side by side (RBAC blocks the junior dev, Policy
blocks the Owner) plus the supporting cast (budget alert, delete lock,
Defender secure score).

Embeds the official Microsoft Azure icon SVGs (rasterized to PNG by headless
Chrome) into a dark-themed diagram and renders:
  - architecture.html  (open it / show it on screen, self-contained)
  - architecture.png   (1600x900 design @2x, drop into the video/post)

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
services actually used in Lab 05 are shown.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":       "general/10007-icon-service-Resource-Groups.svg",
    "policy":   "management + governance/10316-icon-service-Policy.svg",
    "budget":   "general/10793-icon-service-Cost-Budgets.svg",
    "user":     "identity/10230-icon-service-Users.svg",
    "iam":      "identity/10340-icon-service-Entra-Identity-Roles-and-Administrators.svg",
    "vm":       "compute/10021-icon-service-Virtual-Machine.svg",
    "storage":  "storage/10086-icon-service-Storage-Accounts.svg",
    "defender": "security/10241-icon-service-Microsoft-Defender-for-Cloud.svg",
}


def data_uri(rel):
    with open(os.path.join(ICONS, rel), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ic = {k: data_uri(v) for k, v in ICON_FILES.items()}


def node(key, label, sub="", denied=False, size=52):
    subhtml = f'<div class="sub">{sub}</div>' if sub else ""
    badge = '<div class="xbadge">✕</div>' if denied else ""
    return (f'<div class="node"><div class="imgwrap">'
            f'<img src="{ic[key]}" style="width:{size}px;height:{size}px" alt="{label}">'
            f'{badge}</div>'
            f'<div class="lbl">{label}</div>{subhtml}</div>')


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:26px 36px 22px;
    display:flex; flex-direction:column; }}
  h1 {{ font-size:21px; color:#fff; font-weight:800; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:14px; }}
  .stage {{ position:relative; flex:1; margin-top:12px; }}
  .rg {{ position:absolute; inset:0; border:1.5px dashed #3a4658; border-radius:14px;
    padding:46px 26px 18px; display:flex; flex-direction:column; gap:12px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; z-index:3;}}
  .tag img {{ width:18px; height:18px; }}
  .lockbadge {{ position:absolute; top:-15px; right:18px; background:#1c1013;
    border:1px solid #5a2020; border-radius:8px; padding:4px 10px; display:flex; align-items:center;
    gap:6px; font-size:12px; font-weight:700; color:#f78f8f; z-index:3; }}
  .lockbadge .emo {{ font-size:15px; }}
  .lane {{ position:relative; flex:1; border-radius:10px; padding:26px 20px 10px;
    display:flex; align-items:center; gap:14px; }}
  .lane.rbac {{ border:1.5px solid #294b6b; background:#0d1722; }}
  .lane.pol  {{ border:1.5px solid #5a4419; background:#1a1509; }}
  .lane > .tag {{ top:-13px; font-size:12px; }}
  .lane.rbac > .tag {{ background:#0d1722; color:#79c0ff; }}
  .lane.pol  > .tag {{ background:#1a1509; color:#e3b341; }}
  .node {{ text-align:center; width:132px; flex:none; }}
  .imgwrap {{ position:relative; display:inline-block; }}
  .xbadge {{ position:absolute; top:-6px; right:-8px; width:18px; height:18px; border-radius:50%;
    background:#3a1014; border:1.5px solid #f78f8f; color:#f78f8f; font-size:11px; font-weight:900;
    display:flex; align-items:center; justify-content:center; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:12.5px; }}
  .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}
  .chiprow {{ display:flex; flex-direction:column; gap:3px; margin-top:6px; align-items:flex-start; }}
  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:2px 7px; font-size:10.5px; color:#9fb3c8; white-space:nowrap; }}
  .chip.deny {{ background:#1c1013; border-color:#5a2020; color:#f78f8f; font-weight:700; }}
  .flowcol {{ display:flex; flex-direction:column; align-items:center; gap:2px; flex:1; min-width:90px; }}
  .flowcol .lblsm {{ font-family:ui-monospace,Menlo,monospace; font-size:10.5px; color:#f78f8f;
    text-align:center; white-space:nowrap; }}
  .arrow {{ font-size:24px; font-weight:700; }}
  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }}
  .support {{ flex:0 0 auto; display:flex; gap:16px; padding:22px 6px 6px; position:relative; }}
  .support > .tag {{ top:-2px; left:8px; font-size:11.5px; }}
  .card {{ flex:1; border:1px solid #2a313c; background:#161b22; border-radius:10px;
    padding:12px 14px; display:flex; align-items:center; gap:12px; }}
  .card img {{ width:34px; height:34px; flex:none; }}
  .card .emo {{ font-size:30px; flex:none; width:34px; text-align:center; }}
  .card .txt {{ flex:1; }}
  .card .ctitle {{ font-weight:700; color:#e6edf3; font-size:12.5px; }}
  .card .csub {{ color:#7d8da0; font-size:11px; margin-top:1px; }}
  .card .cnote {{ color:#e3b341; font-size:10.5px; margin-top:3px; font-style:italic; }}
  .legend {{ flex:0 0 auto; margin-top:14px; display:flex; gap:26px; flex-wrap:wrap;
    font-size:12px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
</style></head><body><div class="canvas">
  <h1>Lab 05, Governance &amp; Hardening <span>· proving control of rg-lab05-gov-cam: who can act, what can exist, what it may cost, what can't be deleted</span></h1>

  <div class="stage">
    <div class="rg">
      <div class="tag"><img src="{ic['rg']}"> rg-lab05-gov-cam · East US</div>
      <div class="lockbadge"><span class="emo">🔒</span> lab05-delete-lock · CanNotDelete</div>

      <div class="lane rbac">
        <div class="tag">RBAC, governs WHO</div>
        {node("user", "junior-dev-cam", "Reader @ RG scope")}
        <div class="flowcol">
          <span class="lblsm">try: Create Storage Account</span>
          <span class="arrow a-deny">→</span>
        </div>
        {node("iam", "Access control (IAM)", "role check")}
        <div class="flowcol">
          <span class="lblsm">Access denied</span>
          <span class="arrow a-deny">✕</span>
        </div>
        {node("storage", "storage account", "blocked, Reader can't create", denied=True)}
        <div class="chiprow">
          <span class="chip deny">Denial A: this person can't</span>
          <span class="chip">An Owner still could</span>
        </div>
      </div>

      <div class="lane pol">
        <div class="tag">Azure Policy, governs WHAT (binds everyone, Owner included)</div>
        {node("user", "cam", "Owner @ RG scope")}
        <div class="flowcol">
          <span class="lblsm">try: Create vm-policy-test · Standard_D2s_v3</span>
          <span class="arrow a-deny">→</span>
        </div>
        {node("policy", "Lab05-Governance-Baseline", "initiative · 3 built-ins")}
        <div class="chiprow">
          <span class="chip">Allowed VM SKUs: B1s / B1ms</span>
          <span class="chip">Allowed locations: eastus / westus2</span>
          <span class="chip">Require tag: owner</span>
        </div>
        <div class="flowcol">
          <span class="lblsm">Policy check failed · Restrict-VM-Sizes</span>
          <span class="arrow a-deny">✕</span>
        </div>
        {node("vm", "vm-policy-test", "Standard_D2s_v3 · denied", denied=True)}
        <div class="chiprow">
          <span class="chip deny">Denial B: nobody can</span>
          <span class="chip">Rule binds the Owner too</span>
        </div>
      </div>

      <div class="support">
        <div class="tag">Supporting controls</div>
        <div class="card">
          {f'<img src="{ic["budget"]}">'}
          <div class="txt">
            <div class="ctitle">Monthly-Lab-Budget</div>
            <div class="csub">$50/mo · email alert @ 80% actual</div>
            <div class="cnote">alerts, does not cap spend</div>
          </div>
        </div>
        <div class="card">
          <div class="emo">🔒</div>
          <div class="txt">
            <div class="ctitle">lab05-delete-lock</div>
            <div class="csub">CanNotDelete on the RG</div>
            <div class="cnote">blocks delete for the Owner too, remove lock first at teardown</div>
          </div>
        </div>
        <div class="card">
          {f'<img src="{ic["defender"]}">'}
          <div class="txt">
            <div class="ctitle">Defender for Cloud</div>
            <div class="csub">Secure Score · read-only walk</div>
            <div class="cnote">free CSPM, paid Defender plans stay off</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="legend">
    <span><b>Denial A (RBAC):</b> sign in as junior-dev-cam → Create → Storage Account is greyed out / "not authorized", the person is restricted</span>
    <span><b>Denial B (Policy):</b> as Owner, create a D2s_v3 VM → "Validation failed · Policy check failed", the resource itself is refused</span>
    <span><b>Budget vs. Policy:</b> the budget only emails at 80% actual; the policy is what actually prevents the oversized VM before it deploys</span>
  </div>
</div>
<script>
  // Fixed 1600x900 design scaled to fit any window (PNG renders at scale 1).
  function fit() {{
    var c = document.querySelector('.canvas');
    c.style.transform = 'scale(' + Math.min(innerWidth/1600, innerHeight/900) + ')';
  }}
  addEventListener('resize', fit); fit();
</script>
</body></html>"""

html_path = os.path.join(OUT, "architecture.html")
png_path = os.path.join(OUT, "architecture.png")
with open(html_path, "w") as fh:
    fh.write(HTML)

subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                "--force-device-scale-factor=2", "--window-size=1600,900",
                f"--screenshot={png_path}", f"file://{html_path}"],
               check=True, capture_output=True, text=True)

print(f"[ok] {html_path}")
print(f"[ok] {png_path} ({os.path.getsize(png_path)/1024:.0f} KB)")
