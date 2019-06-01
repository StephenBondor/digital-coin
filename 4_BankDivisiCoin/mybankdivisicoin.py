from uuid import uuid4


class Tx:  # a transaction
    def __init__(self, id, tx_ins, tx_outs):
        self.id = id
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs

    def sign_input(self, index, private_key):
        signature = private_key.sign(self.tx_ins[index].spend_message())
        self.tx_ins[index].signature = signature


class TxIn:  # an input transaction
    def __init__(self, tx_id, index, signature):
        self.tx_id = tx_id
        self.index = index
        self.signature = signature

    def spend_message(self):  # this is equivalent to transfer_message in previous coins
        return f"{self.tx_id}:{self.index}".encode()


class TxOut:  # an output transaction
    def __init__(self, tx_id, index, amount, public_key):
        self.tx_ins = tx_id
        self.tx_outs = index
        self.amount = amount
        self.public_key = public_key


class Bank:  # bank is still central authority
    def __init__(self):
        self.txs = {}

    def issue(self, amount, public_key):  # issues a new coin
        id = uuid4()
        tx_outs = [TxOut(id, 0, amount, public_key)]
        tx = Tx(id, [], tx_outs)
        self.txs[tx.id] = tx
        return tx

    def is_unspent(self, tx_in):  # makes sure its all unspent
        for tx in self.txs.values():
            for _tx_in in tx.tx_ins:
                if tx_in.tx_id == _tx_in.tx_id and tx_in.index == _tx_in.index:
                    return False
        return True

    def validate_tx(self, tx):
        in_sum = 0  # get the inputs
        for tx_in in tx.tx_ins:  # loop over all inputs for the tx
            assert self.is_unspent(tx_in)  # check if its unspent
            tx_out = self.txs[tx_in.tx_id].tx_outs[tx_in.index]  # check if sig matches
            tx_out.public_key.verify(tx_in.signature, tx_in.spend_message())
            in_sum += tx_out.amount  # add to the in_sum
        out_sum = sum(tx_out.amount for tx_out in tx.tx_outs)  # get the outputs
        assert in_sum == out_sum  # make sure the inputs and outputs match

    def handle_tx(self, tx):  # validates and adds a tx
        self.validate_tx(tx)
        self.txs[tx.id] = tx

    def fetch_utxo(self, public_key):  # get the utxo's for pub)key
        spent_pairs = [  # Find which (tx_id, index) pairs have been spent
            (tx_in.tx_id, tx_in.index)
            for tx in self.txs.values()
            for tx_in in tx.tx_ins
        ]
        return [  # Return tx_outs associated with public_key and not in ^^ list
            tx_out
            for tx in self.txs.values()
            for i, tx_out in enumerate(tx.tx_outs)
            if public_key.to_string() == tx_out.public_key.to_string()
            and (tx.id, i) not in spent_pairs
        ]

    def fetch_balance(self, public_key):  # get the balance for a pub key
        return sum([tx_out.amount for tx_out in self.fetch_utxo(public_key)])
