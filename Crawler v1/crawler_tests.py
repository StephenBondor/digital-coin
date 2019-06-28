from exercises import *


############
## TESTING #
############


def test_int_to_little_endian():
    integer = 22
    bytes = b"\x16\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    result = int_to_little_endian(integer, 10)
    assert bytes == result, f"Correct answer: {bytes}. Your answer: {result}"
    print("Little Endian Tests passed!")


def test_int_to_big_endian():
    integer = 22
    bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x16"
    result = int_to_big_endian(integer, 10)
    assert bytes == result, f"Correct answer: {bytes}. Your answer: {result}"
    print("Big Endian Tests passed!")


def test_serialize_version_payload_integers():
    now = int(time.time()) - 10
    version_payload_dict = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_GETUTXO": True},
        nonce=4,
        timestamp=now,
        start_height=50,
    )
    version_payload = read_version_payload(BytesIO(version_payload_dict))
    assert version_payload["version"] == 70015
    assert version_payload["services"] == 3
    assert version_payload["timestamp"] == now
    assert version_payload["nonce"] == 4
    assert version_payload["start_height"] == 50
    print("Serialize Payload with Integers Test passed!")


def test_services_dict_to_int():
    services_dict = {
        "NODE_NETWORK": True,
        "NODE_GETUTXO": False,
        "NODE_BLOOM": True,
        "NODE_WITNESS": False,
        "NODE_CASH": True,
        "NODE_NETWORK_LIMITED": True,
    }
    answer = 1 + 4 + 1024
    result = services_dict_to_int(services_dict)
    assert (
        answer == result
    ), f"services_dict_to_int({repr(services_dict)}) should equal {answer}, was {result}"
    print("Services dict to int Test passed!")


def test_serialize_version_payload_services_dict():
    now = int(time.time()) - 10
    version_payload = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_BLOOM": True},
        nonce=4,
        timestamp=now,
        start_height=50,
    )
    version_payload = read_version_payload(BytesIO(version_payload))
    assert version_payload["version"] == 70015
    assert version_payload["services"] == 5
    assert version_payload["timestamp"] == now
    assert version_payload["nonce"] == 4
    assert version_payload["start_height"] == 50
    print("Serialize Version Payload Test passed!")


def test_bytes_to_bool():
    assert (
        bool_to_bytes(True) == b"\x01"
    ), f'bool_to_bytes(False) should equal b"\\x01", was {bool_to_bytes(True)}'
    assert (
        bool_to_bytes(False) == b"\x00"
    ), f'bool_to_bytes(False) should equal b"\\x00", was {bool_to_bytes(False)}'
    print("Bool to Bytes Test passed!")


def test_serialize_version_payload_booleans():
    now = int(time.time()) - 10
    version_payload = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_BLOOM": True},
        nonce=4,
        timestamp=now,
        start_height=50,
        user_agent=b"/buidl-army/",
    )
    version_payload = read_version_payload(BytesIO(version_payload))
    assert version_payload["version"] == 70015
    assert version_payload["services"] == 5
    assert version_payload["timestamp"] == now
    assert version_payload["nonce"] == 4
    assert version_payload["start_height"] == 50
    assert (
        version_payload["user_agent"] == b"/buidl-army/"
    ), f'version_payload["user_agent"] is {version_payload["user_agent"]}, should be b"/buidl-army/"'
    assert (
        version_payload["relay"] is True
    ), f'version_payload["relay"] is {version_payload["relay"]}, should be "True"'
    print("Serialize Version Payload Booleans Test passed!")


def test_serialize_version_payload_VarStr():
    now = int(time.time()) - 10
    version_payload = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_BLOOM": True},
        nonce=4,
        timestamp=now,
        start_height=50,
        user_agent=b"/buidl-army/",
    )
    version_payload = read_version_payload(BytesIO(version_payload))
    assert version_payload["version"] == 70015
    assert version_payload["services"] == 5
    assert version_payload["timestamp"] == now
    assert version_payload["nonce"] == 4
    assert version_payload["start_height"] == 50
    assert version_payload["user_agent"] == b"/buidl-army/"
    print("Serialize Version Payload VarStr Test passed!")


def test_serialize_version_payload_network_addresses():
    now = int(time.time()) - 10
    version_payload = serialize_version_payload(
        services_dict={"NODE_NETWORK": True, "NODE_BLOOM": True},
        nonce=4,
        timestamp=now,
        start_height=50,
        user_agent=b"/buidl-army/",
    )
    version_payload = read_version_payload(BytesIO(version_payload))
    assert version_payload["version"] == 70015
    assert version_payload["services"] == 5
    assert version_payload["timestamp"] == now
    assert version_payload["receiver_address"] == dummy_address
    assert version_payload["sender_address"] == dummy_address
    assert version_payload["nonce"] == 4
    assert version_payload["start_height"] == 50
    assert version_payload["user_agent"] == b"/buidl-army/"
    print("Serialize Version Payload Network Addresses Test passed!")


def test_serialize_message():
    m = serialize_message(command=b"version", payload=b"foo")
    assert m[0:4] == bytes([249, 190, 180, 217])
    assert m[4:16] == b"version" + (5 * b"\x00")
    assert m[16:20] == b"\x03\x00\x00\x00"
    assert m[20:24] == b"\xc7\xad\xe8\x8f"
    assert m[24:] == b"foo"
    print("Serialize Message Tests passed!")


if __name__ == "__main__":
    test_int_to_little_endian()
    test_int_to_big_endian()
    test_serialize_version_payload_integers()
    test_services_dict_to_int()
    test_serialize_version_payload_services_dict()
    test_bytes_to_bool()
    test_serialize_version_payload_booleans()
    test_serialize_version_payload_VarStr()
    test_serialize_version_payload_network_addresses()
    test_serialize_message()
