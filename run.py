from flask import Flask
from routes import main
from handler import errors
import os

App = Flask(__name__)
App.register_blueprint(main)
App.register_blueprint(errors)

try:
    SERVER_PORT = os.getConfig('SERVER_PORT')
    if len(SERVER_PORT) == 0:
        raise KeyError
except:
    SERVER_PORT = 80

if __name__ == '__main__':
	App.run(debug=True, host='0.0.0.0', port=SERVER_PORT)