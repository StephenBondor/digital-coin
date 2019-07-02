from exercises import *
import time, socket, threading, queue, logging

logging.basicConfig(level="INFO", filename="crawler.log")
logger = logging.getLogger(__name__)

DNS_SEEDS = [
    "dnsseed.bitcoin.dashjr.org",
    "dnsseed.bluematt.me",
    "seed.bitcoin.sipa.be",
    "seed.bitcoinstats.com",
    "seed.bitcoin.jonasschnelli.ch",
    "seed.btc.petertodd.org",
    "seed.bitcoin.sprovoost.nl",
    "dnsseed.emzy.de",
]


def read_addr_payload(stream):
    # return a list of varint-many read_address objects.
    return [read_address(stream) for _ in range(read_varint(stream))]


def query_dns_seeds():
    nodes = []
    for seed in DNS_SEEDS:
        try:
            addr_info = socket.getaddrinfo(seed, 8333, 0, socket.SOCK_STREAM)
            addresses = [ai[-1][:2] for ai in addr_info]
            nodes.extend([Node(*addr) for addr in addresses])
        except OSError as e:
            logger.info(f"DNS seed query failed: {str(e)}")
    return nodes


class Node:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    @property
    def address(self):
        return (self.ip, self.port)


class Connection:
    def __init__(self, node, timeout):
        self.node = node
        self.timeout = timeout
        self.sock = None
        self.stream = None
        self.start = None

        # Results
        self.peer_version_payload = None
        self.nodes_discovered = []

    #################
    # Send Messages #
    #################

    def send_version(self):
        payload = serialize_version_payload()
        self.sock.sendall(serialize_message(command=b"version", payload=payload))

    def send_verack(self):
        msg = serialize_message(command=b"verack")
        self.sock.sendall(msg)

    def send_pong(self, payload):
        res = serialize_message(command=b"pong", payload=payload)
        self.sock.sendall(res)

    def send_getaddr(self):
        self.sock.sendall(serialize_message(b"getaddr"))

    ###################
    # Handle Commands #
    ###################

    def handle_version(self, payload):
        self.peer_version_payload = read_version_payload(BytesIO(payload))
        self.send_verack()  # Acknowledge them biddies

    def handle_verack(self, payload):
        self.send_getaddr()  # handshake complete, request addresses

    def handle_ping(self, payload):
        self.send_pong(payload)

    def handle_addr(self, payload):
        payload = read_addr_payload(BytesIO(payload))
        if len(payload) > 1:
            self.nodes_discovered = [Node(a["ip"], a["port"]) for a in payload]

    ##################
    # Handle Message #
    ##################

    def handle_msg(self):
        msg = read_message(self.stream)
        cmd = msg["command"].decode()
        logger.info(f'Received a message "{cmd}"')
        method_name = f"handle_{cmd}"
        if hasattr(self, method_name):
            getattr(self, method_name)(msg["payload"])

    def remain_alive(self):
        timed_out = time.time() - self.start > self.timeout
        return not timed_out and not self.nodes_discovered

    def open(self):
        # Initiate Handshake
        self.start = time.time()
        logger.info(f"Connecting to {self.node.ip}")
        self.sock = socket.create_connection(self.node.address, timeout=self.timeout)
        self.stream = self.sock.makefile("rb")
        self.send_version()

        # Handle messages until program exits
        while self.remain_alive():
            self.handle_msg()

    def close(self):  # Clean up sockets file descriptor
        if self.sock:
            self.sock.close()


class Worker(threading.Thread):
    def __init__(self, worker_ins, worker_outs, timeout):
        super().__init__()
        self.worker_ins = worker_ins
        self.worker_outs = worker_outs
        self.timeout = timeout

    def run(self):
        while True:
            # queues lock and this line spins until something is here
            node = self.worker_ins.get()
            try:
                cnxn = Connection(node, timeout=self.timeout)
                cnxn.open()  # Open Socket
            except (OSError, BitcoinProtocolError) as e:
                logger.info(f"Got error: {str(e)}")
            finally:
                cnxn.close()  # Close Socket
            self.worker_outs.put(cnxn)  # report results back to crawler


class Crawler:
    def __init__(self, num_workers=10, timeout=10):
        self.timeout = timeout
        self.worker_ins = queue.Queue()
        self.worker_outs = queue.Queue()
        self.workers = [
            Worker(self.worker_ins, self.worker_outs, self.timeout)
            for _ in range(num_workers)
        ]

    def seed(self):
        for node in query_dns_seeds():
            self.worker_ins.put(node)

    def print_report(self):
        print(f"ins: {self.worker_ins.qsize()} | outs: {self.worker_outs.qsize()}")

    def main_loop(self):
        while True:
            cnxn = self.worker_outs.get()
            for node in cnxn.nodes_discovered:
                self.worker_ins.put(node)
            logger.info(f"{cnxn.node.ip} report version {cnxn.peer_version_payload}")
            self.print_report()

    def crawl(self):
        self.seed()  # get the seeds
        for worker in self.workers:  # start all the workers
            worker.start()
        self.main_loop()


if __name__ == "__main__":
    Crawler(num_workers=25, timeout=1).crawl()
