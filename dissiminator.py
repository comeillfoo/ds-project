#!/usr/bin/env python3
import sys
import click

from nodes import NodesPool


DEFAULT_NUMBER_NODES = 3
DEFAULT_ROUNDS_LIMIT = 100

@click.group()
@click.option('-n', '--nodes', type=int, default=DEFAULT_NUMBER_NODES,
              show_default=True, help='Number of nodes')
@click.option('-l', '--limit', type=int, default=DEFAULT_ROUNDS_LIMIT,
              show_default=True, help='Maximum rounds of simulation')
@click.pass_context
def main(ctx, nodes: int, limit: int):

    ctx.ensure_object(dict)
    ctx.obj['nodes'] = nodes
    ctx.obj['limit'] = limit


def run(nodes: int, limit: int):
    rounds = 0
    with NodesPool(nodes) as pool:
        while rounds < limit and not pool.exchange():
            print(f'[{rounds}] starting...')
            rounds += 1


@main.command()
@click.pass_context
def singlecast(ctx):
    pass


@main.command()
@click.pass_context
def multicast(ctx):
    pass


@main.command()
@click.pass_context
def broadcast(ctx):
    pass


@main.command()
@click.option('--push', is_flag=True, default=True, help='Enable push mode')
@click.option('--pull', is_flag=True, help='Enable pull mode')
@click.pass_context
def gossip(ctx, push: bool, pull: bool):
    pass



if __name__ == '__main__':
    main(obj={})
