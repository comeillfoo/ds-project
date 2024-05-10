#!/usr/bin/env bash

# @brief namespace id
NS=ns-$$

# @brief random packet loss percentage
loss_random="$1"

set -euo pipefail

cleanup() {
    echo "Deleting network namespace $NS"
    ip netns delete $NS
}


if ! ip netns add $NS; then
    echo 'Failed to add network namespace'
    exit 1
fi
echo "Added network namespace $NS"
trap cleanup EXIT 1 2 3 6

if [ -n "${loss_random}" ]; then
    echo "Setting random loss to ${loss_random}..."
    if ! ip netns exec $NS tc qdisc add dev lo root netem loss random "${loss_random}"; then
        echo "Failed to set random loss to ${loss_random}"
        cleanup
        exit 1
    fi
    echo 'Check lo settings:'
    ip netns exec $NS tc qdisc show dev lo
fi

if ! ip netns exec $NS ip link set dev lo up; then
    echo 'Failed to set lo up'
    cleanup
    exit 1
fi
echo 'Set up lo'

