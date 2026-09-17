#!/usr/bin/env python3
"""
make-diagram.py, Lab 07 architecture diagram from REAL Azure service icons.

Embeds the official Microsoft Azure icon SVGs (rasterized to PNG by headless
Chrome) into a dark-themed diagram and renders:
  - architecture.html  (open it / show it on screen, self-contained)
  - architecture.png   (1600x900 design @2x, drop into the video/post)

Icons come from tools/thumbnailer/azure-icons/extracted/.../Icons. Only the
services actually used in Lab 07 are shown.

Matches the real build: rg-lab07-cam holds ACR (acrlab07cam) and the AKS
cluster (aks-lab07-cam, --tier free, managed identity + --attach-acr). AKS
auto-creates a second resource group (MC_rg-lab07-cam_aks-lab07-cam_westus2)
for the node pool VMs, disks, NICs, and the Standard Load Balancer the
type:LoadBalancer Service provisions. The Deployment (2 replicas, aks-demo
namespace) runs behind that Service; the HPA scales it 2→10 on 50% CPU;
Container Insights (Log Analytics) watches the cluster.
"""
import os, base64, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ICONS = os.path.join(REPO, "tools/thumbnailer/azure-icons/extracted",
                     "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_FILES = {
    "rg":       "general/10007-icon-service-Resource-Groups.svg",
    "acr":      "containers/10105-icon-service-Container-Registries.svg",
    "aks":      "containers/10023-icon-service-Kubernetes-Services.svg",
    "vm":       "compute/10021-icon-service-Virtual-Machine.svg",
    "lb":       "networking/10062-icon-service-Load-Balancers.svg",
    "pip":      "networking/10069-icon-service-Public-IP-Addresses.svg",
    "identity": "identity/10227-icon-service-Managed-Identities.svg",
    "monitor":  "monitor/00001-icon-service-Monitor.svg",
    "pod":      "containers/10104-icon-service-Container-Instances.svg",
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
  .rg {{ position:absolute; left:300px; top:78px; right:40px; bottom:96px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:46px 24px 20px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; }}
  .tag img {{ width:20px; height:20px; }}

  .acrbox {{ position:absolute; left:20px; top:44px; bottom:20px; width:190px;
    border:1.5px solid #2f4159; border-radius:12px; background:#10161f; padding:40px 12px 14px;
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; }}
  .acrbox > .tag {{ background:#10161f; color:#7fb0ff; font-size:12px; left:12px; }}

  .cluster {{ position:absolute; left:236px; right:24px; top:44px; bottom:20px;
    border:1.5px solid #2f4159; border-radius:12px; background:#10161f; padding:44px 22px 16px;
    display:flex; flex-direction:column; justify-content:center; gap:10px; }}
  .cluster > .tag {{ background:#10161f; color:#7fb0ff; }}

  .lbrow {{ display:flex; align-items:center; justify-content:center; gap:18px; margin-bottom:10px; }}

  .mcbox {{ position:relative; border:1.5px solid #294b6b; border-radius:10px;
    background:#0d1722; padding:36px 18px 16px; margin-top:8px; }}
  .mcbox > .tag {{ position:absolute; top:-13px; left:16px; background:#0d1722; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#79c0ff; font-size:11.5px; }}
  .mcbox > .tag img {{ width:18px; height:18px; }}

  .noderow {{ display:flex; gap:28px; align-items:flex-start; justify-content:center; }}
  .nodebox {{ border:1.5px dashed #3a4658; border-radius:10px; padding:14px 16px 10px;
    text-align:center; background:#0e1620; }}
  .nodebox .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:13px; }}
  .nodebox .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}
  .podrow {{ display:flex; gap:8px; margin-top:10px; justify-content:center; }}
  .podrow img {{ width:30px; height:30px; opacity:.92; }}

  .row {{ display:flex; gap:16px; align-items:center; justify-content:center; }}
  .node {{ text-align:center; width:128px; }}
  .node img {{ width:50px; height:50px; }}
  .lbl {{ margin-top:6px; font-weight:700; color:#e6edf3; font-size:13px; }}
  .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}
  .chip {{ display:inline-block; background:#161b22; border:1px solid #2a313c;
    border-radius:6px; padding:2px 7px; font-size:11px; color:#9fb3c8; margin-top:4px; }}
  .flow {{ font-family:ui-monospace,Menlo,monospace; color:#8b98a5; font-size:11.5px;
    text-align:center; margin-top:6px; }}
  .arrow {{ color:#2f81f7; font-size:24px; align-self:center; }}
  .hpa {{ display:inline-block; margin-top:10px; background:#132a1c; border:1px solid #2ea043;
    border-radius:6px; padding:4px 10px; font-size:11.5px; color:#7ee787; font-weight:700; }}

  .internet {{ position:absolute; left:40px; top:280px; width:240px; text-align:center; }}
  .internet .globe {{ font-size:54px; }}
  .internet .lbl {{ font-size:14px; }}


  .insights {{ position:absolute; right:36px; top:96px; width:170px; text-align:center;
    border:1.5px solid #2a313c; border-radius:10px; background:#161b22; padding:12px 8px 10px; }}
  .insights img {{ width:34px; height:34px; }}
  .insights .lbl {{ font-size:12px; margin-top:4px; }}
  .insights .sub {{ font-size:10.5px; }}
  .i-line {{ position:absolute; right:118px; top:150px; width:2px; height:auto; }}

  .legend {{ position:absolute; left:40px; bottom:24px; right:40px; display:flex; flex-direction:column;
    gap:5px; font-size:12px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
  .a-allow {{ color:#3fb950; }} .a-deny {{ color:#f78f8f; }} .a-scale {{ color:#7ee787; }}
</style></head><body><div class="canvas">
  <h1>Lab 07, Containerized App on Kubernetes (AKS) <span>· self-healing, load-balanced, autoscaling on CPU, nobody at the keyboard</span></h1>

  <div class="internet">
    <div class="globe">🌐</div>
    <div class="lbl">Internet / browser</div>
    <div class="chip">HTTP :80</div>
    <div class="flow">⬇</div>
    {icon("pip", "Public IP", "Service: LoadBalancer")}
  </div>

  <div class="rg">
    <div class="tag"><img src="{ic['rg']}"> rg-lab07-cam · westus2</div>

    <div class="acrbox">
      <div class="tag"><img src="{ic['acr']}"> ACR</div>
      {icon("acr", "acrlab07cam", "Basic tier")}
      <div class="chip">aks-demo-api:v1</div>
      <div class="flow">az acr build<br>(no local docker)</div>
    </div>

    <div class="cluster">
      <div class="tag"><img src="{ic['aks']}"> aks-lab07-cam · AKS (--tier free)</div>
      <div class="flow" style="margin-bottom:8px;">control plane, Azure-managed (API server, scheduler, etcd) · --enable-managed-identity</div>
      <div class="flow" style="margin-bottom:8px; color:#f0883e;">← nodes pull <span class="chip" style="margin:0 2px;">acrlab07cam</span> images via AcrPull (cluster's managed identity, --attach-acr, zero stored credentials)</div>

      <div class="lbrow">
        {icon("lb", "Load Balancer", "Standard · public IP")}
        <div class="arrow">→</div>
        <div class="node"><div class="lbl">Service</div><div class="sub">aks-demo-api · type LoadBalancer</div><div class="chip">selector app=aks-demo-api</div></div>
      </div>

      <div class="mcbox">
        <div class="tag"><img src="{ic['vm']}"> MC_rg-lab07-cam_aks-lab07-cam_westus2 · node pool (auto-managed, never edit)</div>
        <div class="noderow">
          <div class="nodebox">
            {icon("vm", "node-1", "Standard_D2s_v4")}
            <div class="podrow">{f'<img src="{ic["pod"]}">' * 1}</div>
            <div class="sub">ns: aks-demo</div>
          </div>
          <div class="nodebox">
            {icon("vm", "node-2", "Standard_D2s_v4")}
            <div class="podrow">{f'<img src="{ic["pod"]}">' * 1}</div>
            <div class="sub">ns: aks-demo</div>
          </div>
          <div class="nodebox" style="border-style:solid;">
            <div class="lbl">Deployment</div>
            <div class="sub">aks-demo-api</div>
            <div class="podrow">{f'<img src="{ic["pod"]}">' * 3}</div>
            <div class="sub">:8080 · readiness/liveness /healthz</div>
            <div class="hpa">HPA 2 → 10 replicas @ 50% CPU</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="insights">
    {icon("monitor", "Container Insights", "Log Analytics workspace")}
  </div>

  <div class="legend">
    <span><b>Request path:</b> browser → Public IP :80 → Load Balancer → Service (selector <code>app=aks-demo-api</code>) → Pod :8080 (namespace <span class="a-allow">aks-demo</span>)</span>
    <span><b>Pull path:</b> nodes ← <span class="a-allow">ACR (AcrPull via cluster managed identity, zero stored credentials)</span></span>
    <span><b>Self-healing vs. autoscaling:</b> Deployment restores the replica count when a pod dies · <span class="a-scale">HPA moves the count itself</span> as CPU crosses 50% (metrics-server) · Container Insights watches it all, no agent installed by hand</span>
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
