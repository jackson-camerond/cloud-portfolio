# Cameron Jackson — Cloud Portfolio

Personal portfolio for **Cameron Jackson** — Systems Specialist (City of Carson) building toward cloud engineering.

Static **HTML / CSS / vanilla JS** (no build step, no framework), hosted on an **Azure Storage static website** and **auto-deployed via GitHub Actions** on every push to `main`.

<!-- 🔗 Live: https://<your-static-site-url>   (add after the first deploy) -->

## Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD: uploads site/src → Azure $web on push to main
├── site/
│   └── src/                    # everything here is published to the $web container
│       ├── index.html          # Azure "Index document name"
│       ├── 404.html            # Azure "Error document path"
│       ├── projects.html
│       ├── resume.html         # source that renders to the résumé PDF
│       ├── Cameron-Jackson-Resume.pdf
│       ├── css/styles.css
│       ├── js/main.js
│       └── img/                # headshot + certification badges
└── .gitignore
```

## Local preview

```bash
cd site/src
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy (CI/CD)

Every push to `main` runs `.github/workflows/deploy.yml`, which logs in to Azure and
uploads `site/src/` to the storage account's `$web` container — no manual uploads.

It expects two repository settings (**Settings → Secrets and variables → Actions**):

| Type | Name | Value |
|------|------|-------|
| Secret | `AZURE_CREDENTIALS` | Service principal JSON from `az ad sp create-for-rbac … --sdk-auth` |
| Variable | `STORAGE_ACCOUNT` | The target storage account name |
