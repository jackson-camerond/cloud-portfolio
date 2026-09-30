#!/usr/bin/env bash
# terraform fmt -check, init -backend=false and validate for every folder of .tf files under labs/*/assets.
# No backend and no cloud credentials: init only downloads providers and modules, validate only reads the code.
#
# Folders that are not whole Terraform configurations get fmt only (validate needs a complete module):
#   labs/capstone-2/assets/snippets   short redacted excerpts published on purpose, not a runnable module
set -uo pipefail

FMT_ONLY=(
  "labs/capstone-2/assets/snippets"
)

# Folders whose code reads a build output (a Lambda zip) that is never committed. The lab's own packaging script
# runs first (local zip only, no cloud calls), so validate sees the same files a real deploy would.
#   labs/lab-29/assets/terraform      filebase64sha256() on build/<service>.zip from scripts/package.sh
prebuild() {
  case "$1" in
    labs/lab-29/assets/terraform) echo "labs/lab-29/assets/scripts/package.sh" ;;
  esac
}

root="${1:-.}"
cd "$root" || exit 2
export TF_IN_AUTOMATION=1 TF_INPUT=0

dirs=$(find labs -path '*/.terraform' -prune -o -path 'labs/*/assets/*' -name '*.tf' -print \
  | xargs -n1 dirname | sort -u)
fail=0
for d in $dirs; do
  echo "::group::$d"
  if ! terraform -chdir="$d" fmt -check -diff; then
    echo "::error file=$d::terraform fmt -check failed (run terraform fmt)"
    fail=1
  fi
  skip=0
  for f in "${FMT_ONLY[@]}"; do [ "$d" = "$f" ] && skip=1; done
  if [ "$skip" = 1 ]; then
    echo "fmt only: $d is not a complete configuration"
  elif [ -n "$(prebuild "$d")" ] && ! bash "$(prebuild "$d")"; then
    echo "::error file=$d::build step $(prebuild "$d") failed"
    fail=1
  elif ! terraform -chdir="$d" init -backend=false -input=false -no-color >/tmp/tf-init.log 2>&1; then
    cat /tmp/tf-init.log
    echo "::error file=$d::terraform init -backend=false failed"
    fail=1
  elif ! terraform -chdir="$d" validate -no-color; then
    echo "::error file=$d::terraform validate failed"
    fail=1
  fi
  echo "::endgroup::"
done
exit $fail
