#!/usr/bin/env python3
import threading
import socket


class Node:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.thread = threading.Thread(target=self._routine, args=(self))

    def _routine(self):
        print(id(self), self.sock.getnameinfo())

    def start(self):
        self.thread.start()

    def finish(self):
        self.sock.close()
        self.thread.join()


class NodesPool:
    def __init__(self, nodes_n: int):
        self.nodes: list[Node] = [ Node() for _ in range(nodes_n) ]


    def __enter__(self):
        pass


    def start(self):
        for node in self.nodes:
            node.start()


    def __exit__(self):
        for node in self.nodes:
            node.finish()

