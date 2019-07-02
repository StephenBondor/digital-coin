import random, time, threading

# This is code to demonstrait how to use OOP to organize a threading model.


def connect(address):
    print(f"connecting to {address}")
    seconds = random.random()
    time.sleep(seconds)
    print(f"connection to {address} took {seconds} seconds")


class Connection:
    def __init__(self, node):
        self.node = node

    def open(self):
        connect(self.node)


class ConnectionWorker(threading.Thread):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def run(self):
        Connection(self.node).open()


for node in range(10):
    # connect(node)
    # thread = threading.Thread(target=connect, args=(node,))
    # thread.start()

    thread = ConnectionWorker(node)
    thread.start()
