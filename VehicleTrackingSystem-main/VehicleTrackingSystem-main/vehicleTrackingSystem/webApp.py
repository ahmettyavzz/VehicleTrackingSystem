from distutils.log import debug
from socket import socket
from MySQLdb.cursors import Cursor
from flask import Flask, config, render_template, flash, redirect, url_for, session, logging, request, render_template
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_socketio import SocketIO
from datetime import datetime
import pymongo

#GİRİŞ EKRANI İÇİN FORM
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")

#HARİTA EKRANI İÇİN FORM
class MapForm(Form):
    carId = StringField("Araç No")
    entryDate = StringField("Başlangıç Tarihi")
    exitDate = StringField("Bitiş Tarihi")

app = Flask(__name__)
app.secret_key = "yazlab1"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "users"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

#socketio
socket = SocketIO(app)

#MONGO DB BAĞLANTI
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["yazlab"]
collection = db["yazlab"]

findAll = collection.find()

tarih = []
x = []
y = []
arabaNo = []

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@socket.on('message')
def handlemsg(msg):
    for row in findAll:
        tarih.append(row["Tarih"])
        arabaNo.append(row["CarId"])

    veri = [x, y]
    socket.send(veri)    


#HARİTA EKRANI
@app.route("/map", methods=["GET", "POST"])
def map():
    form = MapForm(request.form)
    if request.method == "POST":
        carId = form.carId.data
        entryDate = form.entryDate.data
        exitDate = form.exitDate.data

        carId = int(carId)
        entryDate = entryDate[2:len(entryDate)]
        exitDate = exitDate[2:len(exitDate)]

        entryDate = datetime.strptime(entryDate, "%y-%m-%d %H:%M:%S") 
        exitDate = datetime.strptime(exitDate, "%y-%m-%d %H:%M:%S")

        x.clear()
        y.clear()

        if session["id"] == 1:
            if carId == 1 or carId == 2:
                findAll = collection.find({"CarId": carId, "Tarih": { "$gt": entryDate, "$lt": exitDate} })

                for row in findAll:
                    x.append(row["X"])
                    y.append(row["Y"])
        
        if session["id"] == 2:
            if carId == 6 or carId == 8:
                findAll = collection.find({"CarId": carId, "Tarih": { "$gt": entryDate, "$lt": exitDate} })

                for row in findAll:
                    x.append(row["X"])
                    y.append(row["Y"])

    else: 
        findAll = collection.find({"Tarih": { "$gt": datetime.strptime("18-10-02 14:06:00", "%y-%m-%d %H:%M:%S") , "$lt": datetime.strptime("18-10-02 14:36:00", "%y-%m-%d %H:%M:%S")}})
        x.clear()
        y.clear()
        for row in findAll:
            x.append(row["X"])
            y.append(row["Y"])

    return render_template("map2.html", form = form)

control = 0
#GİRİŞ EKRANI
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "select * from info where UserName=%s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["Password"]
            id = data["Id"]

            if (password_entered == real_password):
                flash("Hoşgeldiniz", "success")
                e = datetime.now()
                session["logged_in"] = True
                session["username"] = username
                session["id"] = id

                sorgu2 = "update info set EntryTime=%s where id=%s"
                cursor = mysql.connection.cursor()
                cursor.execute(sorgu2, (e, id))
                mysql.connection.commit()

                return redirect(url_for("index"))
            
            else:
                global control
                control+=1
                print(control)
                if (control < 3):
                    flash("Parola yanlış", "danger")
                else:
                    flash("Parolayı " +  str(control) + " kere yanlış girdiniz", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor", "danger")
            return redirect(url_for("login"))
        

    return render_template("login.html", form = form)

#ÇIKIŞ
@app.route("/logout")
def logout():
    e = datetime.now()

    sorgu = "update info set ExitTime=%s where id=%s"
    cursor = mysql.connection.cursor()
    cursor.execute(sorgu, (e, session["id"]))
    mysql.connection.commit()
    session.clear()

    return redirect(url_for("index"))

if __name__ == "__main__":
    socket.run(app, host='localhost', debug=True)
