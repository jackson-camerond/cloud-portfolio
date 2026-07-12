# Site

The deployable portfolio. Everything in [`src/`](src/) is published to the Azure
Storage `$web` container by the GitHub Actions workflow on every push to `main`.

- `index.html` — home (Azure "Index document name")
- `404.html` — not-found page (Azure "Error document path")
- `projects.html` — projects
- `resume.html` → `Cameron-Jackson-Resume.pdf` — résumé (HTML source + rendered PDF)
- `css/`, `js/`, `img/` — assets (headshot + certification badges)

See the [repository README](../README.md) for the deploy / CI-CD setup.

## Local preview

```bash
cd src
python3 -m http.server 8000
# open http://localhost:8000
```
