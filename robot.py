import bluetooth
from time import sleep, time


class PacketType:
    STORAGE = 0x01
    SUPPLY = 0x02
    RADIATION = 0x03
    STOP = 0x04
    RESUME = 0x05
    STATUS = 0x06
    HEARTBEAT = 0x07


class Robot:

    def __init__(self):
        self.buffer = []
        self.packet_idx = 0
        self.packet_size = 0
        self.packet_type = 0
        self.data = []
        port = 1
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        server_sock.bind(("", port))
        server_sock.listen(1)

        while True:
            print("waiting for robot")
            client_sock, address = server_sock.accept()
            print("Accepted connection from ", address)

            last_heartbeat_time = time()
            last_radiation_time = time()
            high = True
            while True:
                now = time()

                try:
                    if now - last_heartbeat_time > 1.5:
                        last_heartbeat_time = now
                        heartbeat = Robot.create_packet(PacketType.HEARTBEAT, 255)
                        client_sock.send(heartbeat)

                    if now - last_radiation_time > 2.0:
                        last_radiation_time = now
                        if not high:
                            rad = Robot.create_packet(PacketType.RADIATION, 255, data=bytes([0x2C]))
                            high = True
                        else:
                            rad = Robot.create_packet(PacketType.RADIATION, 255, data=bytes([0xFF]))
                            high = False
                        client_sock.send(rad)

                    raw_data = client_sock.recv(1)
                    type, data = self.parse_data(raw_data)
                    if type and data:
                        print(type, data)

                    sleep(0.01)
                except bluetooth.btcommon.BluetoothError:
                    break

    @staticmethod
    def calc_checksum(packet):
        # 8 bit addition implementation
        eight_bit_sum = 0
        for val in packet[1:]:
            eight_bit_sum = (eight_bit_sum + val) & 0xFF
        return 0xff - eight_bit_sum

    @staticmethod
    def create_packet(pkt_type: int, src: int, data: bytes = None):
        length = 5
        if data:
            length += len(data)

        packet = bytes([0x5f, length, pkt_type, src, 0x00])
        if data:
            packet += data

        checksum = Robot.calc_checksum(packet)
        packet += bytes([checksum])
        return packet

    def parse_data(self, data):
        for byte in data:
            self.buffer.append(byte)
            if self.packet_idx == 0:
                if byte != 0x5F:
                    print("missing start byte")
                    self.clear()
                else:
                    self.packet_idx = 1
            elif self.packet_idx == 1:
                self.packet_size = byte
                if self.packet_size < 5:
                    print("length was %i, but must be >= 5" % self.packet_size)
                    self.clear()
                else:
                    self.packet_idx = 2
            elif self.packet_idx == 2:
                self.packet_type = byte
                if self.packet_type not in vars(PacketType).values():
                    print("unknown type %i" % self.packet_type)
                    self.clear()
                else:
                    self.packet_idx = 3
            elif self.packet_idx == 3:
                packet_src = byte
                if packet_src != 0x00:
                    print("App claims source was %i, but it must be 0x00" % packet_src)
                    self.clear()
                else:
                    self.packet_idx = 4
            elif self.packet_idx == 4:
                packet_dest = byte
                if packet_dest != 0x00 and packet_dest != 0xFF:
                    print("App claims destination was %i, but it must be either 0x00 or 0xFF" % packet_dest)
                    self.clear()
                else:
                    self.packet_idx = 5
            elif self.packet_idx < self.packet_size:
                self.data.append(byte)
                self.packet_idx += 1
            elif self.packet_idx == self.packet_size:
                checksum = Robot.calc_checksum(self.buffer[:-1])
                if checksum != byte:
                    print("Checksum was %i, but it should be %i" % (byte, checksum))
                # now we're done reading the packet
                temp_type = self.packet_type
                temp_data = self.data
                self.clear()
                return temp_type, temp_data

        return None, None

    def clear(self):
        self.packet_idx = 0
        self.packet_size = 0
        self.data = []
        self.buffer = []

if __name__ == '__main__':
    r = Robot()
