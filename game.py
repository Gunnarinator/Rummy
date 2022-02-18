def connection(sock):
    while True:
        data = sock.receive()
        sock.send(data)
