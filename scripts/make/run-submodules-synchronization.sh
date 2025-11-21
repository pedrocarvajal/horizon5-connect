#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../helpers/logger.sh"

log_setup "run-submodules-synchronization"

log_title "Synchronizing Submodules"

log_info "Updating submodules..."
git submodule update --remote --recursive

log_separator
log_info "Submodules synchronized successfully!"

