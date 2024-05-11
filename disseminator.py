#!/usr/bin/env python3
import sys
import click

from nodes import NodesPool
from protos import DisseminationProtocol, Multicast, Gossip


DEFAULT_NUMBER_NODES = 3
DEFAULT_ROUNDS_LIMIT = 100
DEFAULT_GROUP_SIZE = 2


@click.group()
@click.option('-n', '--nodes', type=int, default=DEFAULT_NUMBER_NODES,
              show_default=True, help='Number of nodes')
@click.option('-l', '--limit', type=int, default=DEFAULT_ROUNDS_LIMIT,
              show_default=True, help='Maximum rounds of simulation')
@click.pass_context
def main(ctx, nodes: int, limit: int):
    if nodes <= 0:
        raise click.BadOptionUsage('nodes',
                                   'Nodes number should be positive', ctx)

    if limit <= 0:
        raise click.BadOptionUsage('limit',
                                'Maximum rounds number should be positive', ctx)

    ctx.ensure_object(dict)
    ctx.obj['nodes'] = nodes
    ctx.obj['limit'] = limit


def run(limit: int, proto: DisseminationProtocol):
    rounds = 1
    with proto.pool:
        while rounds <= limit and not proto.exchange():
            print(f'[{rounds}] finished', proto.pool.count_disseminated_nodes(),
                  proto.pool.count_disseminated_nodes(False))
            rounds += 1

        if not proto.pool.is_pool_disseminated():
            print(f'[{rounds}] failed to disseminate pool, left',
                  proto.pool.count_disseminated_nodes(False))
            return

        print(f'[{rounds}] pool successfully disseminated')


@main.command()
@click.pass_context
def singlecast(ctx):
    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']), 1))


@main.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def multicast(ctx, group: int):
    if not (group > 1 and group < ctx.obj['nodes']):
        raise click.BadArgumentUsage(
            'Multicast group size should be between 1 and nodes number', ctx)

    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']), group))


@main.command()
@click.pass_context
def broadcast(ctx):
    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']),
                                    ctx.obj['nodes'] - 1))


@main.command()
@click.option('-m', '--mode', type=click.Choice(['push', 'pull', 'push-pull']),
              default='push', help='Gossip protocol mode', show_default=True)
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def gossip(ctx, mode: str, group: int):
    if group <= 0 or group >= ctx.obj['nodes']:
        raise click.BadArgumentUsage(
            'Number of random nodes for gossip should be between 1 and nodes number', ctx)

    run(ctx.obj['limit'], Gossip(NodesPool(ctx.obj['nodes']), mode, group))



if __name__ == '__main__':
    main(obj={})
