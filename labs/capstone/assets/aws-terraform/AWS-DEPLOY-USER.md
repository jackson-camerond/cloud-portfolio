# AWS deploy user — capstone (open perms, torn down tomorrow)

Copy-paste sheet for the one IAM user Terraform runs as. **Open permissions on
purpose** — this is a throwaway identity in your own sandbox account
(<AWS-ACCOUNT-ID>), deleted right after the shoot, so it gets full access to
guarantee zero permission errors mid-lab.

| Field | Value |
|---|---|
| **User name** | `svc-deploy` |
| **Description / tag** | `project=azure-migrate-lab` — temporary deploy identity for the AWS→Azure Migrate capstone; torn down after recording |
| **Console access** | No (programmatic only — access key + secret) |
| **Permissions** | `AdministratorAccess` (one click) — or the inline JSON below (`Action: *`, `Resource: *`) |
| **Region** | `us-east-1` |

Neither profile on this laptop can deploy (`cam-s3-uploader` = S3 only,
`cam-readonly` = read only), which is why we make this one.

---

## Console steps (you're doing this now)

1. **IAM → Users → Create user** → name `svc-deploy` → **no** console access.
2. **Set permissions → Attach policies directly** → check **`AdministratorAccess`**.
   (Or *Create policy → JSON* → paste `deploy-user-policy.json` from this folder → attach it.)
3. **Add tag** `project = azure-migrate-lab` (so teardown is easy to find).
4. **Create user** → open it → **Security credentials → Create access key** →
   *Command Line Interface* → **copy the Access Key ID + Secret off camera.**

## Wire it up + verify

```bash
aws configure --profile deploy      # paste key + secret; region us-east-1
export AWS_PROFILE=deploy            # Terraform borrows this automatically
aws sts get-caller-identity                   # must show .../svc-deploy
```

Tell me when that's done and I'll run `terraform init && terraform plan` against it.

## Inline policy (only if you skip AdministratorAccess)

`deploy-user-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "OpenForLabTornDownTomorrow", "Effect": "Allow", "Action": "*", "Resource": "*" }
  ]
}
```

## Teardown (tomorrow, after the shoot — do NOT leave this user)

IAM → Users → `svc-deploy` → delete access key, detach policy, delete user.
(`terraform destroy` removes the `svc-azure-migrate` user the *lab* creates, but
not this bootstrap user — delete it by hand.)
