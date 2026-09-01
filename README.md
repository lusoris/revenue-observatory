# Revenue Observatory

Canonical Gitea workspace for Revenue Observatory's evidence-backed opportunity
portfolio, validation records, economics models, and operator-ready handoff
briefs.

Gitea `main` is the source of truth. Public GitHub publication is intentionally
held until the operator records the exact destination in
[issue #1](https://git.dev.cauda.dev/gitea_admin/revenue-observatory/issues/1);
the publisher must fast-forward a CI-validated Gitea commit and must never
invent or rewrite public history.

## Validation

Every pull request and `main` push runs the repository gate on the office Gitea
runner. The gate parses every tracked JSON record, rejects empty files,
conflict markers, non-UTF-8 source text, and trailing whitespace, and emits a
commit-bound tree receipt:

```bash
python3 scripts/verify_repository.py \
  --root . \
  --output-root "${TMPDIR:-/tmp}/revenue-observatory-verify"
```
