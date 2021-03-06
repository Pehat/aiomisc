import asyncio
import itertools
import logging.handlers
import socket
from multiprocessing import cpu_count
from typing import Iterable, Any, List, Tuple

import uvloop

from aiomisc.thread_pool import ThreadPoolExecutor


log = logging.getLogger(__name__)


def chunk_list(iterable: Iterable[Any], size: int):
    iterable = iter(iterable)

    item = list(itertools.islice(iterable, size))
    while item:
        yield item
        item = list(itertools.islice(iterable, size))


OptionsType = List[Tuple[int, int, int]]


def bind_socket(*, address: str, port: int, options=()):
    if ':' in address:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setblocking(0)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock_addr = address, port

    if sock.family == socket.AF_INET6:
        log.info('Listening tcp://[%s]:%s' % sock_addr)
    else:
        log.info('Listening tcp://%s:%s' % sock_addr)

    try:
        sock.bind(sock_addr)
    finally:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)

    for level, option, value in options:
        sock.setsockopt(level, option, value)

    return sock


def new_event_loop(pool_size=None) -> asyncio.AbstractEventLoop:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    pool_size = pool_size or cpu_count()

    asyncio.get_event_loop().close()

    loop = asyncio.new_event_loop()
    thread_pool = ThreadPoolExecutor(pool_size, loop=loop)

    loop.set_default_executor(thread_pool)

    asyncio.set_event_loop(loop)

    return loop
