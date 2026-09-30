# Checkov skip lists for lab Terraform

`lab-guard.yml` runs Checkov on every `labs/<lab>/assets` folder that holds Terraform, with soft-fail off.
Each lab can have one file here, `<lab>.yaml`, listing the checks it skips and why. A lab with no file here
skips nothing, so a new lab starts with every check on.

Rules for a skip:
- one line per check id, with the reason on the same line or right above it
- only for something the lab does on purpose (a short-lived demo that is torn down the same day, a cost
  choice, a public endpoint the lab is about) or a check that cannot apply (a redacted excerpt)
- never a blanket skip across labs, and never a skip for a finding nobody has read

Findings that are real gaps rather than lab choices are marked `KNOWN GAP` so they stay visible.
