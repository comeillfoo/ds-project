#!/usr/bin/env python3
import click
import logging

from nodes import NodesPool, LOG_NODE_LEVEL
from protos import DisseminationProtocol, Multicast, Gossip, LOG_PROTO_LEVEL


DEFAULT_NUMBER_NODES = 3
DEFAULT_ROUNDS_LIMIT = 500
DEFAULT_GROUP_SIZE = 2

LOG_ROUNDS_LEVEL = 18
logging.addLevelName(LOG_ROUNDS_LEVEL, 'ROUNDS')

def log_rounds(msg, *args, **kwargs):
    logging.log(LOG_ROUNDS_LEVEL, msg, *args, **kwargs)

def count_logging_level(verbosity: int) -> int:
    return {
        0: logging.INFO,
        1: LOG_ROUNDS_LEVEL,
        2: LOG_PROTO_LEVEL,
        3: LOG_NODE_LEVEL,
    }.get(verbosity, logging.DEBUG)

@click.group()
@click.option('-n', '--nodes', type=int, default=DEFAULT_NUMBER_NODES,
              show_default=True, help='Number of nodes')
@click.option('-l', '--limit', type=int, default=DEFAULT_ROUNDS_LIMIT,
              show_default=True, help='Maximum rounds of simulation')
@click.option('-c', '--loss-chance', type=float, default=0.0,
              show_default=True, help='probability% of losing a message')
@click.option('-v', '--verbose', count=True, default=0,
              help='Set verbosity level, default INFO')
@click.pass_context
def main(ctx, nodes: int, limit: int, loss_chance: float, verbose: int):
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
    ctx.obj['loss'] = loss_chance / 100


def run(limit: int, proto: DisseminationProtocol):
    rounds = 1
    overall_nodes = len(proto.pool.nodes)
    with proto.pool:
        try:
            while rounds <= limit:
                should_stop = proto.exchange()
                notified = proto.pool.count_disseminated_nodes()
                not_notified = proto.pool.count_disseminated_nodes(False)

                log_rounds('round [%i/%i]: %i/%i/%i; (total/notified/not notified)',
                             rounds, limit, overall_nodes, notified, not_notified)

                if should_stop: break
                rounds += 1

            logging.info('total: %i msgs, discarded: %i msgs',
                         proto.pool.counters['total'], proto.pool.counters['discarded'])
            logging.info('expected: %f, actual: %f', proto.pool.discard_chance,
                         proto.pool.actual_discard_chance())

            if not proto.pool.is_pool_disseminated():
                notified = proto.pool.count_disseminated_nodes()
                not_notified = proto.pool.count_disseminated_nodes(False)
                logging.warning('not disseminated: [%s]',
                                ', '.join(map(str, proto.pool.i_disseminated_nodes(False))))
                logging.info('FAILED to disseminate pool: [%i/%i/%i], (%i/%i)',
                            overall_nodes, notified, not_notified, rounds - 1, limit)
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
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    run(limit, Multicast(NodesPool(nodes, loss), 1))


@main.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def multicast(ctx, group: int):
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    check_group_value(ctx, group, 'Multicast group size should be between 1 and'
                      ' nodes number')
    run(limit, Multicast(NodesPool(nodes, loss), group))


@main.command()
@click.pass_context
def broadcast(ctx):
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    run(limit, Multicast(NodesPool(nodes, loss), nodes - 1))


@main.group()
def gossip():
    pass


GOSSIP_ERROR_MSG = 'Number of random nodes for gossip should be between 1 and ' \
                   'nodes number'


@gossip.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def push(ctx, group: int):
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    check_group_value(ctx, group, GOSSIP_ERROR_MSG)

    run(limit, Gossip(NodesPool(nodes, loss), 'push', group, 0))


@gossip.command()
@click.argument('group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def pull(ctx, group: int):
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    check_group_value(ctx, group, GOSSIP_ERROR_MSG)

    run(limit, Gossip(NodesPool(nodes, loss), 'pull', 0, group))


@gossip.command()
@click.argument('push_group', type=int, default=DEFAULT_GROUP_SIZE)
@click.argument('pull_group', type=int, default=DEFAULT_GROUP_SIZE)
@click.pass_context
def push_pull(ctx, push_group: int, pull_group: int):
    limit, nodes, loss = ctx.obj['limit'], ctx.obj['nodes'], ctx.obj['loss']
    check_group_value(ctx, push_group, GOSSIP_ERROR_MSG)
    check_group_value(ctx, pull_group, GOSSIP_ERROR_MSG)

    run(limit, Gossip(NodesPool(nodes, loss), 'push-pull', push_group,
                      pull_group))


if __name__ == '__main__':
    main(obj={})
