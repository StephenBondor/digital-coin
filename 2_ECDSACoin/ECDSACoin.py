import pickle
from ecdsa import SigningKey, SECP256k1, BadSignatureError

# the bank is the issuing source of truth, bad bank!
bank_private_key = SigningKey.generate(curve=SECP256k1)
bank_public_key = bank_private_key.get_verifying_key()


def serialize(coin):
    return pickle.dumps(coin)


def transfer_message(prev_sig, next_pub_key):
    return serialize({"prev_sig": prev_sig, "next_owner_pub_key": next_pub_key})


class Transfer:
    def __init__(self, signature, public_key):
        self.signature = signature
        self.public_key = public_key


class ECDSACoin:
    def __init__(self, transfers):
        self.transfers = transfers

    def validate(self):
        prev_transfer = self.transfers[0]  # Check the first transfer
        message = serialize(prev_transfer.public_key)
        assert bank_public_key.verify(prev_transfer.signature, message)
        for transfer in self.transfers[1:]:  # Check the subsequent transfers
            assert prev_transfer.public_key.verify(
                transfer.signature,
                transfer_message(prev_transfer.signature, transfer.public_key),
            )  # Check previous owner signed this transfer using their private key
            prev_transfer = transfer  # set prev to current, repeat


def issue(public_key):
    message = serialize(public_key)  # Create a message specifying the recipient
    signature = bank_private_key.sign(message)  # signing with the banks private key
    transfer = Transfer(signature, public_key)  # Create transfer
    return ECDSACoin([transfer])  # Return the newly created coin


# Alternatively, but ew gross:
# def issue(pub_key):
#     return ECDSACoin([Transfer(bank_private_key.sign(serialize(pub_key)), pub_key)])


if __name__ == "__main__":
    # Testing signing:
    # private_key = SigningKey.generate(curve=SECP256k1)
    # public_key = private_key.get_verifying_key()
    # message = b"i need coffee"
    # signature = private_key.sign(message)
    # public_key.verify(signature, message)
    # public_key.verify(signature, b"i need coffee")
    # END TESTS

    bob_private_key = SigningKey.generate(curve=SECP256k1)
    alice_private_key = SigningKey.generate(curve=SECP256k1)
    bob_public_key = bob_private_key.get_verifying_key()
    alice_public_key = alice_private_key.get_verifying_key()

    # The great Saga of Bob trying to steal Alice's coin
    # alice_coin = issue(alice_public_key)  # Alice gets issued coin
    # alice_coin.validate()  # That coin is valide, yo
    # bob_takes_alice_coin = Transfer(
    #     signature=bob_private_key.sign(serialize(bob_public_key)),
    #     public_key=bob_public_key,
    # )  # bob tries to steal it without having the right private key
    # alt_coin = ECDSACoin([bob_takes_alice_coin])
    # try:
    #     alt_coin.validate()
    # except BadSignatureError:
    #     print("Bad signature detected -- BAD BOB")
    # END SAGA

    def get_owner(coin):
        database = {
            serialize(bob_public_key): "Bob",
            serialize(alice_public_key): "Alice",
            serialize(bank_public_key): "Bank",
        }
        public_key = serialize(coin.transfers[-1].public_key)
        return database[public_key]

    # The Great WHO OWNS THIS COIN SAGA
    # coin = issue(alice_public_key)
    # print("this coin is owned by", get_owner(coin))
    # message = transfer_message(coin.transfers[-1].signature, bob_public_key)
    # alice_to_bob = Transfer(
    #     signature=alice_private_key.sign(message), public_key=bob_public_key
    # )
    # coin.transfers.append(alice_to_bob)
    # print("this coin is owned by", get_owner(coin))
    # message = transfer_message(coin.transfers[-1].signature, bank_public_key)
    # bob_to_bank = Transfer(
    #     signature=bob_private_key.sign(message), public_key=bank_public_key
    # )
    # coin.transfers.append(bob_to_bank)
    # print("this coin is owned by", get_owner(coin))
    # END SAGA

    coin = issue(alice_public_key)
    coin.validate()
    print("this coin is owned by", get_owner(coin))

    alice_to_bob = Transfer(
        alice_private_key.sign(
            transfer_message(coin.transfers[-1].signature, bob_public_key)
        ),
        bob_public_key,
    )

    coin.transfers.append(alice_to_bob)
    coin.validate()
    print("this coin is owned by", get_owner(coin))

    # ECDSA COIN DOES NOT SOLVE THE DOUBLE SPEND PROBLEM!
