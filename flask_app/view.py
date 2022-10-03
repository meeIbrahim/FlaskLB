from flask import Flask
from flask import render_template
import socket
import os


app = Flask(__name__)

hostname = socket.gethostname()
Username = "Muhammad Ibrahim"

@app.route('/')
def hello():
    return render_template('mainpage.html',hostname=hostname,username=Username)


if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000))
    app.run(debug=True,host='0.0.0.0',port=port)