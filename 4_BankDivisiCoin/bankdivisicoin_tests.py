import uuid
from ecdsa import SigningKey, SECP256k1
from mybankdivisicoin import TxIn, TxOut, Tx, Bank

# The usual suspects
bob_private_key = SigningKey.generate(curve=SECP256k1)
alice_private_key = SigningKey.generate(curve=SECP256k1)
bob_public_key = bob_private_key.get_verifying_key()
alice_public_key = alice_private_key.get_verifying_key()


def test_bank_balances():
    # Create bank and issue Alice some coins
    bank = Bank()
    coinbase = bank.issue(1000, alice_public_key)
    tx_ins = [TxIn(coinbase.id, 0, None)]
    tx_id = uuid.uuid4()

    tx_outs = [  # Alice sends 10 coins to Bob
        TxOut(tx_id, 0, 10, bob_public_key),
        TxOut(tx_id, 1, 990, alice_public_key),
    ]
    alice_to_bob = Tx(tx_id, tx_ins, tx_outs)
    alice_to_bob.sign_input(0, alice_private_key)
    bank.handle_tx(alice_to_bob)

    assert 990 == bank.fetch_balance(alice_public_key)
    assert 10 == bank.fetch_balance(bob_public_key)
