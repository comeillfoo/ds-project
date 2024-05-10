#!/usr/bin/env python3
import threading
import socket


class Node:

    def __init__(self, nodes_pool):
        self.nodes_pool = nodes_pool

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(('127.0.0.1', 0))
        self.port = self.sock.getsockname()[1]

        self.thread = threading.Thread(target=self._routine)


    def _routine(self):
        pass


    def start(self):
        self.thread.start()


    def finish(self):
        self.sock.close()
        self.thread.join()


class NodesPool:
    def __init__(self, nodes_n: int):
        self.nodes: list[Node] = [ Node(self) for _ in range(nodes_n) ]


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        for node in self.nodes:
            node.finish()


    def exchange(self) -> bool:
        return False
