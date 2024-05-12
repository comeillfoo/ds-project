#!/usr/bin/env python3
import click
import logging

from nodes import NodesPool, LOG_NODE_LEVEL
from protos import DisseminationProtocol, Multicast, Gossip, LOG_PROTO_LEVEL


DEFAULT_NUMBER_NODES = 3
DEFAULT_ROUNDS_LIMIT = 100
DEFAULT_GROUP_SIZE = 2

def count_logging_level(verbosity: int) -> int:
    return {
        0: logging.INFO,
        1: LOG_PROTO_LEVEL,
        2: LOG_NODE_LEVEL,
    }.get(verbosity, logging.DEBUG)

@click.group()
@click.option('-n', '--nodes', type=int, default=DEFAULT_NUMBER_NODES,
              show_default=True, help='Number of nodes')
@click.option('-l', '--limit', type=int, default=DEFAULT_ROUNDS_LIMIT,
              show_default=True, help='Maximum rounds of simulation')
@click.option('-v', '--verbose', count=True, default=0,
              help='Set verbosity level, default INFO')
@click.pass_context
def main(ctx, nodes: int, limit: int, verbose: int):
    logging.basicConfig(level=count_logging_level(verbose))

    if nodes <= 0:
        raise click.BadOptionUsage('nodes', 'Nodes number should be positive',
                                   ctx)

    if limit <= 0:
        raise click.BadOptionUsage('limit', 'Maximum rounds number should be '
                                   'positive', ctx)

    ctx.ensure_object(dict)
    ctx.obj['nodes'] = nodes
    ctx.obj['limit'] = limit


def run(limit: int, proto: DisseminationProtocol):
    rounds = 1
    overall_nodes = len(proto.pool.nodes)
    with proto.pool:
        try:
            while rounds <= limit:
                should_stop = proto.exchange()
                notified = proto.pool.count_disseminated_nodes()
                not_notified = proto.pool.count_disseminated_nodes(False)

                logging.info('round [%i/%i]: %i/%i/%i; (total/notified/not notified)',
                             rounds, limit, overall_nodes, notified, not_notified)

                if should_stop: break
                rounds += 1

            if not proto.pool.is_pool_disseminated():
                notified = proto.pool.count_disseminated_nodes()
                not_notified = proto.pool.count_disseminated_nodes(False)
                logging.info('FAILED to disseminate pool: [%i/%i/%i], (%i/%i)',
                            overall_nodes, notified, not_notified, rounds, limit)
                return

            logging.info('SUCCEED in dissemination: (%i/%i) rounds',
                            rounds, limit)
        except Exception as e:
            logging.critical('Unforeseen exception occured', exc_info=e)


def check_group_value(ctx, group: int, msg: str):
    if group <= 0 or group >= ctx.obj['nodes']:
        raise click.BadArgumentUsage(msg, ctx)


@main.command()
@click.pass_context
def singlecast(ctx):
    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']), 1))


@main.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def multicast(ctx, group: int):
    check_group_value(ctx, group, 'Multicast group size should be between 1 and'
                      ' nodes number')
    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']), group))


@main.command()
@click.pass_context
def broadcast(ctx):
    run(ctx.obj['limit'], Multicast(NodesPool(ctx.obj['nodes']),
                                    ctx.obj['nodes'] - 1))


@main.group()
def gossip():
    pass


GOSSIP_ERROR_MSG = 'Number of random nodes for gossip should be between 1 and ' \
                   'nodes number'


@gossip.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def push(ctx, group: int):
    check_group_value(ctx, group, GOSSIP_ERROR_MSG)

    run(ctx.obj['limit'], Gossip(NodesPool(ctx.obj['nodes']), 'push', group, 0))


@gossip.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def pull(ctx, group: int):
    check_group_value(ctx, group, GOSSIP_ERROR_MSG)

    run(ctx.obj['limit'], Gossip(NodesPool(ctx.obj['nodes']), 'pull', 0, group))


@gossip.command()
@click.argument('push_group', type=int, default=DEFAULT_GROUP_SIZE)
@click.argument('pull_group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def push_pull(ctx, push_group: int, pull_group: int):
    check_group_value(ctx, push_group, GOSSIP_ERROR_MSG)
    check_group_value(ctx, pull_group, GOSSIP_ERROR_MSG)

    run(ctx.obj['limit'], Gossip(NodesPool(ctx.obj['nodes']), 'push-pull',
                                 push_group, pull_group))


if __name__ == '__main__':
    main(obj={})
