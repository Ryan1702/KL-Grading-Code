#!/usr/bin/env bash
# Push this repository to GitHub.
# Usage: bash push.sh   (you will be asked for a GitHub Personal Access Token)
set -euo pipefail
cd "$(dirname "$0")"

REPO_HTTPS="https://github.com/Ryan1702/KL-Grading-Code.git"
REPO_SSH="git@github.com:Ryan1702/KL-Grading-Code.git"

git init -q 2>/dev/null || true
git branch -M main
git remote remove origin 2>/dev/null || true

echo "Choose authentication method:"
echo "  1) HTTPS with a Personal Access Token (recommended)"
echo "  2) SSH (uses ~/.ssh/id_rsa; the key must be added to GitHub)"
read -r -p "Method [1/2]: " METHOD

if [ "$METHOD" = "2" ]; then
  git remote add origin "$REPO_SSH"
  git push -u origin main
else
  read -r -s -p "GitHub Personal Access Token: " TOKEN; echo
  git push "https://Ryan1702:${TOKEN}@github.com/Ryan1702/KL-Grading-Code.git" main
  git remote remove origin 2>/dev/null || true
fi
echo "Done: https://github.com/Ryan1702/KL-Grading-Code"
