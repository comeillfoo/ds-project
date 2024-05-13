#!/usr/bin/env bash

# @brief nodes number
NODES=100

# @brief default number of test repeats
TEST_REPEATS=3

# @brief default logs directory
LOGS='./logs'

# @brief timeout
TIMEOUT=60


_join_by() {
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}

run_zero_loss_test() {
    timeout --preserve-status $TIMEOUT ./run.sh -n $NODES $@
}

run_test_with_loss() {
    local loss=$1
    shift 1
    timeout --preserve-status $TIMEOUT ./run.sh --loss $loss -n $NODES $@
}

test_single() {
    local i=$1
    shift 1

    local log_file
    log_file="$(_join_by _ $@).log.${i}"

    local loss=$1;
    shift 1
    local protocol=$1;
    mkdir -p "${LOGS}/${protocol}"
    local log_file_path="${LOGS}/${protocol}/${log_file}"
    shift 1
    if [ $loss -lt 0 ]; then
        echo "Fatal: invalid loss $loss provided"
        return 1
    fi

    echo "# Test #${i}: PROTO: ${protocol}; LOSS: ${loss}%; ARGS: $@"
    if [ $loss -ge 0 ]; then
        run_test_with_loss $loss $protocol $@ |& tee "${log_file_path}"
    else
        run_zero_loss_test $protocol $@ |& tee "${log_file_path}"
    fi
    echo '#####################################################################'
}


test_multiple() {
    for ((i = 0; i < $TEST_REPEATS; ++i)); do
        test_single $i $@
    done
}

test_all() {
    local loss=$1
    test_multiple $loss singlecast
    test_multiple $loss broadcast

    for ((group_size = 5; group_size < 100; group_size += 25)); do
        test_multiple $loss gossip push $group_size
    done

    for ((group_size = 5; group_size < 100; group_size += 25)); do
        test_multiple $loss gossip pull $group_size
    done

    for ((push_gsz = 10; push_gsz < 100; push_gsz += 30)); do
        for ((pull_gsz = 10; pull_gsz < 100; pull_gsz += 30)); do
            test_multiple $loss gossip push-pull $push_gsz $pull_gsz
        done
    done

    for ((group_size = 5; group_size < 100; group_size += 25)); do
        test_multiple $loss multicast $group_size
    done
}

set -uo pipefail

testing_losses=(0 25 50 75 90)

for loss in "${testing_losses[@]}"; do
    echo '#####################################################################'
    echo "# Testing protos with $loss% loss"
    echo '#####################################################################'
    test_all $loss
done
