#!/usr/bin/env bash

# @brief return code on failure
RC_NOT_OK=1

# @brief return code if not satisfied with environment
RC_SKIP=4

# @brief namespace id
NS=ns-$$

# @brief random packet loss percentage
loss_random="$1"

cleanup() {
    echo "## Deleting network namespace $NS..."
    ip netns delete $NS
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

set -euo pipefail


if ! require_command python3; then
    echo '# not ok: python3 not found [SKIP]'
    exit $RC_SKIP
fi

if ! ip netns add $NS; then
    echo '# not ok: failed to add network namespace'
    exit $RC_NOT_OK
fi
echo "## Added network namespace $NS"
trap cleanup 1 2 3 6

if [ -n "${loss_random}" ]; then
    echo "## Setting random loss to ${loss_random}..."
    if ! ip netns exec $NS tc qdisc add dev lo root netem loss random "${loss_random}"; then
        cleanup
        echo "# not ok: failed to set random loss to ${loss_random}"
        exit $RC_NOT_OK
    fi
    echo '## Check lo settings:'
    ip netns exec $NS tc qdisc show dev lo
fi

if ! ip netns exec $NS ip link set dev lo up; then
    cleanup
    echo '# not ok: failed to set lo up'
    exit $RC_NOT_OK
fi
echo '## Set up lo'

cleanup
echo '# ok: test finished successfully'
