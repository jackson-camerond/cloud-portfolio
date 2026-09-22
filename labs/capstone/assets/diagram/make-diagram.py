#!/usr/bin/env python3
"""
make-diagram.py — Capstone architecture diagram (AWS -> Azure live cross-cloud
migration, zero data loss).

Two-column, side-by-side cloud layout with the cross-cloud data path drawn in
the gap between them, matching the convention of the other lab generators
(see labs/lab-02/assets/diagram/make-diagram.py for the Azure icon-sourcing
pattern and labs/lab-08/assets/diagram/make-diagram.py for the nested
absolute-positioned box/region convention). AWS is on the left (source),
Azure is on the right (target), so the diagram reads in migration order.

Source of truth: labs/capstone/notes/DIAGRAM-SPEC.md ("Proposed architecture
diagram" section) plus the actual Terraform in
labs/capstone/assets/{aws,azure}-terraform.

Renders:
  - architecture.html  (self-contained, open it directly)
  - architecture.png   (3200x1800, drop into the video)
"""
import os, base64, subprocess

# The AWS/Azure per-service icon packs live in the PUBLIC portfolio repo
# (tools/thumbnailer/{aws,azure}-icons/), a sibling of this private repo, not
# inside portfolio-private itself (which only vendors the Azure icons + a
# generic AWS badge). Resolve the sibling checkout explicitly.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PUBLIC_REPO = os.path.join(os.path.dirname(REPO), "portfolio")
AWS_ICONS = os.path.join(PUBLIC_REPO, "tools/thumbnailer/aws-icons/extracted")
AZ_ICONS = os.path.join(PUBLIC_REPO, "tools/thumbnailer/azure-icons/extracted",
                        "Azure_Public_Service_Icons/Icons")
OUT = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

AWS_ICON_FILES = {
    "vpc":  "Resource-Icons_04302026/Res_Networking-Content-Delivery/Res_Amazon-VPC_Virtual-private-cloud-VPC_48.svg",
    "igw":  "Resource-Icons_04302026/Res_Networking-Content-Delivery/Res_Amazon-VPC_Internet-Gateway_48.svg",
    "ec2":  "Architecture-Service-Icons_04302026/Arch_Compute/64/Arch_Amazon-EC2_64.svg",
    # No dedicated "Security Group" glyph ships in this icon pack; the closest
    # available stand-in is the generic firewall icon (noted in the report).
    "sg":   "Resource-Icons_04302026/Res_General-Icons/Res_48_Light/Res_Firewall_48_Light.svg",
    "key":  "Resource-Icons_04302026/Res_Security-Identity/Res_AWS-Identity-Access-Management_Long-Term-Security-Credential_48.svg",
    "role": "Resource-Icons_04302026/Res_Security-Identity/Res_AWS-Identity-Access-Management_Role_48.svg",
}
AZ_ICON_FILES = {
    "vnet":    "networking/10061-icon-service-Virtual-Networks.svg",
    "rg":      "general/10007-icon-service-Resource-Groups.svg",
    "vm":      "compute/10021-icon-service-Virtual-Machine.svg",
    "nsg":     "networking/10067-icon-service-Network-Security-Groups.svg",
    "pip":     "networking/10069-icon-service-Public-IP-Addresses.svg",
    "storage": "storage/10086-icon-service-Storage-Accounts.svg",
    "law":     "management + governance/00009-icon-service-Log-Analytics-Workspaces.svg",
    "rsv":     "management + governance/00017-icon-service-Recovery-Services-Vaults.svg",
    "migrate": "migrate/10281-icon-service-Azure-Migrate.svg",
    "disk":    "compute/10032-icon-service-Disks.svg",
}


