from flask import Flask, redirect, render_template, send_file

import os

from waitress import serve # для запуска сервера


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jprB?VYVYOn4_6qm$kEsDo@pB5[_0E^gD%zC'

APP_URL = 'http://127.0.0.1:5000'

@app.route('/')
@app.route('/index')
def main():
    return 'hello world'

if __name__ == '__main__':
    #db_session.global_init("db/data.db")
    print(f'server is running {APP_URL}')
    serve(app, port=os.environ.get("PORT", 5000), host='0.0.0.0')
