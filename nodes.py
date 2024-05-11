#!/usr/bin/env python3
from typing import Iterable

import errno
import threading
import socket
from functools import reduce


class Node:

    def __init__(self, nodes_pool, host: str, kind: socket.SocketKind):
        self.nodes_pool = nodes_pool

        self.sock = socket.socket(socket.AF_INET, kind)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)

        self.sock.bind((host, 0))

        self.port = self.sock.getsockname()[1]
        self.is_disseminated = False


    def start_exchange(self, is_send: bool, neighbours: Iterable) -> threading.Thread:
        def _xmit():
            for neigh in neighbours:
                self.sock.sendto(b'test', neigh.sock.getsockname())
                # print(f'xmit {self.port} -> {neigh.port}')

        def _recv():
            try:
                self.sock.recvfrom(1024)
            except socket.error as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    return
                print('Fatal error on', self.port, e)
                return

            self.is_disseminated = True

        callback = _xmit if is_send else _recv

        t = threading.Thread(target=callback)
        t.start()
        return t


class NodesPool:
    def __init__(self, nodes_n: int):
        nodes_kind = socket.SOCK_DGRAM # if is_gossip else socket.SOCK_STREAM

        self.nodes = [ Node(self, '127.0.0.1', nodes_kind) for _ in range(nodes_n) ]


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        for node in self.nodes:
            # print('closing', node.sock.getsockname(), '...')
            node.sock.close()


    def is_pool_disseminated(self) -> bool:
        return reduce(lambda acc, is_disseminated: acc and is_disseminated,
               map(lambda node: node.is_disseminated, self.nodes), True)


    def disseminated_nodes(self, target: bool = True) -> set[Node]:
        return set(filter(lambda node: node.is_disseminated == target, self.nodes))

    def count_disseminated_nodes(self, target: bool = True) -> int:
        return len(self.disseminated_nodes(target))

