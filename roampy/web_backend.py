from flask import Flask, request, jsonify
import Queue
import json

app = Flask(__name__)
q = Queue.Queue(100)
last = 0
alarm_queue = 0

@app.route('/', methods=["GET", "POST"])
def poster():
	if request.method == "POST":
		try:
			global last
			data = request.json["content"]
			last = data
			print "Got data: {}.".format(data)
		except:
			print "Bad data."
	return "OK"

@app.route('/alarm/', methods=["GET", "POST"])
def alarm():
	global alarm_queue

	if request.method == "POST":
		alarm_queue = 1
		print "ALARM ON"
		return "OK"

	return_alarm = alarm_queue
	alarm_queue = 0
	return str(return_alarm)

@app.route('/last/')
def get_last():
	global last
	return str(last)

if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
