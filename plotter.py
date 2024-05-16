#!/usr/bin/python3
import os
import sys
import argparse
import re

import matplotlib.pyplot as plt

from pathlib import Path
from typing import Tuple, Iterable
from functools import reduce

SEP='#####################################################################'

PROTO_RX=re.compile(r'.*PROTO: (\w+);.*')
LOSS_RX=re.compile(r'.*LOSS: (\d+)\%;.*')
ARGS_RX=re.compile(r'.*ARGS: (.*)')
RESULT_RX=re.compile(r'INFO:root:SUCCEED in dissemination: \((\d+)/\d+\) rounds')

def argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser('plotter')

    p.add_argument('logs', type=Path, help='Path to folder with logs')
    return p


def is_logfile(file: str) -> bool:
    return file.endswith('.log')


def parse_test_info(line: str) -> Tuple[str, str, float]:
    proto = PROTO_RX.match(line).groups()[0]
    loss = float(LOSS_RX.match(line).groups()[0])
    args = ARGS_RX.match(line).groups()[0]
    return proto, args, loss


def parse_log(logfile: str) -> dict:
    result = {}
    with open(logfile, 'r') as f:
        for trun_log in f.read().split(SEP):
            test_runs_lines = list(filter(lambda s: s != '', trun_log.split('\n')))
            if not test_runs_lines:
                continue
            proto, args, loss = parse_test_info(test_runs_lines[0])
            proto_args = ' '.join([proto, args]).strip()
            test_result = int(RESULT_RX.match(test_runs_lines[-2]).groups()[0])
            runs = result.get(proto_args, [])
            runs.append((loss, test_result))
            result[proto_args] = runs
    return result


def compile_logs(acc: dict, logs: dict) -> dict:
    for testcase, tc_results in logs.items():
        results = acc.get(testcase, {})
        # print(testcase, tc_results, results)
        for i, tc_result in enumerate(tc_results):
            result = results.get(i, [])
            result.append(tc_result)
            results[i] = result
        acc[testcase] = results
        # print(acc)
    return acc


def main() -> int:
    args = argparser().parse_args()
    readlink = lambda logfile: os.path.join(args.logs, logfile)
    logs = reduce(compile_logs,
                  map(parse_log,
                      map(readlink, filter(is_logfile, os.listdir(args.logs)))), {})

    for testcase, results in logs.items():
        fig, ax = plt.subplots(1, figsize=(10, 5))
        n = len(results)
        ax.set_xticks(range(0, 100, 5))
        y_avg = [0.0] * n
        for i, result in results.items():
            result = sorted(result)
            print(testcase, result)
            x = list(map(lambda r: r[0], result))
            x_avg = x

            y = list(map(lambda r: r[1], result))
            y_avg = [ y_acc + y_curr for y_acc, y_curr in zip(y_avg, y) ]

            ax.plot(x, y, '--', label=str(i))

        y_avg = list(map(lambda v: v / n, y_avg))
        ax.plot(x_avg, y_avg, 'o-', label='average')
        for x, y in zip(x_avg, y_avg):
            ax.text(x, y * 1.05, '%.2f' % y, ha='center')

        plt.title(f'Dissemination for {testcase}')
        plt.xlabel('Chance to loss message, %')
        plt.ylabel('Time to disseminate, rounds #')
        plt.grid(True)
        ax.legend()
        fig.savefig(f'{testcase}.png')



if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt as e:
        print('Interrupted')
        sys.exit(1)
