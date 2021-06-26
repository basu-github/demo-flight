#!/usr/bin/env python
 
from threading import Lock
from flask import Flask, render_template, session, request, copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect
import sqlite3
import logging
import logging.handlers
import time

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
LOGGER = logging.getLogger()



# create sqlite3 DB

def create_db():
    '''
    create database
    '''
    global dbname
    dbname = "database.db"
    conn = sqlite3.connect(dbname)
    LOGGER.info("Opened database successfully")

    conn.execute('CREATE TABLE if not exists bookingstatus (ID INTEGER PRIMARY KEY autoincrement,\
                  JOBNAME TEXT, SEATID INT,STARTTIME TEXT, ENDTIME TEXT,\
                  USERNAME TEXT)')
    #conn.execute('ALTER TABLE bookingstatus ADD REPORTSTATUS TEXT')
    LOGGER.info("Table created successfully")
    conn.close()

# updating the table

def insert_values_db(project, seatid, status, time, username):
    '''
    insert values into db
    '''
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO bookingstatus (JOBNAME, SEATID, STARTTIME, ENDTIME,\
                     USERNAME, REPORTSTATUS) VALUES (?,?,?,?,?,?)"\
                     , (project, seatid, status, time, 'None',username))
        con.commit()
        msg = "Record successfully added"
        cur.execute("SELECT * from bookingstatus")


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1 
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * from bookingstatus")
        conn.commit()
        result = cur.fetchall()
    num_seats = result[-1][2]
    session['seat'] = session.get('seat', num_seats)
    emit('my_response',
         {'data': session['seat'], 'count': session['receive_count']})



@socketio.event
def my_book(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * from bookingstatus")
        conn.commit()
        result = cur.fetchall()
    num_seats = result[-1][2]
    with sqlite3.connect("database.db") as conn:
      cur = conn.cursor()
      cur.execute("UPDATE bookingstatus set SEATID = %i -1"%num_seats)
      cur.execute("SELECT * from bookingstatus")
      conn.commit()
      result = cur.fetchall()
    num_seats = result[-1][2]
    session['seat'] = session.get('seat', num_seats) - 1
    emit('my_response',
         {'data': session['seat'], 'count': session['receive_count']})



@socketio.event
def my_ping():
    emit('my_pong')


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    create_db()
    time.sleep(2)
    insert_values_db('flight', 60,"dummy", time.ctime(), 'basu')
    socketio.run(app, host='0.0.0.0',port=80)
