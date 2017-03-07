import bluetooth
from time import sleep, time


def main():
    port = 1
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(1)

    while True:
        print("waiting for robot")
        client_sock, address = server_sock.accept()
        print("Accepted connection from ", address)

        last_heartbeat_time = time()
        while True:
            now = time()

            try:
                if now - last_heartbeat_time > 1.5:
                    last_heartbeat_time = now
                    heartbeat = bytes([0x5f, 0x05, 0x07, 0x0C, 0x00, 0xE7])
                    print("Sending: ", heartbeat)
                    client_sock.send(heartbeat)

                data = client_sock.recv(1024)
                print("Received: ", data)
                sleep(0.1)
            except bluetooth.btcommon.BluetoothError:
                break


if __name__ == '__main__':
    main()