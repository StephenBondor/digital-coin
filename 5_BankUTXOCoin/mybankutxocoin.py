import uuid
from ecdsa import SigningKey, SECP256k1

# centrally issued, divisible


class Tx:
    def __init__(self, id, tx_ins, tx_outs):
        self.id = id
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs

    def sign_input(self, index, private_key):
        signature = private_key.sign(self.tx_ins[index].spend_message)
        self.tx_ins[index].signature = signature


class TxIn:
    def __init__(self, tx_id, index, signature=None):
        self.tx_id = tx_id
        self.index = index
        self.signature = signature

    @property
    def spend_message(self):
        return f"{self.tx_id}:{self.index}".encode()

    @property
    def outpoint(self):
        return (self.tx_id, self.index)


class TxOut:
    def __init__(self, tx_id, index, amount, public_key):
        self.tx_id = tx_id
        self.index = index
        self.amount = amount
        self.public_key = public_key

    @property
    def outpoint(self):
        return (self.tx_id, self.index)


class Bank:
    def __init__(self):
        self.utxo = {}

    def update_utxo(self, tx):
        for tx_in in tx.tx_ins:
            del self.utxo[tx_in.outpoint]
        for tx_out in tx.tx_outs:
            self.utxo[tx_out.outpoint] = tx_out

    def issue(self, amount, public_key):
        id_ = str(uuid.uuid4())
        tx_outs = [TxOut(id_, 0, amount, public_key)]
        tx = Tx(id_, [], tx_outs)
        self.update_utxo(tx)
        return tx

    def validate_tx(self, tx):
        in_sum = 0  # get the inputs
        for tx_in in tx.tx_ins:  # loop over all inputs for the tx
            assert tx_in.outpoint in self.utxo  # check if its unspent
            tx_out = self.utxo[tx_in.outpoint]  # check if the sigs match
            tx_out.public_key.verify(tx_in.signature, tx_in.spend_message)
            in_sum += tx_out.amount  # Sum up the total inputs
        out_sum = sum(tx_out.amount for tx_out in tx.tx_outs)  # get the outputs
        assert in_sum == out_sum  # make sure the inputs and outputs match

    def handle_tx(self, tx):
        self.validate_tx(tx)  # Save to self.txs if it's valid
        self.update_utxo(tx)  # self.txs[tx.id] = tx

    def fetch_utxo(self, pub_key):
        return [
            utxo
            for utxo in self.utxo.values()
            if utxo.public_key.to_string() == pub_key.to_string()
        ]

    def fetch_balance(self, public_key):  # get the balance for a pub key
        return sum([tx_out.amount for tx_out in self.fetch_utxo(public_key)])
