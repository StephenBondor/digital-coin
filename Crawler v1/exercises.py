import time
import socket
from random import randint
from hashlib import sha256
from io import BytesIO


def compute_checksum(bytes):
    first_round = sha256(bytes).digest()
    second_round = sha256(first_round).digest()
    return second_round[:4]


####################
# READING MESSAGES #
####################

ZERO = b"\x00"
NETWORK_MAGIC = b"\xf9\xbe\xb4\xd9"
IPV4_PREFIX = b"\x00" * 10 + b"\x00" * 2


def little_endian_to_int(b):
    return int.from_bytes(b, "little")


def big_endian_to_int(b):
    return int.from_bytes(b, "big")


def bytes_to_bool(bytes):
    return True if bytes == b"\x01" else False


def read_varint(stream):
    i = little_endian_to_int(stream.read(1))
    if i == 0xFF:
        return little_endian_to_int(stream.read(8))
    elif i == 0xFE:
        return little_endian_to_int(stream.read(4))
    elif i == 0xFD:
        return little_endian_to_int(stream.read(2))
    else:
        return i


def read_varstr(stream):
    length = read_varint(stream)
    string = stream.read(length)
    return string


def bytes_to_ip(b):
    # IPv4
    if b[0:12] == IPV4_PREFIX:
        return socket.inet_ntop(socket.AF_INET, b[12:16])
    # IPv6
    else:
        return socket.inet_ntop(socket.AF_INET6, b)


def read_address(stream, has_timestamp):
    r = {}
    if has_timestamp:
        r["timestamp"] = little_endian_to_int(stream.read(4))
    r["services"] = little_endian_to_int(stream.read(8))
    r["ip"] = bytes_to_ip(stream.read(16))
    r["port"] = big_endian_to_int(stream.read(2))
    return r


def read_version_payload(stream):
    r = {}
    r["version"] = little_endian_to_int(stream.read(4))
    r["services"] = little_endian_to_int(stream.read(8))
    r["timestamp"] = little_endian_to_int(stream.read(8))
    r["receiver_address"] = read_address(stream, has_timestamp=False)
    r["sender_address"] = read_address(stream, has_timestamp=False)
    r["nonce"] = little_endian_to_int(stream.read(8))
    r["user_agent"] = read_varstr(stream)
    r["start_height"] = little_endian_to_int(stream.read(4))
    r["relay"] = bytes_to_bool(stream.read(1))
    return r


def double_sha256(s):
    return sha256(sha256(s).digest()).digest()


def read_message(stream):
    msg = {}
    magic = stream.read(4)

    if magic != NETWORK_MAGIC:
        raise Exception(f"Magic is wrong: {magic}")

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


def serialize_address(address, has_timestamp):
    result = b""
    if has_timestamp:
        result += int_to_little_endian(address["timestamp"], 8)
    result += int_to_little_endian(address["services"], 8)
    result += ip_to_bytes(address["ip"])
    result += int_to_big_endian(address["port"], 2)
    return result


def int_to_little_endian(integer, length):
    return integer.to_bytes(length, "little")


def int_to_big_endian(integer, length):
    return integer.to_bytes(length, "big")


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


def bool_to_bytes(bool):
    return bytes([bool])


def serialize_varint(i):
    if i < 0xFD:
        return bytes([i])
    elif i < 256 ** 2:
        return b"\xfd" + int_to_little_endian(i, 2)
    elif i < 256 ** 4:
        return b"\xfe" + int_to_little_endian(i, 4)
    elif i < 256 ** 8:
        return b"\xff" + int_to_little_endian(i, 8)
    else:
        raise RuntimeError("integer too large: {}".format(i))


def serialize_varstr(bytes):
    return serialize_varint(len(bytes)) + bytes


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
    msg = int_to_little_endian(version, 4)
    msg += int_to_little_endian(services_dict_to_int(services_dict), 8)
    msg += int_to_little_endian(timestamp, 8)
    msg += serialize_address(receiver_address, has_timestamp=False)
    msg += serialize_address(sender_address, has_timestamp=False)
    msg += int_to_little_endian(nonce, 8)
    msg += serialize_varstr(user_agent)  # zero byte signifies an empty varstr
    msg += int_to_little_endian(start_height, 4)
    msg += bool_to_bytes(relay)
    return msg


def serialize_message(command=b"version", payload=b""):
    result = NETWORK_MAGIC
    result += command + ZERO * (12 - len(command))
    result += int_to_little_endian(len(payload), 4)
    result += compute_checksum(payload)
    result += payload
    return result


def handshake(address):
    sock = socket.create_connection(address, timeout=1)
    stream = sock.makefile("rb")

    # Step 1: our version message
    now = int(time.time()) - 10
    payload = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_BLOOM": True},
        nonce=4,
        timestamp=now,
        start_height=50,
        user_agent=b"/buidl-army/",)

    sock.sendall(serialize_message(command="version", payload=payload))
    print("Sent version")

    # Step 2: their version message
    peer_version = "READ THEIR VERSION MESSAGE HERE"
    print("Version: ")
    print(peer_version)

    # Step 3: their version message
    peer_verack = "READ THEIR VERACK MESSAGE HERE"
    print("Verack: ", peer_verack)

    # Step 4: our verack
    sock.sendall("OUR VERACK HERE")
    print("Sent verack")

    return sock, stream
