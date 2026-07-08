#!/usr/bin/env bash
set -ue

git switch mlell
git tag -f old-fork
git reset --hard master

fork_tools=(branches.yml README.md README.rst update_branches.py merge_branches.sh)
git restore -SW --source master .
git restore -SW --source old-fork "$@"
git add "${fork_tools[@]}"
git commit -m "Add fork tools"

echo "====================================================="
echo "Done. Merge the feature branches now."
echo "====================================================="
