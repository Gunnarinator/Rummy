from flask import Flask, send_from_directory
from flask_sock import Sock

import game

app = Flask(__name__)
sock = Sock(app)

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
async def public(path):
    return send_from_directory("public", path)

@sock.route('/stream')
def socket(sock):
    game.connection(sock)

if __name__ == '__main__':
    app.debug = True
    app.run(port="8080")

