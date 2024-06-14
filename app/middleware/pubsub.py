from queue import Queue
import threading

class Broker():
    def __init__(self):
        self.subscribers: dict[str, list] = {}
        self.message_queue = Queue()

    def subscribe(self, topic: str, subscriber):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(subscriber)

    def receive_message(self, topic: str, message: dict):
        self.message_queue.put((topic, message))

    def process_messages(self):
        print("Processing messages")
        t = threading.Timer(5, self.process_messages)
        t.daemon = True
        t.start()
        while not self.message_queue.empty():
            topic, message = self.message_queue.get()
            print(topic, message)
            if topic in self.subscribers:
                for subscriber in self.subscribers[topic]:
                    subscriber.receive_message(message)

class Producer():
    def __init__(self, name: str):
        self.name = name 

    def publish(self, topic: str, message: dict):
        broker.receive_message(topic, message)

class Subscriber():
    def __init__(self, name: str):
        self.name = name

    def subscribe(self, topic: str):
        broker.subscribe(topic, self)

    def receive_message(self, message: dict):
        print(f"{self.name} received message: {message}")

broker = Broker()
t = threading.Thread(target=broker.process_messages)
t.daemon = True
# t.start()

