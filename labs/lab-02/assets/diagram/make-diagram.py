#!/usr/bin/env python3
"""
make-diagram.py : Lab 02 architecture flowchart from real Azure service icons.

Embeds the official Microsoft Azure icon SVGs (rasterized to PNG by headless
Chrome) into a dark-themed diagram and renders:
  - architecture.html  (self-contained, open it in a browser)
  - architecture.png   (3200x1800, drop into the video)

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
services actually used in Lab 02 are shown.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":      "general/10007-icon-service-Resource-Groups.svg",
    "vnet":    "networking/10061-icon-service-Virtual-Networks.svg",
    "subnet":  "networking/02742-icon-service-Subnet.svg",
    "vm":      "compute/10021-icon-service-Virtual-Machine.svg",
    "nsg":     "networking/10067-icon-service-Network-Security-Groups.svg",
    "pip":     "networking/10069-icon-service-Public-IP-Addresses.svg",
    "sql":     "databases/10132-icon-service-SQL-Server.svg",
    "bastion": "networking/02422-icon-service-Bastions.svg",
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
  .rg {{ position:absolute; left:40px; top:78px; right:40px; bottom:90px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:46px 26px 26px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; }}
  .tag img {{ width:20px; height:20px; }}
  .vnet {{ position:absolute; left:300px; right:26px; top:46px; bottom:26px;
    border:1.5px solid #2f4159; border-radius:12px; background:#10161f; padding:44px 22px 22px; }}
  .vnet > .tag {{ background:#10161f; color:#7fb0ff; }}
  .subnet {{ position:absolute; top:44px; bottom:22px; width:46%;
    border:1.5px solid #294b6b; border-radius:10px; background:#0d1722; padding:40px 18px 18px; }}
  .subnet.web {{ left:22px; }}
  .subnet.db  {{ right:22px; }}
  .subnet > .tag {{ background:#0d1722; color:#79c0ff; font-size:12px; }}
  .row {{ display:flex; gap:16px; align-items:center; justify-content:center; height:100%; }}
  .node {{ text-align:center; width:128px; }}
  .node img {{ width:54px; height:54px; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:13px; }}
  .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}
  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:2px 7px; font-size:11px; color:#9fb3c8; margin-top:4px; }}
  .flow {{ font-family:ui-monospace,Menlo,monospace; color:#8b98a5; font-size:12px;
    text-align:center; margin-top:6px; }}
  .arrow {{ color:#2f81f7; font-size:26px; align-self:center; }}
  .internet {{ position:absolute; left:40px; top:300px; width:230px; text-align:center; }}
  .internet .globe {{ font-size:54px; }}
  .internet .lbl {{ font-size:14px; }}
  .connector {{ position:absolute; left:48%; right:48%; top:50%; transform:translateY(-50%);
    text-align:center; z-index:5; }}
  .connector .line {{ color:#2f81f7; font-size:30px; font-weight:700; }}
  .connector .port {{ display:block; background:#0e1116; border:1px solid #2f4159;
    border-radius:6px; padding:2px 7px; font-size:11px; color:#3fb950;
    font-family:ui-monospace,Menlo,monospace; margin-top:2px; white-space:nowrap; }}
  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }}
  .legend {{ position:absolute; left:40px; bottom:28px; right:40px; display:flex; gap:22px;
    font-size:12px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
</style></head><body><div class="canvas">
  <h1>Lab 02, Secure 2-Tier Web App <span>· link shortener · one VNet, two subnets, NSG-isolated DB</span></h1>

  <div class="internet">
    <div class="globe">🌐</div>
    <div class="lbl">Internet / browser</div>
    <div class="chip">HTTP :80</div>
    <div class="flow">⬇</div>
    {icon("pip", "Public IP", "vm-web-01 only")}
  </div>

  <div class="rg">
    <div class="tag"><img src="{ic['rg']}"> rg-lab02-cam</div>

    <div class="vnet">
      <div class="tag"><img src="{ic['vnet']}"> vnet-lab02 · 10.0.0.0/16</div>

      <div class="subnet web">
        <div class="tag"><img src="{ic['subnet']}"> snet-web · 10.0.1.0/24</div>
        <div class="row">
          {icon("nsg", "NSG", "allow :80 in")}
          <div class="arrow">→</div>
          {icon("vm", "vm-web-01", "B1s · public")}
        </div>
        <div class="flow">nginx → gunicorn → Flask (pymssql)</div>
      </div>

      <div class="connector">
        <div class="line">→</div>
        <span class="port">:1433</span>
      </div>

      <div class="subnet db">
        <div class="tag"><img src="{ic['subnet']}"> snet-db · 10.0.2.0/24</div>
        <div class="row">
          {icon("nsg", "NSG", "allow :1433 from snet-web only")}
          <div class="arrow">→</div>
          {icon("vm", "vm-db-01", "B2s · no public IP")}
          {icon("sql", "SQL Server", "appdb · dbo.links")}
        </div>
        <div class="flow">10.0.2.4 : 1433</div>
      </div>
    </div>
  </div>

  <div class="legend">
    <span><b>Request path:</b> browser → Public IP → NSG :80 → vm-web-01 → <span class="a-allow">NSG :1433</span> → vm-db-01 → dbo.links</span>
    <span><b>Privacy:</b> DB has <span class="a-deny">no public IP</span>; 1433 reachable only from snet-web</span>
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
