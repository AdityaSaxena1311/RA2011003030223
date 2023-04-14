from flask import Flask, jsonify, request
import requests
import datetime
import time
import os
import psycopg2
app = Flask(__name__)
API_KEY = "YOUR_API_KEY"
JD_RAILWAY_API = "https://api.johndoe.com/trains"
MAX_DELAY = 30 * 60 
ALLOWED_WINDOW = 2 * 60 * 60
DB_HOST = "localhost"
DB_NAME = "train_schedule_db"
DB_USER = "admin"
DB_PASSWORD = "password"
db = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = db.cursor()
@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    return jsonify({"token": "YOUR_AUTH_TOKEN"})
@app.route('/trains/schedule', methods=['GET'])
def trains_schedule():
    auth_token = request.headers.get('Authorization')
    if not auth_token:
        return jsonify({"error": "Unauthorized"}), 401
    response = requests.get(f"{JD_RAILWAY_API}?apikey={API_KEY}")
    if response.status_code != 200:
        return jsonify({"error": "Unable to get train schedule"}), 500
    trains = response.json()
    current_time = int(time.time())
    valid_trains = []
    for train in trains:
        departure_time = datetime.datetime.strptime(train['departure_time'], '%Y-%m-%d %H:%M:%S')
        departure_timestamp = int((departure_time - datetime.datetime(1970,1,1)).total_seconds())
        delay = int(train['delay'])
        if departure_timestamp + delay > current_time + MAX_DELAY and departure_timestamp + delay < current_time + ALLOWED_WINDOW:
            valid_trains.append(train)
    for train in valid_trains:
        train_id = train['train_id']
        response = requests.get(f"{JD_RAILWAY_API}/{train_id}?apikey={API_KEY}")
        if response.status_code == 200:
            data = response.json()
            sleeper_availability = data['sleeper_availability']
            ac_availability = data['ac_availability']
            sleeper_price = data['sleeper_price']
            ac_price = data['ac_price']
            cursor.execute("INSERT INTO train_coach (train_id, coach_type, seat_availability, price) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)",
                           (train_id, 'sleeper', sleeper_availability, sleeper_price, train_id, 'ac', ac_availability, ac_price))
    cursor.execute("SELECT train.train_id, train.train_name, train.departure_time, train.arrival_time, "
                   "SUM(train_coach.seat_availability) AS total_seats, "
                   "MIN(train_coach.price) AS min_price "
                   "FROM train JOIN train_coach ON train.train_id = train_coach.train_id "
                   "WHERE train_coach.seat_availability > 0 "
                   "GROUP BY train.train_id "
                   "ORDER BY min_price ASC, total_seats DESC, departure_time DESC")
    results = cursor.fetchall()
    train_schedule = []
    for row in results:
        train_id, train_name, departure_time, arrival_time, total_seats, min_price = row
        train_schedule.append({
            "train_id": train_id,
            "train_name": train_name,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "total_seats": total_seats,
            "min_price": min_price
        })
    return jsonify(train_schedule), 200
app.run(debug=True)

