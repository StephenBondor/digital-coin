import time
import socket
from random import randint
from hashlib import sha256
from io import BytesIO


def double_sha256(s):
    return sha256(sha256(s).digest()).digest()


def compute_checksum(s):
    return double_sha256(s)[:4]

# Consider adding more standard bitcoin functioanlity?

####################
# READING MESSAGES #
####################

ZERO = b"\x00"
NETWORK_MAGIC = b"\xf9\xbe\xb4\xd9"
IPV4_PREFIX = ZERO * 12


def read_varint(stream):
    small_int = stream.read(1)[0]
    try:
        length = {0xFF: 8, 0xFE: 4, 0xFD: 2}[small_int]
        return int.from_bytes(stream.read(length), "little")
    except:
        return small_int


def read_varstr(stream):
    length = read_varint(stream)
    return stream.read(length)


def bytes_to_ip(b):
    if b[0:12] == IPV4_PREFIX:
        return socket.inet_ntop(socket.AF_INET, b[12:16])
    else:
        return socket.inet_ntop(socket.AF_INET6, b)


def read_address(stream, has_timestamp=True):
    r = {}
    if has_timestamp:
        r["timestamp"] = int.from_bytes(stream.read(4), "little")
    r["services"] = int.from_bytes(stream.read(8), "little")
    r["ip"] = bytes_to_ip(stream.read(16))
    r["port"] = int.from_bytes(stream.read(2), "big")
    return r


def read_version_payload(stream):
    r = {}
    r["version"] = int.from_bytes(stream.read(4), "little")
    r["services"] = int.from_bytes(stream.read(8), "little")
    r["timestamp"] = int.from_bytes(stream.read(8), "little")
    r["receiver_address"] = read_address(stream, has_timestamp=False)
    r["sender_address"] = read_address(stream, has_timestamp=False)
    r["nonce"] = int.from_bytes(stream.read(8), "little")
    r["user_agent"] = read_varstr(stream)
    r["start_height"] = int.from_bytes(stream.read(4), "little")
    r["relay"] = bool(stream.read(1))
    return r


def read_message(stream):
    msg = {}
    magic = stream.read(4)
    if magic != NETWORK_MAGIC:
        raise Exception(f"Magic is not {NETWORK_MAGIC}, it's: {magic}")
    msg["command"] = stream.read(12).strip(ZERO)
    payload_length = int.from_bytes(stream.read(4), "little")
    checksum = stream.read(4)
    msg["payload"] = stream.read(payload_length)
    if compute_checksum(msg["payload"]) != checksum:
        raise Exception("Checksum does not match")
    return msg


#####################
# CREATING MESSAGES #
#####################


dummy_address = {"services": 0, "ip": "0.0.0.0", "port": 8333}


def ip_to_bytes(ip):
    if ":" in ip:
        return socket.inet_pton(socket.AF_INET6, ip)
    else:
        return IPV4_PREFIX + socket.inet_pton(socket.AF_INET, ip)


def serialize_address(address, has_timestamp=True):
    r = b""
    if has_timestamp:
        r += address["timestamp"].to_bytes(8, "little")
    r += address["services"].to_bytes(8, "little")
    r += ip_to_bytes(address["ip"])
    r += address["port"].to_bytes(2, "big")
    return r


def services_dict_to_int(services_dict):
    key_multiplier = {
        "NODE_NETWORK": 2 ** 0,
        "NODE_GETUTXO": 2 ** 1,
        "NODE_BLOOM": 2 ** 2,
        "NODE_WITNESS": 2 ** 3,
        "NODE_NETWORK_LIMITED": 2 ** 10,
    }
    services_int = 0
    for key, on_or_off in services_dict.items():
        services_int += int(on_or_off) * key_multiplier.get(key, 0)
    return services_int


def serialize_varint(i):
    if i < 0xFD:
        return bytes([i])
    elif i < 256 ** 2:
        return b"\xfd" + i.to_bytes(2, "little")
    elif i < 256 ** 4:
        return b"\xfe" + i.to_bytes(4, "little")
    elif i < 256 ** 8:
        return b"\xff" + i.to_bytes(8, "little")
    else:
        raise RuntimeError(f"Integer is too large: {i}")


def serialize_varstr(b):
    return serialize_varint(len(b)) + b


def serialize_version_payload(
    version=70015,
    services_dict={},
    timestamp=None,
    receiver_address=dummy_address,
    sender_address=dummy_address,
    nonce=None,
    user_agent=b"/buidl-bootcamp/",
    start_height=0,
    relay=True,
):
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        nonce = randint(0, 2 ** 64)
    msg = version.to_bytes(4, "little")
    msg += services_dict_to_int(services_dict).to_bytes(8, "little")
    msg += timestamp.to_bytes(8, "little")
    msg += serialize_address(receiver_address, has_timestamp=False)
    msg += serialize_address(sender_address, has_timestamp=False)
    msg += nonce.to_bytes(8, "little")
    msg += serialize_varstr(user_agent)  # zero byte signifies an empty varstr
    msg += start_height.to_bytes(4, "little")
    msg += bytes([relay])
    return msg


def serialize_message(command=b"version", payload=b""):
    r = NETWORK_MAGIC
    r += command + ZERO * (12 - len(command))
    r += len(payload).to_bytes(4, "little")
    r += compute_checksum(payload)
    r += payload
    return r


def handshake(address):
    sock = socket.create_connection(address, timeout=10)
    stream = sock.makefile("rb")

    # Step 1: Send our version message
    payload = serialize_version_payload()
    sock.sendall(serialize_message(command=b"version", payload=payload))
    print("Sent our version")

    # Step 2: Receive their version message
    version = read_message(stream)
    print(f"Version Received: {version}")

    # Step 3: Receive their verack message
    peer_verack = read_message(stream)
    print("Verack Received: ", peer_verack)

    # Step 4: Send our verack
    sock.sendall(serialize_message(command=b"verack"))
    print("Sent verack")

    return sock
