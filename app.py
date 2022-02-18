from flask import Flask, send_file
from flask_sock import Sock

import game

app = Flask(__name__)
sock = Sock(app)

@app.route("/")
async def index():
    return send_file("public/index.html")

@sock.route('/stream')
def socket(sock):
    game.connection(sock)

if __name__ == '__main__':
    app.debug = True
    app.run(port="8080")

