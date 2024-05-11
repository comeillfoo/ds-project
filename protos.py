#!/usr/bin/env python3
from abc import ABC, abstractmethod
from enum import IntEnum, auto
import random


from nodes import NodesPool, Node


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


class DisseminationProtocol:
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
        potential_senders = set()
        while len(self.send_idx_queue) > 0:
            sender_i: int = self.send_idx_queue.pop()
            receivers_i: set[int] = self.pick_next_nodes_group(sender_i)
            non_disseminated = set(map(lambda inode: inode[0],
                                       filter(lambda inode: not inode[1].is_disseminated,
                                              map(lambda idx: (idx, self.pool.nodes[idx]), receivers_i))))
            # print(f'Picked sender [{sender_i}], {len(receivers_i)} receivers'
            #       f' and {len(non_disseminated)} receivers are not disseminated yet:',
            #       non_disseminated)

            receivers = set(map(self._inode, receivers_i))

            sender_t = self._inode(sender_i).start_exchange(True, receivers)
            receivers_t = [ receiver.start_exchange(False, []) for receiver in receivers ]

            for receiver_t in receivers_t:
                receiver_t.join()
            sender_t.join()

            potential_senders.update(map(lambda inode: inode[0],
                                         filter(lambda inode: inode[1].is_disseminated,
                                                enumerate(self.pool.nodes))))

        self.send_idx_queue = potential_senders
        return super().exchange()


class Gossip(DisseminationProtocol):
    def __init__(self, nodes_pool: NodesPool, mode: str, group_size: int):
        super().__init__(nodes_pool)
        self._exchange_cb = {
            'push': self._push_exchange,
            'pull': self._pull_exchange,
            'push-pull': self._push_pull_exchange
        }.get(mode, self._push_exchange)

        self.group_size = group_size

        start_node = self._pick_node()
        start_node.is_disseminated = True
        self.send_queue = { start_node }


    def _push_exchange(self):
        potential_senders = set()
        while len(self.send_queue) > 0:
            sender: Node = self.send_queue.pop()
            # print('Picked sender:', sender.port, sender.is_disseminated)
            receivers: set[Node] = self._pick_nodes_group(sender)
            # print('Picked receivers:',
            #       ', '.join(map(lambda receiver: str(receiver.port), receivers)))

            sender_t = sender.start_exchange(True, receivers)
            receivers_t = [ receiver.start_exchange(False, []) for receiver in receivers ]
            for receiver_t in receivers_t:
                receiver_t.join()
            sender_t.join()
            # TODO: maybe restrict disseminated nodes from previous rounds from
            # sending again
            potential_senders.update(filter(lambda sender: sender.is_disseminated,
                                    self.pool.nodes))

            # print('Updated potential senders:',
            #       ', '.join(map(lambda sender: str(sender.port), potential_senders)))

        self.send_queue = potential_senders


    def _pull_exchange(self):
        raise NotImplementedError


    def _push_pull_exchange(self):
        raise NotImplementedError


    def _pick_random_node(self) -> Node:
        idx = random.randrange(0, len(self.pool.nodes))
        return self.pool.nodes[idx]


    def _pick_node(self, target_dissemination: bool = False) -> Node:
        node = self._pick_random_node()
        while node.is_disseminated != target_dissemination:
            node = self._pick_random_node()
        return node


    def _pick_nodes_group(self, self_node: Node) -> list[Node]:
        ans = set()
        while len(ans) < self.group_size:
            node = self._pick_random_node()
            if node == self_node:
                continue
            ans.add(node)
        return ans



    def exchange(self) -> bool:
        self._exchange_cb()
        return super().exchange()

