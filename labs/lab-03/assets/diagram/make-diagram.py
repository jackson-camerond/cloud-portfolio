#!/usr/bin/env python3
"""
make-diagram.py — Lab 03 architecture flowchart from REAL Azure service icons.

Embeds the official Microsoft Azure icon SVGs into a dark-themed diagram and
renders:
  - architecture.html  (open it / show it on screen — self-contained)
  - architecture.png   (1600x900 design, 2x device scale — drop into the video)

Shows the actual Lab 03 build: the Lab 02 VM stack (rg-lab02-cam) still
running vm-web-01, with vm-db-01 decommissioned in place of the new PaaS
side (rg-lab03-cam): Azure SQL Database behind a logical server, Key Vault,
the managed-identity/IMDS secret fetch, and Azure Monitor watching the DB.

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
services actually used in Lab 03 are shown.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":       "general/10007-icon-service-Resource-Groups.svg",
    "vnet":     "networking/10061-icon-service-Virtual-Networks.svg",
    "subnet":   "networking/02742-icon-service-Subnet.svg",
    "vm":       "compute/10021-icon-service-Virtual-Machine.svg",
    "nsg":      "networking/10067-icon-service-Network-Security-Groups.svg",
    "pip":      "networking/10069-icon-service-Public-IP-Addresses.svg",
    "sqlsrv":   "databases/10132-icon-service-SQL-Server.svg",
    "sqldb":    "databases/10130-icon-service-SQL-Database.svg",
    "keyvault": "security/10245-icon-service-Key-Vaults.svg",
    "identity": "identity/10227-icon-service-Managed-Identities.svg",
    "monitor":  "management + governance/00001-icon-service-Monitor.svg",
}


def data_uri(rel):
    with open(os.path.join(ICONS, rel), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ic = {k: data_uri(v) for k, v in ICON_FILES.items()}


def icon(key, label, sub="", size=54, extra_class=""):
    subhtml = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="node {extra_class}"><img src="{ic[key]}" alt="{label}" '
            f'style="width:{size}px;height:{size}px">'
            f'<div class="lbl">{label}</div>{subhtml}</div>')


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:28px 40px; }}
  h1 {{ font-size:21px; color:#fff; font-weight:800; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:14px; }}

  .rg {{ position:absolute; top:82px; bottom:112px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:44px 20px 16px; }}
  .rg.old {{ left:246px; width:556px; }}
  .rg.new {{ left:1028px; right:40px; }}
  .tag {{ position:absolute; top:-13px; left:16px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:7px; font-weight:700; color:#9fb3c8; font-size:12.5px;
    white-space:nowrap; }}
  .tag img {{ width:18px; height:18px; }}
  .tag.faded {{ color:#6a7686; }}

  .vnet {{ position:absolute; left:16px; right:16px; top:42px; bottom:16px;
    border:1.5px solid #2f4159; border-radius:12px; background:#10161f; padding:40px 14px 14px; }}
  .vnet > .tag {{ background:#10161f; color:#7fb0ff; }}
  .subnet {{ position:absolute; top:38px; bottom:14px; width:47%;
    border:1.5px solid #294b6b; border-radius:10px; background:#0d1722; padding:36px 12px 10px; }}
  .subnet.web {{ left:14px; }}
  .subnet.db  {{ right:14px; }}
  .subnet > .tag {{ background:#0d1722; color:#79c0ff; font-size:11px; }}

  .col {{ display:flex; flex-direction:column; align-items:center; gap:8px; height:100%;
    justify-content:center; }}
  .row {{ display:flex; gap:12px; align-items:center; justify-content:center; }}
  .node {{ text-align:center; width:112px; }}
  .node img {{ display:block; margin:0 auto; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:12.5px; }}
  .sub {{ color:#7d8da0; font-size:10.5px; margin-top:2px; line-height:1.3; }}
  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:2px 7px; font-size:10.5px; color:#9fb3c8; margin-top:4px; }}
  .chip.mi {{ border-color:#3d3560; color:#c9b8ff; }}
  .chip.secret {{ border-color:#3d5a3d; color:#8ce38c; }}
  .flow {{ font-family:ui-monospace,Menlo,monospace; color:#8b98a5; font-size:11px;
    text-align:center; margin-top:4px; }}
  .arrow {{ color:#2f81f7; font-size:22px; align-self:center; }}

  .decom {{ opacity:0.42; filter:grayscale(1); }}
  .decom .lbl {{ text-decoration:line-through; color:#9aa4b0; }}
  .decom-tag {{ margin-top:3px; font-size:9px; color:#f78f8f; font-weight:700;
    border:1px solid #5a2f2f; border-radius:5px; padding:2px 6px; display:inline-block;
    max-width:150px; white-space:normal; text-align:center; line-height:1.3; }}

  .internet {{ position:absolute; left:40px; top:300px; width:210px; text-align:center; }}
  .internet .globe {{ font-size:50px; }}
  .internet .lbl {{ font-size:13px; }}

  .connector {{ position:absolute; left:812px; width:200px; top:394px;
    text-align:center; z-index:5; }}
  .connector .line {{ color:#2f81f7; font-size:26px; font-weight:700; }}
  .connector .port {{ display:block; background:#0e1116; border:1px solid #2f4159;
    border-radius:6px; padding:2px 7px; font-size:10.5px; color:#3fb950;
    font-family:ui-monospace,Menlo,monospace; margin-top:2px; white-space:nowrap; }}

  .paas-row {{ position:absolute; left:16px; right:16px; border:1.5px solid #4b3f22;
    border-radius:10px; background:#1a1508; }}
  .paas-row.sql {{ top:42px; height:34%; padding:34px 14px 10px; }}
  .paas-row.kv  {{ top:calc(42px + 34% + 14px); height:30%; padding:34px 14px 10px; }}
  .paas-row > .tag {{ background:#1a1508; color:#e0b95c; font-size:11px; }}
  .mon-row {{ position:absolute; left:16px; right:16px; top:calc(42px + 34% + 14px + 30% + 14px);
    bottom:14px; display:flex; align-items:center; justify-content:center; gap:14px; }}

  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }}
  .legend {{ position:absolute; left:40px; bottom:22px; right:40px; display:flex;
    flex-direction:column; gap:5px; font-size:11.5px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
  .mi-label {{ color:#c9b8ff; }}

  svg.overlay {{ position:absolute; left:0; top:0; width:1600px; height:900px; z-index:4;
    pointer-events:none; }}
  .flowA-txt {{ position:absolute; font-size:11px; color:#c9b8ff; font-family:ui-monospace,Menlo,monospace;
    text-align:center; z-index:6; background:#0e1116; padding:1px 6px; border-radius:4px; }}
</style></head><body><div class="canvas">
  <h1>Lab 03 — PaaS Modernization &amp; Secrets <span>· link shortener · DB moves to Azure SQL (PaaS), password moves to Key Vault via managed identity</span></h1>

  <div class="internet">
    <div class="globe">🌐</div>
    <div class="lbl">Internet / browser</div>
    <div class="chip">HTTP :80</div>
    <div class="flow">⬇</div>
    {icon("pip", "Public IP", "vm-web-01 only", size=44)}
  </div>

  <div class="rg old">
    <div class="tag"><img src="{ic['rg']}"> rg-lab02-cam <span style="color:#5c6b7a;font-weight:500;">· existing VM stack, still running</span></div>
    <div class="vnet">
      <div class="tag"><img src="{ic['vnet']}"> vnet-lab02 · 10.0.0.0/16</div>

      <div class="subnet web">
        <div class="tag"><img src="{ic['subnet']}"> snet-web · 10.0.1.0/24</div>
        <div class="col">
          <div class="row">
            {icon("nsg", "NSG", "allow :80 in", size=40)}
            <div class="arrow">→</div>
            {icon("vm", "vm-web-01", "B1s · public", size=48)}
          </div>
          <div class="chip mi">🪪 system-assigned managed identity</div>
          <div class="flow">nginx → gunicorn → Flask (pymssql)</div>
        </div>
      </div>

      <div class="subnet db">
        <div class="tag"><img src="{ic['subnet']}"> snet-db · 10.0.2.0/24</div>
        <div class="col">
          <div class="node decom">
            <img src="{ic['vm']}" alt="vm-db-01" style="width:48px;height:48px">
            <div class="lbl">vm-db-01</div>
            <div class="sub">SQL Server on B2s</div>
          </div>
          <div class="decom-tag">✕ DECOMMISSIONED · step 7</div>
          <div class="flow">replaced by Azure SQL →</div>
        </div>
      </div>
    </div>
  </div>

  <div class="connector">
    <div class="line">— TLS/TDS →</div>
    <div class="port">:1433 · sql-lab03-cam.database.windows.net</div>
  </div>

  <div class="rg new">
    <div class="tag"><img src="{ic['rg']}"> rg-lab03-cam <span style="color:#5c6b7a;font-weight:500;">· new · West US 2 · PaaS, no VNet</span></div>

    <div class="paas-row sql">
      <div class="tag"><img src="{ic['sqlsrv']}"> public endpoint + firewall <span style="color:#8b98a5;font-weight:500;">(Azure services ✓ · client IP ✓ · TLS 1.2+ only)</span></div>
      <div class="row">
        {icon("sqlsrv", "sql-lab03-cam", "logical server · admin sqladmin", size=50)}
        <div class="arrow">→</div>
        {icon("sqldb", "sqldb-app", "Basic · 5 DTU · appuser (contained user)", size=50)}
      </div>
    </div>

    <div class="paas-row kv">
      <div class="tag"><img src="{ic['keyvault']}"> kv-lab03-cam <span style="color:#8b98a5;font-weight:500;">· Standard · RBAC · purge protection off</span></div>
      <div class="row">
        {icon("keyvault", "Key Vault", "RBAC: Secrets User → vm-web-01", size=48)}
        <div class="chip secret">🔑 secret: DbAppPassword</div>
      </div>
    </div>

    <div class="mon-row">
      {icon("monitor", "Azure Monitor", "sqldb-app → DTU % (Max)", size=38)}
      <span style="color:#5c6b7a;font-size:11px;">platform metrics · free · proves the managed DB is alive</span>
    </div>
  </div>

  <svg class="overlay" viewBox="0 0 1600 900">
    <defs>
      <marker id="arrM" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L7,3 z" fill="#c9b8ff"/>
      </marker>
    </defs>
    <path d="M 676 460 C 800 640, 1220 700, 1440 560" fill="none" stroke="#7a5cc7"
      stroke-width="2" stroke-dasharray="5 4" marker-end="url(#arrM)"/>
  </svg>
  <div class="flowA-txt" style="left:770px; top:640px;">Flow A · service start: IMDS 169.254.169.254 → bearer token → GET secret (RBAC checked)</div>

  <div class="legend">
    <span><b>Flow B · request:</b> browser → Public IP → NSG :80 → vm-web-01 (nginx/gunicorn/Flask) → <span class="a-allow">TLS/TDS :1433</span> → sql-lab03-cam gateway → firewall check → sqldb-app as <code>appuser</code> → rows render</span>
    <span><b>Flow A · secret fetch (service start):</b> ExecStartPre runs fetch-db-pass.sh → <span class="mi-label">IMDS (link-local, no auth needed)</span> → Entra ID signs token for vm-web-01's identity → Key Vault checks RBAC (Secrets User) → value written to <code>/run/links/db.env</code> (tmpfs/RAM only, never disk)</span>
    <span><b>Exposure trade:</b> sqldb-app has a <span class="a-deny">public endpoint</span> (firewalled + TLS-only) — no VNet needed, no OS to attack; production answer would be a Private Endpoint</span>
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
