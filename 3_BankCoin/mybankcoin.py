from ecdsa import SigningKey, SECP256k1
from copy import deepcopy
from uuid import uuid4
import pickle

# To solve double spend: Whatever the bank says goes!
# But it costs...
# No flexibility in tx construction
# 1 coin per tx
# 1 output per tx


def transfer_message(prev_sig, next_pub_key):
    return pickle.dumps({"prev_sig": prev_sig, "next_owner_pub_key": next_pub_key})


class Transfer:
    def __init__(self, signature, public_key):
        self.signature = signature
        self.public_key = public_key

    def __eq__(self, other):  # used for shallow comparison
        return (
            self.signature == other.signature
            and self.public_key.to_string() == other.public_key.to_string()
        )


class BankCoin:
    def __init__(self, transfers):
        self.transfers = transfers
        self.id = uuid4()

    def __eq__(self, other):  # used for shallow comparison
        return self.id == other.id and self.transfers == other.transfers

    def validate(self):
        prev_transfer = self.transfers[0]
        for transfer in self.transfers[1:]:  # loop through all the transfers
            assert prev_transfer.public_key.verify(
                transfer.signature,
                transfer_message(prev_transfer.signature, transfer.public_key),
            )  # Check previous owner signed this transfer using their private key
            prev_transfer = transfer  # set prev to current, repeat

    def transfer(self, owner_priv_key, recipient_pub_key):  # transfer a coin
        prev_sig = self.transfers[-1].signature  # take the last coin sig of the tx
        message = transfer_message(prev_sig, recipient_pub_key)  # create msg/tx
        transfer = Transfer(owner_priv_key.sign(message), recipient_pub_key)
        self.transfers.append(transfer)  # append to transfer list


class Bank:  # bank is the central authority that keeps track of everything
    def __init__(self):
        self.coins = {}

    def issue(self, public_key):  # issues a new coin
        transfer = Transfer(None, public_key)  # Create w/ None b/c we trust the bAnK
        coin = BankCoin([transfer])  # Create coin from transfer
        self.coins[coin.id] = deepcopy(coin)  # add coin to DB
        return coin

    def observe_coin(self, coin):  # bank observes that a transfer has taken place
        last_obsrv = self.coins[coin.id]  # get the last transfer
        last_obsrv_num_transfers = len(last_obsrv.transfers)  # comp num of transfers
        assert last_obsrv.transfers == coin.transfers[:last_obsrv_num_transfers]
        coin.validate()  # make sure that all following transfers are valid
        self.coins[coin.id] = deepcopy(coin)  # add to the coin database
        return coin

    def fetch_coins(self, public_key):  # get all the coins that a Pub_Key has
        coins = []
        for coin in self.coins.values():  # V why do we still need .to_string here? V
            if coin.transfers[-1].public_key.to_string() == public_key.to_string():
                coins.append(coin)
        return coins

        # same as:
        # return [
        #     coin
        #     for coin in self.coins.values()
        #     if coin.transfers[-1].public_key.to_string() == public_key.to_string()
        # ]
