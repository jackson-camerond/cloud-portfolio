#!/usr/bin/env python3
"""
make-diagram.py - Lab 09 architecture diagram.

Unlike the Azure labs, this repo does NOT have an individual per-service AWS
icon set checked in (tools/thumbnailer/badges-library/aws/ has exactly one
generic "aws.png" logo, not per-service SVGs the way azure-icons/ does for
Azure). Rather than fake official icons, each service here is a small
stylized badge using AWS's own per-category brand colors (Lambda orange,
DynamoDB blue, API Gateway / EventBridge pink, CloudWatch teal) with the
service's real short name printed on it. The one real asset available -
the AWS logo - is embedded as the account-boundary tag.

Renders:
  - architecture.html  (self-contained, open it in a browser)
  - architecture.png   (1600x900 @2x, used in the README)
"""
import base64
import os
import subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
AWS_LOGO = os.path.join(REPO, "tools/thumbnailer/badges-library/aws/aws.png")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def data_uri_png(path):
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


AWS_LOGO_URI = data_uri_png(AWS_LOGO)

# One CSS class per AWS category color used in this diagram.
BADGE_COLORS = {
    "lambda": "#ED7100",       # Compute
    "dynamodb": "#4053D6",     # Database
    "apigw": "#E7157B",        # App Integration
    "scheduler": "#8C4FFF",    # App Integration / Networking family (purple)
    "cw": "#2E9E5B",           # decorative teal-green for Management & Governance
}


def badge(key, glyph, label, sub=""):
    color = BADGE_COLORS[key]
    subhtml = f'<div class="sub">{sub}</div>' if sub else ""
    return (
        f'<div class="node">'
        f'<div class="badge" style="background:{color}22;border-color:{color}">'
        f'<span style="color:{color}">{glyph}</span></div>'
        f'<div class="lbl">{label}</div>{subhtml}</div>'
    )


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:32px 40px; }}
  h1 {{ font-size:22px; color:#fff; font-weight:800; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:15px; }}
  .acct {{ position:absolute; left:40px; top:78px; right:40px; bottom:150px;
    border:1.5px dashed #3a4658; border-radius:14px; padding:46px 40px 26px; }}
  .tag {{ position:absolute; top:-13px; left:18px; background:#0e1116; padding:0 10px;
    display:flex; align-items:center; gap:8px; font-weight:700; color:#9fb3c8; font-size:13px; }}
  .tag img {{ width:20px; height:20px; }}
  .lane {{ position:absolute; left:40px; right:40px; height:44%;
    display:flex; align-items:center; justify-content:center; gap:34px; }}
  .lane.top {{ top:34px; }}
  .lane.bottom {{ top:52%; border-top:1.5px dashed #232c38; padding-top:10px; }}
  .lane-tag {{ position:absolute; left:0; top:-4px; font-size:12px; color:#5c6b7a;
    font-weight:700; letter-spacing:.03em; text-transform:uppercase; }}
  .lane.bottom .lane-tag {{ top:16px; }}
  .node {{ text-align:center; width:150px; }}
  .badge {{ width:64px; height:64px; margin:0 auto; border-radius:16px; border:1.5px solid;
    display:flex; align-items:center; justify-content:center; font-size:26px; font-weight:800; }}
  .lbl {{ margin-top:8px; font-weight:700; color:#e6edf3; font-size:13px; }}
  .sub {{ color:#7d8da0; font-size:11px; margin-top:2px; }}
  .arrow {{ color:#2f81f7; font-size:28px; font-weight:700; align-self:center; }}
  .arrow .port {{ display:block; font-size:10px; color:#3fb950; font-family:ui-monospace,Menlo,monospace;
    margin-top:2px; white-space:nowrap; }}
  .actor {{ text-align:center; width:150px; }}
  .actor .glyph {{ font-size:44px; }}
  .actor .lbl {{ font-size:13px; }}
  .legend {{ position:absolute; left:40px; bottom:28px; right:40px; display:flex; flex-direction:column;
    gap:6px; font-size:12px; color:#7d8da0; }}
  .legend b {{ color:#9fb3c8; }}
</style></head><body><div class="canvas">
  <h1>Lab 09 - Serverless API &amp; Automation <span>· AWS · us-west-2 · zero servers, pay-per-use</span></h1>

  <div class="acct">
    <div class="tag"><img src="{AWS_LOGO_URI}"> AWS Account · us-west-2 (no VPC needed - fully managed services)</div>

    <div class="lane top">
      <div class="lane-tag">Live API path</div>
      <div class="actor"><div class="glyph">🌐</div><div class="lbl">Client / curl</div></div>
      <div class="arrow">→<span class="port">HTTPS</span></div>
      {badge("apigw", "API", "API Gateway", "HTTP API · $default stage")}
      <div class="arrow">→<span class="port">AWS_PROXY</span></div>
      {badge("lambda", "λ", "Lambda", "items-api · python3.13")}
      <div class="arrow">→<span class="port">GetItem/PutItem</span></div>
      {badge("dynamodb", "DB", "DynamoDB", "lab09-items · on-demand")}
    </div>

    <div class="lane bottom">
      <div class="lane-tag">Automated daily job - nobody at the keyboard</div>
      {badge("scheduler", "⏰", "EventBridge Scheduler", "cron(0 13 * * ? *)")}
      <div class="arrow">→<span class="port">InvokeFunction</span></div>
      {badge("lambda", "λ", "Lambda", "daily-job · python3.13")}
      <div class="arrow">→<span class="port">Scan(COUNT)</span></div>
      {badge("dynamodb", "DB", "DynamoDB", "same table")}
      <div class="arrow">→</div>
      {badge("cw", "☰", "CloudWatch Logs", "daily summary line")}
    </div>
  </div>

  <div class="legend">
    <span><b>Request path:</b> client → API Gateway (HTTP API) → Lambda (items-api) → DynamoDB - every hop pay-per-use, nothing idle to patch or pay for</span>
    <span><b>Automation path:</b> EventBridge Scheduler fires on a cron, IAM role scoped to invoke ONE function → Lambda (daily-job) scans the table → writes its receipt to CloudWatch Logs</span>
    <span><b>Least privilege:</b> each Lambda's role reaches exactly one DynamoDB table ARN; the scheduler's role can invoke exactly one function ARN</span>
  </div>
</div>
<script>
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
