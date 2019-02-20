
from serial import Serial
from .bootstream import make_bootstream

class GA144Serial:
    def __init__(self, chips, port, speed):
        self.chips = chips
        self.serial = Serial(port, speed)
        self.serial.reset_input_buffer()

        self.data = []
        self.errors = []

    def send_bootstream(self, stream):
        #if target:
        #    target.setRTS(0)
        #    target.setRTS(1)
        serial = self.serial
        serial.setRTS(0)
        serial.setRTS(1)
        serial.write(stream)
        serial.flush()

    def write_bootstream(self, bootstream_type):
        bs = make_bootstream(bootstream_type, self.chips)
        self.send_bootstream(bs.stream())

    def read_n(self, n):
        x = [ord(self.serial.read(1)) for _ in range(n)]
        x.reverse()
        word = 0
        for byte in x:
            word = (word << 8) | byte
        return word

    def listen(self):
        while True:
            n = self.read_n(1)
            if n == 1:
                print('[exit]')
                return
            if n == 0:
                n = self.read_n(3)
                print(n & 0x3ffff)
            else:
                raise Exception('unknown serial code: '+str(n))

    def gather(self):
        self.data = []
        self.errors = []
        while True:
            n = self.read_n(1)
            if n == 1:
                return
            if n == 0:
                n = self.read_n(3)
                self.data.append(n & 0x3ffff)
            else:
                self.errors.append(n)
