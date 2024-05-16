#!/usr/bin/env bash

# @brief return code on failure
RC_NOT_OK=1

# @brief return code if not satisfied with environment
RC_SKIP=4

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

usage() {
cat <<EOF
${0##*/} [options] [arguments]

Options:
    -h, --help Show this help message and exits

Arguments:
    extra arguments for disseminator.py
EOF
}

while true; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

set -euo pipefail


if ! require_command python3; then
    echo '# not ok: python3 not found [SKIP]'
    exit $RC_SKIP
fi

echo '## Sourcing local environment...'
if ! source .venv/bin/activate; then
    echo '# not ok: failed to source environment'
    exit $RC_NOT_OK
fi

echo "## Starting test (args: $@)..."
if ! python3 ./disseminator.py $@; then
    echo '# not ok: test failed'
    exit $RC_NOT_OK
fi
echo '# ok: test finished successfully'
