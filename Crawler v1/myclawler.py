from exercises import *
import time, socket


def read_addr_payload(stream):
    # return a list of varint-many read_address objects.
    return [read_address(stream) for _ in range(read_varint(stream))]


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


def query_dns_seeds():
    nodes = []
    for seed in DNS_SEEDS:
        try:
            addr_info = socket.getaddrinfo(seed, 8333, 0, socket.SOCK_STREAM)
            addresses = [ai[-1][:2] for ai in addr_info]
            nodes.extend([Node(*addr) for addr in addresses])
        except OSError as e:
            print(f"DNS seed query failed: {str(e)}")
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
        print("Sent our version")

    def send_verack(self):
        msg = serialize_message(command=b"verack")
        self.sock.sendall(msg)
        print("Sent our verack")

    def send_pong(self, payload):
        res = serialize_message(command=b"pong", payload=payload)
        self.sock.sendall(res)
        print("Sent pong")

    def send_getaddr(self):
        self.sock.sendall(serialize_message(b"getaddr"))
        print("Sent request for addresses")

    ###################
    # Handle Commands #
    ###################

    def handle_version(self, payload):
        stream = BytesIO(payload)
        self.peer_version_payload = read_version_payload(stream)
        # Acknowledge them biddies
        self.send_verack()

    def handle_verack(self, payload):
        # handshake complete, request addresses
        self.send_getaddr()

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
        print(f'Received a message "{cmd}"')
        method_name = f"handle_{cmd}"
        if hasattr(self, method_name):
            getattr(self, method_name)(msg["payload"])

    def remain_alive(self):
        timed_out = time.time() - self.start > self.timeout
        return not timed_out and not self.nodes_discovered

    def open(self):
        self.start = time.time()

        # Initiate Handshake
        print(f"Connecting to {self.node.ip}")
        self.sock = socket.create_connection(self.node.address, timeout=self.timeout)
        self.stream = self.sock.makefile("rb")
        self.send_version()

        # Handle messages until program exits
        while self.remain_alive():
            self.handle_msg()

    def close(self):
        # Clean up sockets file descriptor
        if self.sock:
            self.sock.close()


class Crawler:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.nodes = []
        self.connections = []

    def seed(self):
        self.nodes.extend(query_dns_seeds())

    def print_report(self):
        print(f"nodes: {len(self.nodes)} | connections: {len(self.connections)}")

    def crawl(self):
        # Look up addresses form DNS
        self.seed()

        start = time.time()

        while time.time() - start < 30:
            # Get next address from next address
            node = self.nodes.pop()
            try:
                cnxn = Connection(node, timeout=self.timeout)
                cnxn.open()
            except (OSError) as e:
                print(f"Got error: {str(e)}")
                continue
            finally:
                cnxn.close()

            # Handle the results
            self.nodes.extend(cnxn.nodes_discovered)
            self.connections.append(cnxn)
            print(f"{cnxn.node.ip} report version {cnxn.peer_version_payload}")
            self.print_report()


if __name__ == "__main__":
    Crawler(timeout=1).crawl()
