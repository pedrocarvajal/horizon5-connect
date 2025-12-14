#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-submodules-push"

log_title "Pushing Submodules"

if [ -z "$(git submodule status 2>/dev/null)" ]; then
	log_warning "No submodules found"
else
	git submodule foreach 'if [ -n "$(git status --porcelain)" ]; then echo "Pushing changes in $name..."; git add . && git commit -m "Update submodule" && git push; else echo "No changes in $name"; fi'
fi

