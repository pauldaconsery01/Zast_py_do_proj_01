import sqlite3
import os
import threading
from flask import Flask, render_template, request, send_file
from pyngrok import ngrok
import numpy as np
import pickle
from PIL import Image
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import base64
import urllib.parse

# Token autoryzacyjny do podmiany przez uzytkownika
# ngrok.set_auth_token("2PvGYS2MXO9I1PVsPmb17yA3Jtq_7fDbkruASEHVXiGmxPp86")
ngrok.set_auth_token("2QFwbed6PaudUiDh4zeTGgYgMRl_b1Y8gT9ZtqmbsZB2hmZV")

os.environ["FLASK_DEBUG"] = "development"
app = Flask(__name__)
port = 5000

public_url = ngrok.connect(port).public_url
print(" * public url \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

app.config["BASE_URL"] = public_url


@app.route("/")
@app.route('/home')
def index():
    return render_template("index.html")


# Utworzenie bazy danych
connect = sqlite3.connect('database.db')
connect.execute(
    'CREATE TABLE IF NOT EXISTS PARTICIPANTS (name TEXT, \
    email TEXT,  country TEXT,  review TEXT, note TEXT)')

# Wpisanie inicjalne do bazy przykładowych recenzji
n_obs = connect.execute("SELECT EXISTS (SELECT 1 FROM PARTICIPANTS);").fetchall()[0][0]
if n_obs == 0:
    intro_data = [("John", "john@gmail.com", "UK", "Poor service, rude waiters, long awaiting time.", "1 - Terrible"),
                  ("Johny", "john1@gmail.com", "USA",
                   "Very good quality of service, proper communication, elegant serving.", "4 - Wonderful"),
                  ("Jan", "john2@gmail.com", "PL", "Poor service, rude waiters, long awaiting time.", "3 - Decent"),
                  ("Johannes", "john23@gmail.com", "DE", "Poor service, rude waiters, long awaiting time.",
                   "1 - Terrible"),
                  ("Jan", "john3@gmail.com", "PL", "Calming music and polite staff, elegant.", "3 - Decent")
                  ]

    connect.executemany("INSERT INTO PARTICIPANTS VALUES(?, ?, ?, ?, ?)", intro_data)
    connect.commit()


# Wpisanie do bazy danych wartosci dodanych w ankiecie
@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        country = request.form['country']

        review = request.form['review']
        note = request.form['note']

        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO PARTICIPANTS \
            (name,email,country, review, note) VALUES (?,?,?,?,?)",
                           (name, email, country, review, note))
            users.commit()

        return render_template("index.html")
    else:
        return render_template('join.html')


# Wyświetlenie rececnji z bazy danych
@app.route('/participants')
def participants():
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    # cursor.execute('SELECT * FROM PARTICIPANTS')
    cursor.execute('SELECT name, country, review, note FROM PARTICIPANTS')

    data = cursor.fetchall()
    connect.close()
    return render_template("participants.html", data=data)


# Wygenerowanie chmury wyrazów:
@app.route('/wordcloud', methods=["POST", "GET"])
def wordcloud():
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()

    texts = []
    for row in cursor.execute('SELECT REVIEW FROM PARTICIPANTS'):
        texts.append(row[0])

    connect.close()
    text = ''
    # tokenizacja recencji i sprowadzenie do małej litery
    for element in texts:

        element = str(element)

        tokens = element.split()

        for i in range(len(tokens)):
            tokens[i] = tokens[i].lower()

        text += " ".join(tokens) + " "

    count = 20
    width = 500
    height = 500
    minfontsize = 4
    maxfontsize = 150

    stopwords = set(STOPWORDS)

    wc = WordCloud(background_color="black",
                   max_words=count,
                   collocations=False,
                   width=width,
                   min_font_size=minfontsize,
                   max_font_size=maxfontsize,
                   height=height,
                   stopwords=stopwords)

    wordcloud = wc.generate(str(text))
    wordcloudImage = wordcloud.to_image()

    buffer = BytesIO()
    wordcloudImage.save(buffer, format="png")
    buffer.seek(0)
    image_memory = base64.b64encode(buffer.getvalue())

    return render_template("wordcloud.html", img_data=image_memory.decode('utf-8'))


threading.Thread(target=app.run, kwargs={"use_reloader": False}).start()