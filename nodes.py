#!/usr/bin/env python3
from typing import Iterable

import logging
import errno
import threading
import socket
from functools import reduce
from enum import IntEnum, auto

import random


LOG_NODE_LEVEL = 14
logging.addLevelName(LOG_NODE_LEVEL, 'NODE')

def log_node(msg, *args, **kwargs):
    logging.log(LOG_NODE_LEVEL, msg, *args, **kwargs)


class MessageType(IntEnum):
    PUSH = 0
    PULL = auto()

    def __str__(self) -> str:
        if self is MessageType.PUSH:
            return 'PUSH'
        if self is MessageType.PULL:
            return 'PULL'
        return 'MessageType[Unknown]'


class Node:

    def __init__(self, nodes_pool, id: int):
        self.nodes_pool = nodes_pool
        self.nid = id
        self.is_disseminated = False


    def xmit(self, neigh, msg: MessageType) -> bool:
        log_node('xmit [%i] ---> (%i): %s', self.nid, neigh.nid, str(msg))
        return neigh.recv(self, msg)


    def recv(self, neigh, msg: MessageType) -> bool:
        if self.nodes_pool.should_discard():
            log_node('recv [%i] x--- (%i): msg[%s] lost', self.nid, neigh.nid,
                     str(msg))
            return False

        log_node('recv [%i] <--- (%i): %s', self.nid, neigh.nid, str(msg))
        if self.is_disseminated and msg == MessageType.PULL:
            self.xmit(neigh, MessageType.PUSH)

        if msg == MessageType.PUSH:
            self.is_disseminated = True
        return True


class NodesPool:
    def __init__(self, nodes_n: int, discard_chance: float = 0.0):
        self.nodes = [ Node(self, nid) for nid in range(nodes_n) ]
        self.discard_chance = discard_chance
        self.counters = {
            'total': 0,
            'discarded': 0,
        }


    def should_discard(self) -> bool:
        self.counters['total'] += 1
        chance = random.uniform(0.0, 1.0)
        logging.debug('dice showed: %f', chance)
        if self.discard_chance <= chance:
            return False
        self.counters['discarded'] += 1
        return True


    def actual_discard_chance(self) -> float:
        return self.counters['discarded'] / self.counters['total']


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


    def is_pool_disseminated(self) -> bool:
        return reduce(lambda acc, is_disseminated: acc and is_disseminated,
               map(lambda node: node.is_disseminated, self.nodes), True)


    def disseminated_nodes(self, target: bool = True) -> set[Node]:
        return set(filter(lambda node: node.is_disseminated == target, self.nodes))

    def count_disseminated_nodes(self, target: bool = True) -> int:
        return len(self.disseminated_nodes(target))

    def i_disseminated_nodes(self, target: bool = True) -> set[int]:
        return set(map(lambda inode: inode[0],
                       filter(lambda inode: inode[1].is_disseminated == target,
                              enumerate(self.nodes))))

