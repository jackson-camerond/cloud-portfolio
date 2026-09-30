#!/usr/bin/env bash
# Checkov on every labs/<lab>/assets folder that holds Terraform. Hard fail (no soft-fail).
# A lab's accepted findings live in .github/checkov/<lab>.yaml, each with its reason; a lab without a file
# there runs with every check on.
set -uo pipefail
root="${1:-.}"
cd "$root" || exit 2
fail=0
for assets in labs/*/assets; do
  [ -d "$assets" ] || continue
  if [ -z "$(find "$assets" -path '*/.terraform' -prune -o -name '*.tf' -print -quit)" ]; then
    continue
  fi
  lab=$(basename "$(dirname "$assets")")
  cfg=".github/checkov/$lab.yaml"
  echo "::group::checkov $assets"
  if [ -f "$cfg" ]; then
    echo "skip list: $cfg"
    checkov -d "$assets" --config-file "$cfg"
  else
    echo "no skip list for $lab: every check on"
    checkov -d "$assets" --framework terraform --compact --quiet
  fi
  rc=$?
  echo "::endgroup::"
  if [ $rc -ne 0 ]; then
    echo "::error file=$assets::Checkov failed for $lab (fix it, or add a skip with its reason to $cfg)"
    fail=1
  fi
done
exit $fail