def data_uri(base, rel):
    with open(os.path.join(base, rel), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


aws = {k: data_uri(AWS_ICONS, v) for k, v in AWS_ICON_FILES.items()}
az = {k: data_uri(AZ_ICONS, v) for k, v in AZ_ICON_FILES.items()}


def card(icon_src, name, sub="", extra_cls="", style="", size=34):
    subhtml = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="card {extra_cls}" style="{style}">'
            f'<div class="chead"><img src="{icon_src}" style="width:{size}px;height:{size}px;">'
            f'<div class="name">{name}</div></div>{subhtml}</div>')


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  html,body {{ width:100%; height:100%; overflow:hidden; background:#0e1116;
    font:14px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#d6deeb; }}
  body {{ display:flex; align-items:center; justify-content:center; }}
  .canvas {{ position:relative; flex:none; width:1600px; height:900px; }}

  h1 {{ position:absolute; left:32px; top:14px; right:32px; font-size:21px; color:#fff; font-weight:800; }}
  h1 span {{ color:#5c6b7a; font-weight:500; font-size:13px; display:block; margin-top:2px; }}

  .region {{ position:absolute; border:1.5px dashed #3a4658; border-radius:14px; background:transparent; }}
  .region.aws  {{ border-color:#ff9900; }}
  .region.az   {{ border-color:#2f81f7; }}
  .tag {{ position:absolute; top:-11px; left:16px; background:#0e1116; padding:0 8px;
    font-weight:700; color:#9fb3c8; font-size:11.5px; white-space:nowrap; }}
  .tag.aws {{ color:#ffb84d; }}
  .tag.az  {{ color:#7fb0ff; }}

  .subbox {{ position:absolute; border:1.5px solid #2f4159; border-radius:11px; background:#10161f; }}
  .subbox .tag {{ background:#10161f; }}

  .card {{ position:absolute; border:1.5px solid #2f4159; border-radius:9px; background:#161b22;
    padding:7px 10px; overflow:hidden; }}
  .card.hi {{ border-color:#3fb950; background:#0f1c12; }}
  .card.hi .name {{ color:#5fd97a; }}
  .card.warn {{ border-color:#f7b955; background:#231a0d; }}
  .card.warn .name {{ color:#f7b955; }}
  .card.dim {{ border-style:dashed; opacity:.62; }}
  .chead {{ display:flex; align-items:center; gap:8px; }}
  .name {{ font-weight:800; color:#e6edf3; font-size:12.5px; line-height:1.2; }}
  .sub {{ color:#8a9bb0; font-size:10.3px; margin-top:4px; line-height:1.36; }}
  .badge {{ position:absolute; background:#0e1116; border:1px solid #3a4658; border-radius:5px;
    padding:4px 8px; font-size:10px; color:#9fb3c8; text-align:center; line-height:1.3; }}
  .chip {{ display:inline-block; background:#0e1116; border:1px solid #3a4658; border-radius:5px;
    padding:1px 6px; font-size:9.5px; color:#9fb3c8; font-family:ui-monospace,Menlo,monospace;
    margin:2px 3px 0 0; }}
  .flag {{ position:absolute; background:#231a0d; border:1px solid #f7b955; border-radius:6px;
    padding:5px 9px; font-size:10px; color:#f7b955; font-weight:700; text-align:center; line-height:1.3; }}

  .gap {{ position:absolute; }}
  .flow {{ position:absolute; }}
  .flow .arrow {{ color:#3fb950; font-size:20px; font-weight:700; text-align:center; }}
  .flow .arrow.blue {{ color:#2f81f7; }}
  .flow .arrow.dash {{ color:#7d8da0; }}
  .flow .lbl {{ font-size:10px; color:#9fb3c8; text-align:center; line-height:1.35; margin-top:2px; }}
  .flow .lbl b {{ color:#e6edf3; }}
  .note {{ font-size:9.5px; color:#6a7a8c; text-align:center; font-style:italic; line-height:1.3; }}

  .legend {{ position:absolute; left:32px; right:32px; bottom:14px; display:flex; flex-direction:column;
    gap:4.5px; font-size:11px; color:#9fb3c8; }}
  .legend b {{ color:#e6edf3; }}
  .l-repl {{ color:#3fb950; }} .l-admin {{ color:#f7b955; }} .l-verify {{ color:#7fb0ff; }} .l-auth {{ color:#ff9900; }}
</style></head><body><div class="canvas">

  <h1>Capstone — AWS &rarr; Azure Live Migration, Zero Data Loss
    <span>A running Windows Server workload is discovered, continuously replicated, rehearsed, and cut over from AWS EC2 to Azure with Azure Migrate — while the app keeps taking writes</span></h1>

  <!-- ======================================================================= AWS (SOURCE, LEFT) ======================================================================= -->
  <div class="region aws" style="left:28px; top:70px; width:648px; height:398px;">
    <div class="tag aws"><img src="{aws['vpc']}" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;">VPC · vpc-migrate-cam · 10.0.0.0/16 · us-east-1</div>

    {card(aws['igw'], "igw-migrate-cam", "internet door for the VPC", style="left:504px; top:16px; width:150px; height:56px;", size=24)}

    <div class="subbox" style="left:20px; top:82px; width:608px; height:288px;">
      <div class="tag">Public Subnet · snet-migrate-cam · 10.0.1.0/24 (AZ us-east-1a) · route 0.0.0.0/0 &rarr; IGW, auto-assigns public IP</div>

      {card(aws['ec2'], "ec2-migrate-source-cam",
            "Windows Server 2022 Base AMI (looked up at plan time, most_recent) &middot; t3.medium &middot; "
            "root volume 30&nbsp;GB gp3, <b style='color:#f78f8f'>unencrypted</b><br>"
            "Runs the workload being migrated:<br>Flask link-shortener + SQLite (<code>links.db</code>)",
            style="left:150px; top:40px; width:340px; height:150px;", size=46)}

      <div class="badge" style="left:150px; top:208px; width:340px;">
        <img src="{aws['sg']}" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;">
        <b style="color:#e6edf3;">migrate-source-sg-cam</b> (stateful, LAB-ONLY 0.0.0.0/0)<br>
        <span class="chip">80 app</span><span class="chip">443 Migrate</span><span class="chip">5985 WinRM</span><span class="chip">3389 RDP</span><span class="chip">all egress</span>
      </div>
    </div>
  </div>

  {card(aws['key'], "svc-azure-migrate-cam (IAM User)",
        "Static access key/secret, read off camera via <code>terraform output -raw</code> and pasted into the "
        "Migrate appliance config manager. <b style='color:#5fd97a'>This is the real cross-cloud credential</b> — "
        "describe EC2/volumes/snapshots/images/regions/tags + create/delete snapshot. Deleted at <code>terraform destroy</code>.",
        extra_cls="hi", style="left:28px; top:492px; width:314px; height:172px;", size=30)}

  {card(aws['role'], "role-azure-migrate-cam + instance profile",
        "IAM role/policy/attachment/instance-profile scaffolding, trust policy "
        "<code>sts:AssumeRole</code> for <code>ec2.amazonaws.com</code> only. Same permissions "
        "as the user policy above, but <b style='color:#f7b955'>nothing attaches it to any "
        "actor Azure Migrate uses</b> — spec flags it as vestigial, not the working credential.",
        extra_cls="dim", style="left:362px; top:492px; width:314px; height:172px;", size=30)}

  <div class="tag aws" style="left:28px; top:474px;">IAM (outside the VPC boundary)</div>

  <!-- ======================================================================= GAP — cross-cloud data path ======================================================================= -->
  <div class="flow" style="left:686px; top:186px; width:214px;">
    <div class="arrow">&rarr;</div>
    <div class="lbl"><b>Discovery</b> &middot; WinRM :5985<br>appliance reads EC2 (pull)</div>
  </div>

  <div class="flow" style="left:686px; top:266px; width:214px;">
    <div class="arrow">&rarr;</div>
    <div class="lbl"><b>Replication</b> &middot; mobility agent<br>outbound :9443 (push)</div>
    <div class="note">continuous block-level replication,<br>AWS&rarr;Azure, over public IP:9443 —<br>not a one-time copy</div>
  </div>

  <div class="flow" style="left:686px; top:376px; width:214px;">
    <div class="arrow blue">&#8663;</div>
    <div class="lbl">deltas land in the replication<br>cache, then commit into the<br>vault-managed replica &rarr; disk</div>
  </div>

  <div class="flow" style="left:686px; top:596px; width:214px;">
    <div class="arrow" style="color:#ff9900;">&rarr;</div>
    <div class="lbl"><b>Cross-cloud auth</b> &middot; static key<br>describe + snapshot calls,<br>consumed by discovery appliance</div>
  </div>

  <!-- ======================================================================= AZURE (TARGET, RIGHT) ======================================================================= -->
  <div class="region az" style="left:924px; top:70px; width:648px; height:716px;">
    <div class="tag az"><img src="{az['vnet']}" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;">VNet · vnet-migrate-cam · 10.1.0.0/16 · East US</div>

    <div class="subbox" style="left:20px; top:32px; width:608px; height:398px;">
      <div class="tag"><img src="{az['rg']}" style="width:12px;height:12px;vertical-align:-2px;margin-right:4px;">rg-migrate-source-cam (staging — throwaway scaffolding)</div>

      <div class="badge" style="left:16px; top:26px; width:576px; border-style:dashed; color:#7fb0ff;">
        <img src="{az['migrate']}" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;">
        <b style="color:#7fb0ff;">Azure Migrate project</b> — migrate-project-cam &middot; <i>portal-created, no Terraform resource type (tracked only by a <code>null_resource</code> reminder)</i> — coordinates discovery + replication + cutover below
      </div>

      {card(az['vm'], "vm-mig-appl-cam &middot; discovery appliance",
            "Standard_D16ads_v7 (16 vCPU/64GB = 8 physical cores — clears the Migrate prereq check) &middot; "
            "Windows Server 2022 &middot; admin migrateadmin &middot; NSG: 3389 only",
            style="left:16px; top:74px; width:280px; height:128px;", size=30)}

      {card(az['vm'], "vm-mig-repl-cam &middot; replication appliance",
            "Standard_D16ads_v7 &middot; Windows Server 2022 (2019 fails the installer) &middot; "
            "admin replicationadmin &middot; NSG: 3389, 443, 9443 (inbound replication) &middot; "
            "<img src=\"{}\" style=\"width:11px;height:11px;vertical-align:-1px;\"> +600&nbsp;GB cache disk".format(az['disk']),
            style="left:312px; top:74px; width:280px; height:128px;", size=30)}

      {card(az['storage'], "stmigratecam",
            "replication cache &middot; Standard/StorageV2/LRS &middot; TLS1.2 min",
            style="left:16px; top:216px; width:186px; height:90px;", size=26)}
      {card(az['law'], "law-migrate-cam",
            "PerGB2018 &middot; 30-day retention &middot; backs discovered-machine data",
            style="left:214px; top:216px; width:186px; height:90px;", size=26)}
      {card(az['rsv'], "rsv-migrate-cam",
            "Standard SKU &middot; soft-delete off &middot; orchestrates ASR replication state",
            style="left:412px; top:216px; width:182px; height:90px;", size=26)}

      <div class="flow" style="left:16px; top:318px; width:582px;">
        <div class="lbl" style="text-align:center;">replication appliance &rarr; writes deltas &rarr; <b>stmigratecam</b> &rarr; commits via &rarr; <b>rsv-migrate-cam</b> &rarr; builds &rarr; migrated VM disk (below)</div>
      </div>

      <div class="flow" style="left:16px; top:350px; width:582px;">
        <div class="arrow blue" style="font-size:16px;">&darr;</div>
      </div>
    </div>

    <div class="subbox" style="left:20px; top:452px; width:608px; height:246px;">
      <div class="tag"><img src="{az['rg']}" style="width:12px;height:12px;vertical-align:-2px;margin-right:4px;">rg-migrate-target-cam (target — created empty by Terraform, VM added by Azure Migrate)</div>

      {card(az['vm'], "migrated VM &middot; Standard_D2s_v3",
            "Built by Azure Migrate at cutover from the latest synced disk — <b style='color:#f7b955'>not in either Terraform state</b>. "
            "Runs the same app + <code>links.db</code>, same hostname/OS as the source EC2 instance.",
            extra_cls="warn", style="left:16px; top:66px; width:280px; height:130px;", size=30)}

      {card(az['nsg'], "nsg-migrate-target-cam", "80 (app), 3389 (RDP) — attached post-cutover; Migrate-built NICs arrive with none",
            style="left:312px; top:66px; width:280px; height:70px;", size=24)}
      {card(az['pip'], "pip-migrated-vm", "new public IP, minted + attached post-cutover — the endpoint-flip analog (no domain in this lab)",
            style="left:312px; top:142px; width:280px; height:70px;", size=24)}

      <div class="flag" style="left:312px; top:26px; width:280px;">CUTOVER FLIP: new public IP + target NSG attached here</div>
    </div>
  </div>

  <div class="legend">
    <span><b class="l-repl">Replication path:</b> EC2 disk &rarr; mobility agent, outbound push, TCP&nbsp;:9443, continuous block-level replication (not file sync) &rarr; replication appliance &rarr; stmigratecam cache &rarr; rsv-migrate-cam replica state &rarr; migrated VM disk</span>
    <span><b class="l-admin">Admin path:</b> operator &rarr; RDP :3389, local Administrator credentials from gitignored tfvars &rarr; EC2 / discovery appliance / replication appliance / migrated VM (never typed on camera)</span>
    <span><b class="l-verify">Verification path:</b> curl + browser against the EC2 public IP, then the new Azure public IP &mdash; confirms same app, the two seeded links, and the link created mid-replication, with zero data loss and <b>no automated rollback</b> once cutover is clicked</span>
    <span><b class="l-auth">Cross-cloud auth path:</b> IAM user's static access key (not the IAM role, which is unused) &rarr; AWS API describe/snapshot calls, consumed by the discovery appliance</span>
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
