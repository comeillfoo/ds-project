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
        self.nodes_pool = nodes_pool

    @abstractmethod
    def exchange(self) -> bool:
        return self.nodes_pool.is_pool_disseminated()


class Multicast(DisseminationProtocol):
    def __init__(self, nodes_pool: NodesPool, group_size: int):
        super().__init__(nodes_pool)
        self.group_size = group_size

    def exchange(self) -> bool:
        # TODO: multicast protocol
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
            receivers: set[Node] = self._pick_k_nodes(sender, self.group_size)
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
                                    self.nodes_pool.nodes))

            # print('Updated potential senders:',
            #       ', '.join(map(lambda sender: str(sender.port), potential_senders)))

        self.send_queue = potential_senders


    def _pull_exchange(self):
        raise NotImplementedError


    def _push_pull_exchange(self):
        raise NotImplementedError


    def _pick_random_node(self) -> Node:
        idx = random.randrange(0, len(self.nodes_pool.nodes))
        return self.nodes_pool.nodes[idx]


    def _pick_node(self, target_dissemination: bool = False) -> Node:
        node = self._pick_random_node()
        while node.is_disseminated != target_dissemination:
            node = self._pick_random_node()
        return node


    def _pick_k_nodes(self, self_node: Node, k: int) -> list[Node]:
        ans = set()
        while len(ans) < k:
            node = self._pick_random_node()
            if node == self_node:
                continue
            ans.add(node)
        return ans



    def exchange(self) -> bool:
        self._exchange_cb()
        return super().exchange()

