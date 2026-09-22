#!/usr/bin/env python3
"""
make-diagram.py — Lab 01 architecture flowchart from REAL Azure service icons.

Embeds the official Microsoft Azure icon SVGs (rasterized to PNG by headless
Chrome) into a dark-themed diagram and renders:
  - architecture.html  (open it / show it on screen — self-contained)
  - architecture.png   (1600x900 design @2x, drop into the video/post)

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
services actually used in Lab 01 are shown: a Storage Account with static
website hosting ($web container), an Entra ID app registration / service
principal used as the GitHub Actions deploy identity, and the RBAC role that
scopes it to exactly that one account.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":      "general/10007-icon-service-Resource-Groups.svg",
    "storage": "storage/10086-icon-service-Storage-Accounts.svg",
    "blob":    "general/10781-icon-service-Blob-Page.svg",
    "approg":  "identity/10232-icon-service-App-Registrations.svg",
    "role":    "identity/10340-icon-service-Entra-Identity-Roles-and-Administrators.svg",
}


def data_uri(rel):
    with open(os.path.join(ICONS, rel), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ic = {k: data_uri(v) for k, v in ICON_FILES.items()}


def icon(key, label, sub=""):
    subhtml = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="node"><img src="{ic[key]}" alt="{label}">'
            f'<div class="lbl">{label}</div>{subhtml}</div>')


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:32px 40px; }}
  h1 {{ font-size:22px; color:#fff; font-weight:800; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:15px; }}
  .visitor {{ position:absolute; top:34px; right:40px; text-align:right; }}
  .visitor .lbl {{ font-size:12px; font-weight:700; color:#9fb3c8; }}
  .visitor .flow {{ text-align:right; margin-top:2px; }}

  .zone {{ position:absolute; top:78px; bottom:90px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:46px 22px 22px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; }}
  .tag img {{ width:20px; height:20px; }}
  .tag.emoji {{ font-size:16px; }}

  .zone.github {{ left:40px; width:410px; border-color:#3a4658; background:#12161c; }}
  .zone.entra  {{ left:478px; width:330px; border:1.5px solid #5b4a9c; background:#161226; }}
  .zone.entra > .tag {{ background:#161226; color:#b6a4f0; }}
  .zone.azure  {{ left:836px; right:40px; border:1.5px dashed #3a4658; }}

  .rg-box {{ position:absolute; left:22px; right:22px; top:44px; bottom:22px;
    border:1.5px solid #294b6b; border-radius:10px; background:#0d1722; padding:40px 18px 18px; }}
  .rg-box > .tag {{ background:#0d1722; color:#79c0ff; font-size:12px; }}

  .stack {{ display:flex; flex-direction:column; gap:14px; align-items:stretch;
    height:100%; justify-content:center; }}
  .step-row {{ display:flex; align-items:center; justify-content:center; gap:6px; }}
  .node {{ text-align:center; width:104px; margin:0 auto; }}
  .node img {{ width:44px; height:44px; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:12.5px; }}
  .sub {{ color:#7d8da0; font-size:10.5px; margin-top:2px; }}
  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:3px 8px; font-size:11px; color:#9fb3c8; }}
  .chip.mono {{ font-family:ui-monospace,Menlo,monospace; }}
  .chip-row {{ display:flex; flex-wrap:wrap; gap:6px; justify-content:center; }}
  .flow {{ font-family:ui-monospace,Menlo,monospace; color:#8b98a5; font-size:11px;
    text-align:center; }}
  .divider {{ border-top:1px dashed #2a313c; margin:2px 0; }}
  .arrow-sm {{ color:#2f81f7; font-size:16px; align-self:center; }}
  .center-txt {{ text-align:center; }}

  .connector {{ position:absolute; top:50%; transform:translateY(-50%);
    width:56px; text-align:center; z-index:5; }}
  .connector.c1 {{ left:412px; }}
  .connector.c2 {{ left:794px; }}
  .connector .line {{ color:#2f81f7; font-size:26px; font-weight:700; }}
  .connector .port {{ display:block; background:#0e1116; border:1px solid #2f4159;
    border-radius:6px; padding:2px 6px; font-size:9.5px; color:#3fb950;
    font-family:ui-monospace,Menlo,monospace; margin-top:2px; white-space:nowrap; }}

  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }} .a-warn {{ color:#e3b341; }}
  .legend {{ position:absolute; left:40px; bottom:22px; right:40px; display:flex;
    flex-direction:column; gap:5px; font-size:12px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
</style></head><body><div class="canvas">
  <h1>Lab 01 — Host a Static Website <span>· Azure Storage static hosting + GitHub Actions deploy, zero servers, zero stored keys</span></h1>

  <div class="visitor">
    <div class="lbl">🌐 Visitor</div>
    <div class="chip mono flow">GET https://camjacksonportfolio2026.z##.web.core.windows.net/</div>
  </div>

  <div class="zone github">
    <div class="tag emoji">🐙 GitHub — cam-portfolio repo</div>
    <div class="stack">
      <div class="center-txt"><span class="chip mono">push → main (paths: site/**)</span></div>
      <div class="flow">↓ workflow_dispatch also allowed</div>
      <div class="step-row">
        <div class="chip">checkout</div>
        <div class="arrow-sm">→</div>
        <div class="chip">azure/login</div>
        <div class="arrow-sm">→</div>
        <div class="chip">upload-batch</div>
      </div>
      <div class="flow">ubuntu-latest runner · runs.azure/login@v2</div>
      <div class="divider"></div>
      <div class="chip-row">
        <span class="chip mono">secret: AZURE_CREDENTIALS</span>
        <span class="chip mono">var: STORAGE_ACCOUNT</span>
      </div>
      <div class="flow">4-field JSON: tenantId · clientId · clientSecret · subscriptionId</div>
      <div class="flow a-allow">az storage blob upload-batch --auth-mode login --destination '$web' --overwrite</div>
    </div>
  </div>

  <div class="connector c1">
    <div class="line">→</div>
    <span class="port">login (client secret)</span>
  </div>

  <div class="zone entra">
    <div class="tag">🔑 Entra ID tenant</div>
    <div class="stack">
      {icon("approg", "gh-cloud-portfolio-deploy", "app registration / service principal")}
      <div class="divider"></div>
      {icon("role", "Storage Blob Data Contributor", "RBAC role assignment")}
      <div class="flow a-allow">scoped to ONE storage account</div>
      <div class="flow">data plane only — no keys, no control-plane access</div>
    </div>
  </div>

  <div class="connector c2">
    <div class="line">→</div>
    <span class="port">RBAC token</span>
  </div>

  <div class="zone azure">
    <div class="tag emoji">☁️ Subscription — sub-cloud-portfolio</div>
    <div class="rg-box">
      <div class="tag"><img src="{ic['rg']}"> rg-cloud-portfolio</div>
      <div class="stack">
        {icon("storage", "camjacksonportfolio2026", "Standard · LRS")}
        <div class="center-txt arrow-sm">↓</div>
        {icon("blob", "$web container", "index.html · 404.html")}
        <div class="flow">Data management → Static website: ON</div>
        <div class="center-txt"><span class="chip mono a-allow">.web.core.windows.net endpoint · HTTPS</span></div>
        <div class="flow a-deny">no storage account key used anywhere in the pipeline</div>
      </div>
    </div>
  </div>

  <div class="legend">
    <span><b>Deploy (Flow A):</b> push to <span class="a-allow">main</span> touching <span class="a-allow">site/**</span> → GitHub runner checks out repo → <b>azure/login</b> authenticates as the SP using <b>AZURE_CREDENTIALS</b> → Entra issues a scoped token (<b>Storage Blob Data Contributor</b>, this account only) → <b>upload-batch --auth-mode login</b> writes blobs into <b>$web</b> (idempotent, <span class="a-allow">--overwrite</span>).</span>
    <span><b>Visitor (Flow B):</b> browser → storage account's <b>.web.</b> endpoint → static-website layer serves <b>$web/index.html</b> over HTTPS — <span class="a-deny">no web server, no compute, nothing to patch</span>. Unknown paths get <b>404.html</b>.</span>
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
