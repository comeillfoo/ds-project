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

    p.add_argument('logs', type=Path, nargs='+',
                   help='Path to logs')
    p.add_argument('-s', '--summary', action='store_true',
                   help='Plot summary diagram')
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


GLOBAL_FIG, GLOBAL_AX = plt.subplots(1, figsize=(20, 10))


def figax(summary: bool) -> Tuple:
    if not summary:
        return plt.subplots(1, figsize=(10, 5))
    return GLOBAL_FIG, GLOBAL_AX


def main() -> int:
    args = argparser().parse_args()
    logs = {}
    if args.summary:
        logs.update(reduce(compile_logs, map(parse_log, args.logs), {}))
    else:
        for logfolder in args.logs:
            readlink = lambda logfile: os.path.join(logfolder, logfile)
            logs.update(reduce(compile_logs, map(parse_log,
                    map(readlink, filter(is_logfile, os.listdir(logfolder)))), {}))

    for testcase, results in logs.items():
        fig, ax = figax(args.summary)
        n = len(results)
        ax.set_xticks(range(0, 100, 5))
        y_avg = [0.0] * len(results[0])
        for i, result in results.items():
            result = sorted(result)
            print(testcase, result)
            x = list(map(lambda r: r[0], result))
            x_avg = x

            y = list(map(lambda r: r[1], result))
            y_avg = [ y_acc + y_curr for y_acc, y_curr in zip(y_avg, y) ]
            if not args.summary:
                ax.plot(x, y, '--', label=str(i))

        y_avg = list(map(lambda v: v / n, y_avg))
        if args.summary:
            ax.plot(x_avg, y_avg, 'o-', label=testcase)
        else:
            ax.plot(x_avg, y_avg, 'o-', label='average')

        for x, y in zip(x_avg, y_avg):
            ax.text(x, y * 1.05, '%.2f' % y, ha='center')

        if args.summary:
            plt.title('Dissemination')
        else:
            plt.title(f'Dissemination for {testcase}')
        plt.xlabel('Chance to loss message, %')
        plt.ylabel('Time to disseminate, rounds #')
        plt.grid(True)
        ax.legend()
        if not args.summary:
            fig.savefig(f'{testcase}.png')

    if args.summary:
        GLOBAL_FIG.savefig('summary.png')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt as e:
        print('Interrupted')
        sys.exit(1)
