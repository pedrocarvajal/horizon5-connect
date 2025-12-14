#!/bin/bash

LOGS_FOLDER="logs"
LOG_FILE=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

_log_to_file() {
    local level=$1
    local message=$2
    if [ -n "$LOG_FILE" ]; then
        echo "[$(_timestamp)] [$level] $message" >> "$LOG_FILE"
    fi
}

log_setup() {
    local name=$1
    mkdir -p "$LOGS_FOLDER"
    LOG_FILE="$LOGS_FOLDER/${name}.log"
}

log_debug() {
    local message="$1"
    echo -e "${CYAN}[$(_timestamp)] [DEBUG]${NC} $message"
    _log_to_file "DEBUG" "$message"
}

log_info() {
    local message="$1"
    echo -e "${GREEN}[$(_timestamp)] [INFO]${NC} $message"
    _log_to_file "INFO" "$message"
}

log_warning() {
    local message="$1"
    echo -e "${YELLOW}[$(_timestamp)] [WARNING]${NC} $message"
    _log_to_file "WARNING" "$message"
}

log_error() {
    local message="$1"
    echo -e "${RED}[$(_timestamp)] [ERROR]${NC} $message"
    _log_to_file "ERROR" "$message"
}

log_critical() {
    local message="$1"
    echo -e "${RED}${BOLD}[$(_timestamp)] [CRITICAL]${NC} $message"
    _log_to_file "CRITICAL" "$message"
}

log_title() {
    local message="$1"
    echo ""
    echo "============================================"
    echo "=  $message"
    echo "============================================"
    echo ""
    _log_to_file "TITLE" "$message"
}

log_separator() {
    echo "============================================"
    _log_to_file "SEPARATOR" "============================================"
}

