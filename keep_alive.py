from flask import Flask
from threading import Thread
import random

app = Flask(__name__)


@app.route("/")
def home():
  return "Бот снова работает!"


def run():
  app.run(host="0.0.0.0", port=random.randint(2000, 9000))


def keep_alive():
  t = Thread(target=run)
  t.start()
