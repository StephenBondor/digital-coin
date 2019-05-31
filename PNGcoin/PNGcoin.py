from PIL import Image
import pickle
import io


###########
# Helpers #
###########


def handle_user_input(user_input):
    if user_input.lower() == "y":
        return True
    elif user_input.lower() == "n":
        return False
    else:
        user_input = input('Please enter "y" or "n"')
        return handle_user_input(user_input)


############
# PNG Coin #
############


class PNGCoin:
    def __init__(self, transfers):
        self.transfers = transfers  # PIL.Image instances

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, serialized):
        return pickle.loads(serialized)

    def to_disk(self, filename):
        serialized = self.serialize()
        with open(filename, "wb") as f:
            f.write(serialized)

    @classmethod
    def from_disk(cls, filename):
        with open(filename, "rb") as f:
            serialized = f.read()
            return cls.deserialize(serialized)

    def validate(self):
        for transfer in self.transfers:
            transfer.show()
            user_input = input("Is this a valid minting signature? (y/n)")
            if not handle_user_input(user_input):
                return False
        return True


if __name__ == "__main__":
    coin = PNGCoin([Image.open("alice.png"), Image.open("alice-to-bob.png")])
    bad_coin = PNGCoin([Image.open("alice.png"), Image.open("alice-to-bob-forged.png")])

    print(f"{coin.validate()}")
    # bad_coin.validate()
    # coin.to_disk("saved_work.txt")
    # coin.from_disk("saved_work.txt")
