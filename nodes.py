#!/usr/bin/env python3
from typing import Iterable

import logging
import errno
import threading
import socket
from functools import reduce
from enum import IntEnum, auto

import pickle


LOG_NODE_LEVEL=12
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
    BUFFER_SIZE = 1024

    def __init__(self, nodes_pool, host: str, kind: socket.SocketKind):
        self.nodes_pool = nodes_pool

        self.sock = socket.socket(socket.AF_INET, kind)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)

        self.sock.bind((host, 0))

        self.port = self.sock.getsockname()[1]
        self.is_disseminated = False


    def xmit(self, msg: MessageType, neighbours: Iterable) -> threading.Thread:
        def _xmit():
            for neigh in neighbours:
                self.sock.sendto(pickle.dumps(msg), neigh.sock.getsockname())
                log_node('xmit [%i] -> (%i)', self.port, neigh.port)

        t = threading.Thread(target=_xmit)
        t.start()
        return t


    def recv(self) -> threading.Thread:
        def _recv():
            try:
                data, addr = self.sock.recvfrom(self.BUFFER_SIZE)
                msg = pickle.loads(data)

                log_node('recv [%i] <- (%i): %s', self.port, addr[1],
                              str(msg))

                if self.is_disseminated and msg == MessageType.PULL:
                    log_node('xmit [%i] -> (%i): ACK[%s]', self.port,
                                  addr[1], str(MessageType.PUSH))
                    self.sock.sendto(pickle.dumps(MessageType.PUSH), addr)

                if msg == MessageType.PUSH:
                    log_node('recv [%i]: is disseminated', self.port)
                    self.is_disseminated = True
            except socket.error as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    return
                logging.critical('recv [%i]: socker error', self.port,
                                 exc_info=e)
            except Exception as e:
                logging.critical('recv [%i]: unforeseen error', self.port,
                                 exc_info=e)

        t = threading.Thread(target=_recv)
        t.start()
        return t


class NodesPool:
    def __init__(self, nodes_n: int):
        self.nodes = [ Node(self, '127.0.0.1', socket.SOCK_DGRAM) for _ in range(nodes_n) ]


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        for node in self.nodes:
            ip, port = node.sock.getsockname()
            logging.debug('closing socket %s/%i at pool...', ip, port)
            node.sock.close()


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

