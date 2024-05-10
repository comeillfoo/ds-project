#!/usr/bin/env python3
import sys
import argparse

from node import NodesPool


DISSIMINATION_ALGORITHMS = [
    'single',
    'multi',
    'broad',
    'gossip'
]


def argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser('dissiminator')

    # Options
    default_algorithm = DISSIMINATION_ALGORITHMS[0]
    p.add_argument('-a', '--algorithm', choices=DISSIMINATION_ALGORITHMS,
                   default=default_algorithm,
                   help=f'cast algorithm to use, default {default_algorithm}')

    default_nodes = 3
    p.add_argument('-n', '--nodes', type=int, default=default_nodes,
                   help=f'number of nodes, default {default_nodes}')

    # Arguments
    # TODO:

    return p


def main() -> int:
    args = argparser().parse_args()

    with NodesPool(args.nodes) as pool:
        pool.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())