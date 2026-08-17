#!/usr/bin/env python3
"""
make-diagram.py - Lab 08 architecture diagram (End-to-End CI/CD Pipeline).

Unlike the Azure labs, this repo doesn't vendor a per-service AWS icon set
(only tools/thumbnailer/badges-library/aws/aws.png, one generic logo) - so
this diagram is drawn with plain CSS boxes + the AWS brand color (#FF9900)
instead of official per-service glyphs. Same dark 1600x900 canvas, same
boundary/flow-arrow convention as the other AWS labs (see labs/lab-12).

Two stacked panels:
  1. The GitHub Actions pipeline itself (jobs, gates, the approval).
  2. The AWS account it deploys into (IAM/OIDC, default VPC, ALB, ECS
     Fargate across two AZs, ECR, CloudWatch Logs).

Renders:
  - architecture.html  (self-contained, open it directly)
  - architecture.png    (headless-Chrome screenshot, drop into the video)
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


aws_logo = data_uri_png(AWS_LOGO)

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; padding:32px 40px; }}
  h1 {{ font-size:21px; color:#fff; font-weight:800; display:flex; align-items:center; gap:10px; }}
  h1 img {{ width:24px; height:24px; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:14px; }}

  .region {{ position:absolute; border:1.5px dashed #3a4658; border-radius:14px; }}
  .tag {{ position:absolute; top:-12px; left:18px; background:#0e1116; padding:0 10px;
    font-weight:700; color:#9fb3c8; font-size:12.5px; }}

  .box {{ position:absolute; border:1.5px solid #2f4159; border-radius:10px; background:#10161f;
    padding:8px 12px; overflow:hidden; }}
  .box .name {{ font-weight:800; color:#e6edf3; font-size:13.5px; }}
  .box .sub {{ color:#8a9bb0; font-size:11px; margin-top:2px; line-height:1.3; }}
  .box .icon {{ font-size:20px; }}

  .amber {{ border-color:#ff9900; background:#231a0d; }}
  .amber .name {{ color:#ffb84d; }}
  .amber .sub {{ color:#c99a55; }}

  .green {{ border-color:#2ea043; background:#0f1c12; }}
  .green .name {{ color:#5fd97a; }}
  .green .sub {{ color:#7fae8c; }}

  .dim {{ border-style:dashed; opacity:.6; }}

  .chip {{ display:inline-block; background:#0e1116; border:1px solid #3a4658; border-radius:5px;
    padding:1px 7px; font-size:10px; color:#9fb3c8; font-family:ui-monospace,Menlo,monospace;
    margin:2px 4px 0 0; }}
  .chip.warn {{ border-color:#f7b955; color:#f7b955; }}
  .chip.ok {{ border-color:#3fb950; color:#3fb950; }}

  .arrow {{ position:absolute; color:#2f81f7; font-size:22px; font-weight:700; text-align:center; }}
  .arrow.small {{ font-size:16px; }}
  .flowlbl {{ position:absolute; font-size:10.5px; color:#5c9fe6; text-align:center;
    font-family:ui-monospace,Menlo,monospace; }}
  .stacklbl {{ position:absolute; font-size:10.5px; color:#7d8da0; text-align:center; }}

  .legend {{ position:absolute; left:40px; right:40px; bottom:14px; display:flex; flex-direction:column;
    gap:5px; font-size:11.5px; color:#9fb3c8; }}
  .legend b {{ color:#e6edf3; }}
  .a-ok {{ color:#3fb950; }} .a-warn {{ color:#f7b955; }}
</style></head><body><div class="canvas">
  <h1><img src="{aws_logo}" alt="AWS"> Lab 08 - End-to-End CI/CD Pipeline
    <span>· GitHub Actions builds, scans, and gates every change behind a human approval before it reaches ECS Fargate</span></h1>

  <!-- ============================= REGION A - CI/CD pipeline ============================= -->
  <div class="region" style="left:40px; top:84px; width:1520px; height:264px;">
    <div class="tag">GitHub Actions · .github/workflows/ci-cd.yml · repo: cam/portfolio</div>

    <div class="box" style="left:24px; top:92px; width:150px; height:104px; text-align:center;">
      <div class="icon">🔀</div>
      <div class="name" style="margin-top:4px;">push / PR</div>
      <div class="sub">any branch → main</div>
    </div>

    <div class="arrow" style="left:186px; top:132px; width:26px;">→</div>

    <div class="stacklbl" style="left:222px; top:108px; width:320px;">runs in parallel · hard gate - all must pass</div>
    <div class="box" style="left:222px; top:130px; width:320px; height:50px;">
      <div class="name" style="font-size:12.5px;">terraform-plan</div>
      <div class="sub">gha-plan role (read-only) · fmt / validate / plan</div>
    </div>
    <div class="box" style="left:222px; top:188px; width:320px; height:50px;">
      <div class="name" style="font-size:12.5px;">checkov</div>
      <div class="sub">IaC scan · soft_fail:false · 13 named skip_check IDs</div>
    </div>
    <div class="box" style="left:222px; top:246px; width:320px; height:50px;">
      <div class="name" style="font-size:12.5px;">trivy</div>
      <div class="sub">image scan · builds locally · fails on CRITICAL/HIGH</div>
    </div>

    <div class="arrow" style="left:554px; top:194px; width:26px;">→</div>

    <div class="box amber" style="left:590px; top:150px; width:216px; height:150px; text-align:center;">
      <div class="icon">🔒</div>
      <div class="name" style="margin-top:4px; font-size:13px;">production environment</div>
      <div class="sub">GitHub Environment protection rule -<br>required reviewer must approve</div>
    </div>

    <div class="arrow" style="left:816px; top:194px; width:26px;">→</div>

    <div class="box" style="left:852px; top:120px; width:628px; height:210px;">
      <div class="name">deploy job <span style="font-weight:500;color:#7d8da0;font-size:11px;">- needs: plan, checkov, trivy</span></div>
      <div class="sub" style="margin-top:8px;">
        <b style="color:#e6edf3;">1</b> · assume <b style="color:#ffb84d;">gha-deploy</b> role - sts:AssumeRoleWithWebIdentity<br>
        &nbsp;&nbsp;&nbsp;(OIDC token sub = repo:cam/portfolio:environment:production)<br>
        <b style="color:#e6edf3;">2</b> · docker build &amp; push → ECR, tag <span class="chip">{{sha}}-{{run_number}}</span><br>
        <b style="color:#e6edf3;">3</b> · terraform apply -var image_tag=... (terraform/app)<br>
        <b style="color:#e6edf3;">4</b> · aws ecs wait services-stable
      </div>
    </div>
  </div>

  <div class="arrow" style="left:1090px; top:352px; width:280px; font-size:18px;">⬇</div>
  <div class="flowlbl" style="left:900px; top:378px; width:660px;">temporary AWS credentials (~1 hr, OIDC-issued) → ECR push · terraform apply · ECS deploy</div>

  <!-- ============================= REGION B - AWS account ============================= -->
  <div class="region" style="left:40px; top:398px; width:1520px; height:406px;">
    <div class="tag">AWS Account · us-west-2 · OIDC-federated - no stored AWS access keys</div>

    <!-- IAM / bootstrap column - coords below are relative to THIS region's own box -->
    <div class="region" style="left:24px; top:36px; width:276px; height:352px; border-color:#2f4159;">
      <div class="tag" style="background:#0e1116; color:#7fb0ff;">IAM · bootstrap root (human-applied, once)</div>
      <div class="box" style="left:16px; top:28px; width:244px; height:52px;">
        <div class="name" style="font-size:12px;">OIDC Provider</div>
        <div class="sub">token.actions.githubusercontent.com</div>
      </div>
      <div class="box" style="left:16px; top:88px; width:244px; height:52px;">
        <div class="name" style="font-size:12px;">gha-plan role</div>
        <div class="sub">read-only · sub: repo:cam/portfolio:*</div>
      </div>
      <div class="box amber" style="left:16px; top:148px; width:244px; height:60px;">
        <div class="name" style="font-size:12px;">gha-deploy role</div>
        <div class="sub" style="font-size:10px;">sub: repo:cam/portfolio:<br>environment:production</div>
      </div>
      <div class="box" style="left:16px; top:216px; width:244px; height:52px;">
        <div class="name" style="font-size:12px;">ecs-execution role</div>
        <div class="sub">AmazonECSTaskExecutionRolePolicy</div>
      </div>
      <div class="box dim" style="left:16px; top:276px; width:244px; height:52px;">
        <div class="name" style="font-size:12px;">ecs-task role</div>
        <div class="sub">no policies attached - least privilege</div>
      </div>
    </div>

    <!-- Default VPC - coords below are relative to THIS region's own box -->
    <div class="region" style="left:324px; top:36px; width:900px; height:352px; border-color:#294b6b; background:#0d1722;">
      <div class="tag" style="background:#0d1722; color:#79c0ff;">Default VPC · 2 default public subnets, 2 AZs · no NAT Gateway</div>

      <div class="box amber" style="left:24px; top:32px; width:852px; height:80px;">
        <div class="name">lab08-cicd-alb</div>
        <div class="sub">internet-facing · sg-lab08-cicd-alb (0.0.0.0/0 : 80 in) · listener :80 → target group :8080 (health check GET /health)</div>
      </div>

      <div class="flowlbl" style="left:396px; top:116px; width:60px;">:8080 ⇓</div>

      <!-- AZ boxes - coords relative to THIS az box -->
      <div class="region" style="left:24px; top:154px; width:410px; height:180px; border-color:#294b6b;">
        <div class="tag" style="background:#0d1722; color:#79c0ff; font-size:11px;">us-west-2a · default subnet</div>
        <div class="box green" style="left:16px; top:24px; width:378px; height:140px;">
          <div class="name" style="font-size:12.5px;">ECS Fargate task <span style="color:#7fae8c;font-weight:500;">· lab08-cicd-app:svc</span></div>
          <div class="sub">ARM64 (Graviton) · 256 CPU / 512 MiB · assign_public_ip=true</div>
          <div style="margin-top:5px;">
            <span class="chip ok">sg-app: ALB→:8080 only</span>
            <span class="chip ok">egress 443 only</span><br>
            <span class="chip">image: lab08-cicd-app:&#123;sha&#125;-&#123;run#&#125;</span>
          </div>
        </div>
      </div>

      <div class="region dim" style="left:466px; top:154px; width:410px; height:180px; border-color:#3a4658;">
        <div class="tag" style="background:#0d1722; color:#7d8da0; font-size:11px;">us-west-2b · default subnet</div>
        <div class="box dim" style="left:16px; top:24px; width:378px; height:140px; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center;">
          <div class="sub" style="font-size:11.5px;">desired_count = 1 - Fargate places the<br>single task in either subnet;<br>the ALB target group spans both for HA</div>
        </div>
      </div>
    </div>

    <!-- ECR + CloudWatch column - coords relative to Region B's own box -->
    <div class="box" style="left:1244px; top:36px; width:252px; height:150px;">
      <div class="name">Amazon ECR</div>
      <div class="sub">lab08-cicd-app</div>
      <div style="margin-top:6px;">
        <span class="chip warn">IMMUTABLE tags</span><br>
        <span class="chip">scan_on_push</span><br>
        <span class="chip">lifecycle: keep last 10</span>
      </div>
    </div>
    <div class="flowlbl" style="left:1244px; top:192px; width:252px;">⇕ HTTPS :443 only</div>
    <div class="box" style="left:1244px; top:216px; width:252px; height:172px;">
      <div class="name">CloudWatch Logs</div>
      <div class="sub">/ecs/lab08-cicd</div>
      <div style="margin-top:6px;">
        <span class="chip">7-day retention</span><br>
        <span class="chip">awslogs · stream prefix "app"</span>
      </div>
    </div>
  </div>

  <div class="legend">
    <span><b>Request path:</b> browser → ALB :80 (public subnet, either AZ) → healthy Fargate target :8080 → GET /health drives target-group health</span>
    <span><b>Deploy path:</b> push to main → plan/Checkov/Trivy all pass → <span class="a-warn">production approval</span> → OIDC AssumeRoleWithWebIdentity → gha-deploy role → build+push ECR → terraform apply → ECS rolls the new task out behind the ALB</span>
    <span><b>Trust boundary:</b> <span class="a-ok">no AWS access key is ever stored in GitHub</span> - every credential is short-lived (~1 hr), scoped to one repo, one workflow run, and (for deploy) one approved environment</span>
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
