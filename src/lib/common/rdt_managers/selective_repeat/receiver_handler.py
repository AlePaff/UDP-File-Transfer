from threading import Thread, Event

from lib.common.message import Message

# La clase receiver handler es la interfaz entre la capa de aplicacion y el protocolo de transporte


class ReceiverHandler:

    packetHandler = None

    def __init__(self, socket):
        self.packetHandler = PacketHandler(socket)
        self.packetHandler.start()

    def recv(self):
        return self.packetHandler.recv()


# La clase packet handler es la que se encarga de recibir los mensajes y encolarlos en el orden correcto

class PacketHandler(Thread):
    def __init__(self, socket):
        super(PacketHandler, self).__init__()
        self.socket = socket
        self.window = Window(10)
        self.packet_to_read = Event()

    def run(self):
        while (True):
            packet, addr = self.socket.recv()
            msg = Message.parse(packet)
            seq_num = msg.get_header()
            payload = msg.get_payload()

            if (self.window.packet_inside_window(seq_num)):
                self.window.store(seq_num, payload)
                self.send_ack(seq_num)

            elif (self.window.packet_was_received(seq_num)):
                self.send_ack(seq_num)

            if (self.window.packets_to_read()):
                self.packet_to_read.set()

    def recv(self):
        if (not self.window.packets_to_read()):
            self.packet_to_read.wait()
        self.packet_to_read.clear()

        return self.window.next()

    def send_ack(self, ack_num):
        self.socket.send(("ACK " + str(ack_num)).encode())


# La clase window es la representacion de la ventana de recepcion

class Window:
    def __init__(self, size):
        self.max_window_size = size
        self.base = 0
        self.packets = {}

    def packet_exist(self, seq_num):
        return seq_num in self.packets

    def packet_inside_window(self, seq_num):
        return self.base <= seq_num < self.base + self.max_window_size

    def packet_was_received(self, seq_num):
        return seq_num < self.base

    def store(self, seq_num, packet):
        self.packets[seq_num] = packet

    def next(self):
        if (self.base not in self.packets):
            return None

        self.base += 1
        return self.packets.pop(self.base - 1)

    def is_full(self):
        return len(self.packets) == self.max_window_size

    def packets_to_read(self):
        return self.packet_exist(self.base)
