from PIL import Image
import pickle
import io
from contextlib import suppress


###########
# Helpers #
###########

# help with user verification
def handle_user_input():
    while True:  # Loop until the user returns a 'y' or 'n'
        with suppress(Exception):
            return {"y": True, "n": False}[input("Valid sig? (y/n): ").lower()]


############
# PNG Coin #
############


class PNGCoin:
    def __init__(self, transfers):
        self.transfers = transfers  # PIL.Image list

    def serialize(self):  # convert self to bytes
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, serialized):  # convert bytes to self
        return pickle.loads(serialized)

    def to_disk(self, filename):  # write to disk as a file
        serialized = self.serialize()
        with open(filename, "wb") as f:
            f.write(serialized)

    @classmethod
    def from_disk(cls, filename):  # read file from disk and set to self
        with open(filename, "rb") as f:
            serialized = f.read()
            return cls.deserialize(serialized)

    def validate(self):  # use user input to validate coin
        for transfer in self.transfers:
            transfer.show()
            if not handle_user_input():
                return False
        return True


if __name__ == "__main__":
    coin = PNGCoin([Image.open("alice.png"), Image.open("alice-to-bob.png")])
    bad_coin = PNGCoin([Image.open("alice.png"), Image.open("alice-to-bob-forged.png")])

    print(f"Is this chain valid? {coin.validate()}")
    # bad_coin.validate()
    # coin.to_disk("saved_work.txt")
    # coin.from_disk("saved_work.txt")
