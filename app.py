from flask import Flask, send_from_directory
from flask_sock import Server, Sock

import lobby

app = Flask(__name__)
sock = Sock(app)


@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def public(path):
    return send_from_directory("public", path)


@sock.route('/stream')
def socket(sock: Server):
    lobby.addConnection(sock)


if __name__ == '__main__':
    app.debug = True
