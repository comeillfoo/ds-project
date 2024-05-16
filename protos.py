#!/usr/bin/env python3
from abc import ABC, abstractmethod
from enum import IntEnum, auto
import random
import logging


from nodes import NodesPool, Node, MessageType


LOG_PROTO_LEVEL = 16
logging.addLevelName(LOG_PROTO_LEVEL, 'PROTO')

def log_proto(msg, *args, **kwargs):
    logging.log(LOG_PROTO_LEVEL, msg, *args, **kwargs)


class CastModes(IntEnum):
    SINGLE = 0
    MULTI = auto()
    BROAD = auto()

    @classmethod
    def from_str(cls, string: str):
        return {
            'single': cls.SINGLE,
            'multi': cls.MULTI,
            'broad': cls.BROAD
        }.get(string, cls.SINGLE)


class DisseminationProtocol(ABC):
    def __init__(self, nodes_pool: NodesPool):
        self.pool = nodes_pool

    @abstractmethod
    def exchange(self) -> bool:
        return self.pool.is_pool_disseminated()


class Multicast(DisseminationProtocol):
    def __init__(self, pool: NodesPool, group_size: int):
        super().__init__(pool)
        self.group_size = group_size

        self.send_idx_queue = { 0 }
        self.pool.nodes[0].is_disseminated = True


    def pick_next_nodes_group(self, base: int) -> set[int]:
        nodes_idx = { base }

        def _next_idx(cur: int) -> int:
            return (cur + 1) % len(self.pool.nodes)

        i = base
        while len(nodes_idx) < self.group_size + 1:
            i = _next_idx(i)
            nodes_idx.add(i)

        nodes_idx.remove(base)
        return nodes_idx


    def _inode(self, i: int) -> Node:
        i = i % len(self.pool.nodes)
        return self.pool.nodes[i]


    def exchange(self) -> bool:
        while len(self.send_idx_queue) > 0:
            sender_i: int = self.send_idx_queue.pop()
            receivers_i: set[int] = self.pick_next_nodes_group(sender_i)
            log_proto('picked sender/count receivers [%i/%i]', sender_i,
                      len(receivers_i))

            receivers = set(map(self._inode, receivers_i))

            for receiver in receivers:
                self._inode(sender_i).xmit(receiver, MessageType.PUSH)

        self.send_idx_queue = self.pool.i_disseminated_nodes()
        return super().exchange()


class Gossip(DisseminationProtocol):
    def __init__(self, nodes_pool: NodesPool, mode: str,
                 push_group: int, pull_group: int):
        super().__init__(nodes_pool)
        self._exchange_cb = {
            'push': self._push_exchange,
            'pull': self._pull_exchange,
            'push-pull': self._push_pull_exchange
        }.get(mode, self._push_exchange)

        self.push_group = push_group
        self.pull_group = pull_group

        start_node = self._pick_node()
        start_node.is_disseminated = True
        self.push_queue = { start_node }
        self.pull_queue = self.pool.disseminated_nodes(False)


    def _push_exchange(self):
        log_proto('starting push exchange...')
        while len(self.push_queue) > 0:
            pusher: Node = self.push_queue.pop()
            log_proto('picked pusher [%i]', pusher.nid)

            receivers: set[Node] = self._pick_nodes_group(pusher,
                                                          self.push_group)
            log_proto('picked receivers: [%s]',
                      ', '.join(map(lambda receiver: str(receiver.nid),
                                    receivers)))

            for receiver in receivers:
                pusher.xmit(receiver, MessageType.PUSH)

        # TODO: maybe restrict disseminated nodes from previous rounds from
        # sending again
        self.push_queue = self.pool.disseminated_nodes()


    def _pull_exchange(self):
        log_proto('starting pull exchange...')
        while len(self.pull_queue) > 0:
            puller: Node = self.pull_queue.pop()
            log_proto('picked puller [%i]', puller.nid)

            receivers: set[Node] = self._pick_nodes_group(puller,
                                                          self.pull_group)
            log_proto('picked receivers: [%s]',
                      ', '.join(map(lambda receiver: str(receiver.nid),
                                    receivers)))

            for receiver in receivers:
                puller.xmit(receiver, MessageType.PULL)

        self.pull_queue = self.pool.disseminated_nodes(False)


    def _push_pull_exchange(self):
        self._push_exchange()
        self._pull_exchange()


    def _pick_random_node(self) -> Node:
        idx = random.randrange(0, len(self.pool.nodes))
        return self.pool.nodes[idx]


    def _pick_node(self, target_dissemination: bool = False) -> Node:
        node = self._pick_random_node()
        while node.is_disseminated != target_dissemination:
            node = self._pick_random_node()
        return node


    def _pick_nodes_group(self, self_node: Node, group_size: int) -> list[Node]:
        ans = set()
        while len(ans) < group_size:
            node = self._pick_random_node()
            if node == self_node:
                continue
            ans.add(node)
        return ans



    def exchange(self) -> bool:
        self._exchange_cb()
        return super().exchange()

