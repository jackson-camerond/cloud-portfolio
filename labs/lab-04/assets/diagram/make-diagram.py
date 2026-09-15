#!/usr/bin/env python3
"""
make-diagram.py — Lab 04 architecture diagram from REAL Azure service icons.

Embeds the official Microsoft Azure icon SVGs (rasterized to PNG by headless
Chrome) into a dark-themed diagram and renders:
  - architecture.html  (open it / show it on screen — self-contained)
  - architecture.png   (1600x900 design @2x — drop into the video/post)

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
resources this lab's Terraform config actually builds are shown:
  rg-lab04-tf-cam -> vnet-terraform -> snet-backend -> nsg-web (+ association)
Terraform itself is not an Azure service, so the CLI/build side uses a text
node (same convention the exemplar uses 🌐 for "Internet").
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":     "general/10007-icon-service-Resource-Groups.svg",
    "vnet":   "networking/10061-icon-service-Virtual-Networks.svg",
    "subnet": "networking/02742-icon-service-Subnet.svg",
    "nsg":    "networking/10067-icon-service-Network-Security-Groups.svg",
    "cli":    "other/00559-icon-service-Azure-Cloud-Shell.svg",
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

  .rg {{ position:absolute; left:340px; top:78px; right:40px; bottom:96px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:46px 26px 26px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; }}
  .tag img {{ width:20px; height:20px; }}

  .vnet {{ position:absolute; left:22px; right:22px; top:46px; bottom:22px;
    border:1.5px solid #2f4159; border-radius:12px; background:#10161f; padding:44px 22px 22px; }}
  .vnet > .tag {{ background:#10161f; color:#7fb0ff; }}

  .subnet {{ position:absolute; left:22px; right:22px; top:44px; height:250px;
    border:1.5px solid #294b6b; border-radius:10px; background:#0d1722; padding:40px 26px 18px; }}
  .subnet > .tag {{ background:#0d1722; color:#79c0ff; font-size:12px; }}

  .row {{ display:flex; gap:22px; align-items:center; justify-content:center; height:66%; }}
  .node {{ text-align:center; width:190px; }}
  .node img {{ width:54px; height:54px; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:13px; }}
  .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}

  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:2px 7px; font-size:11px; color:#9fb3c8; margin-top:4px; }}
  .chip.allow {{ color:#3fb950; border-color:#204d2c; }}
  .chip.deny  {{ color:#f78f8f; border-color:#5a2b2b; }}
  .flow {{ font-family:ui-monospace,Menlo,monospace; color:#8b98a5; font-size:12px;
    text-align:center; margin-top:6px; }}
  .arrow {{ color:#2f81f7; font-size:26px; align-self:center; }}
  .note {{ position:absolute; left:26px; right:26px; bottom:6px; text-align:center;
    color:#5c6b7a; font-size:11px; font-style:italic; }}

  .graph {{ position:absolute; left:22px; right:22px; top:314px; bottom:22px;
    border:1.5px dashed #2a3546; border-radius:10px; background:#0d131c;
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; }}
  .graph .cap {{ font-size:12px; color:#7d8da0; font-weight:700; }}
  .chain {{ display:flex; align-items:center; gap:10px; }}
  .pill {{ background:#161b22; border:1px solid #2f4159; border-radius:20px;
    padding:7px 16px; font-size:12.5px; font-weight:700; color:#d6deeb; white-space:nowrap; }}
  .chain .arrow {{ font-size:18px; }}
  .graph .dirs {{ display:flex; gap:34px; font-size:11px; color:#7d8da0; }}
  .graph .dirs b {{ color:#79c0ff; }}

  .side {{ position:absolute; left:36px; width:260px; text-align:center; }}
  .side .glyph {{ font-size:46px; }}
  .side .lbl {{ font-size:14px; }}
  .side .box {{ border:1px solid #2a313c; border-radius:10px; background:#12161d;
    padding:14px 12px; margin-top:8px; }}

  .build {{ top:82px; }}
  .internet {{ top:436px; }}

  .hconn {{ position:absolute; left:300px; width:36px; text-align:center; }}
  .hconn .line {{ color:#2f81f7; font-size:26px; font-weight:700; }}
  .hconn .port {{ display:block; background:#0e1116; border:1px solid #2f4159;
    border-radius:6px; padding:2px 6px; font-size:10.5px; color:#79c0ff;
    font-family:ui-monospace,Menlo,monospace; margin-top:2px; white-space:nowrap; }}
  .hconn .port.allow {{ color:#3fb950; }}
  .build-conn {{ top:200px; }}
  .net-conn   {{ top:500px; }}

  .legend {{ position:absolute; left:40px; right:40px; bottom:26px; display:flex;
    flex-direction:column; gap:5px; font-size:12.5px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }}
</style></head><body><div class="canvas">
  <h1>Lab 04 — Infrastructure as Code (Terraform) <span>· same network as a click-ops build, defined in .tf files and applied by the azurerm provider</span></h1>

  <div class="side build">
    <div class="glyph">💻</div>
    <div class="lbl">Terraform CLI (local)</div>
    <div class="box">
      <div class="chip">init → plan → apply → destroy</div><br>
      <div class="chip">🔑 az login (cached token)</div><br>
      <div class="chip">📄 terraform.tfstate<br>local · gitignored · never committed</div>
      <div class="flow">via azurerm provider<br>→ Azure Resource Manager API</div>
    </div>
  </div>

  <div class="hconn build-conn">
    <div class="line">→</div>
  </div>

  <div class="side internet">
    <div class="glyph">🌐</div>
    <div class="lbl">Internet</div>
    <div class="box">
      <div class="chip">HTTP request, port 80</div>
    </div>
  </div>

  <div class="hconn net-conn">
    <div class="line">→</div>
    <span class="port allow">:80 allow</span>
  </div>

  <div class="rg">
    <div class="tag"><img src="{ic['rg']}"> rg-lab04-tf-cam · East US</div>

    <div class="vnet">
      <div class="tag"><img src="{ic['vnet']}"> vnet-terraform · 10.0.0.0/16</div>

      <div class="subnet">
        <div class="tag"><img src="{ic['subnet']}"> snet-backend · 10.0.1.0/24</div>
        <div class="row">
          {icon("nsg", "nsg-web", "subnet_nsg association")}
          <div class="arrow">→</div>
          <div class="node">
            <div class="lbl">Allow-HTTP-Inbound</div>
            <div class="chip allow">priority 100 · Tcp :80 · src *</div>
            <div class="chip deny">everything else → default DenyAllInBound</div>
          </div>
        </div>
        <div class="note">network-only lab — no VM/public IP yet; this subnet is where later compute would attach</div>
      </div>

      <div class="graph">
        <div class="cap">Terraform dependency graph — derived from references, not written by hand</div>
        <div class="chain">
          <span class="pill">azurerm_resource_group.rg</span>
          <span class="arrow">→</span>
          <span class="pill">azurerm_virtual_network.vnet</span>
          <span class="arrow">→</span>
          <span class="pill">azurerm_subnet.subnet</span>
          <span class="arrow">→</span>
          <span class="pill">azurerm_network_security_group.nsg</span>
          <span class="arrow">→</span>
          <span class="pill">subnet_nsg association</span>
        </div>
        <div class="dirs"><span><b>apply</b> walks this left → right</span><span><b>destroy</b> walks it right → left</span></div>
      </div>
    </div>
  </div>

  <div class="legend">
    <span><b>Build path:</b> 💻 terraform apply → azurerm provider (borrows the Azure CLI's <code>az login</code> token, no secrets in code) → Azure Resource Manager → creates <b>rg-lab04-tf-cam</b> → <b>vnet-terraform</b> → <b>snet-backend</b> → <b>nsg-web</b> → subnet association, in the order the resource <i>references</i> imply — <code>destroy</code> walks the same graph backward. State recorded only in local <code>terraform.tfstate</code> (gitignored).</span>
    <span><b>Traffic path:</b> 🌐 Internet → <span class="a-allow">nsg-web allow-rule :80</span> → snet-backend; every other inbound port hits the NSG's built-in <span class="a-deny">DenyAllInBound</span>.</span>
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
