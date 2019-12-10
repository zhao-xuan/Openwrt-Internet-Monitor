from flask import Flask, escape, request, render_template
import sqlite3
import csv
import requests
import time
import datetime
import json

app = Flask(__name__, static_url_path='/static')

url = 'http://192.168.1.1/cgi-bin/luci/admin/nlbw/data?type=csv&group_by=mac&order_by=-rx,-tx'
login_cred = {'luci_username': 'root', 'luci_password': '59fa5JpTTbknQu6'}

#cookies = dict(sysauth='83063fd9dd72bf35ff40c6a6231aa39e')
host_stats_by_interval = []
prev_host_stats = []
host_mac_address = []
db_conn = sqlite3.connect('database.db', check_same_thread = False)
db_cursor = db_conn.cursor()
db_cursor.execute('CREATE TABLE IF NOT EXISTS "archived_stats" ("id" integer primary key autoincrement,"device_id" integer,"download" integer,"upload" integer,"timestamp" integer)')
db_cursor.execute('CREATE TABLE IF NOT EXISTS "stats" ("id" integer primary key autoincrement, "device_id" integer, "download" integer, "upload" integer, "timestamp" integer)')
db_cursor.execute('CREATE TABLE IF NOT EXISTS "devices" ("id" integer primary key autoincrement, "mac" text, "name" text)')

def get_stats():
	global prev_host_stats
	
	host_stats = []
	try:
		with requests.Session() as s:
			p = s.post(url, data = login_cred)
			r = s.get(url)
			
			if not r.text.startswith('"mac"'):
				raise Exception("Unexpected response from server (bad username/password?)")
			
			reader = csv.reader(r.text.split('\n'), delimiter=';', quotechar='"')
			
			for row in reader:
				if len(row) == 0 or row[0] == "mac" :
					continue
				host_stats.append({
					"mac" : row[0],
					"download" : int(row[2]),
					"upload" : int(row[4])
				})
				
				if db_cursor.execute("SELECT id FROM devices WHERE mac=?", (row[0],)).fetchall() == []:
					db_cursor.execute("INSERT INTO devices (mac, name) VALUES (?, ?)", (row[0], row[0]))
			

			if prev_host_stats != []:
				temp = []
				timestamp = time.time()
				for i in range(0, len(host_stats)):
					temp.append({
						"mac" : host_stats[i]["mac"],
						"d_download" : host_stats[i]["download"] - prev_host_stats[i]["download"],
						"d_upload" : host_stats[i]["upload"] - prev_host_stats[i]["upload"]
					})
					device_id = db_cursor.execute("SELECT id FROM devices WHERE mac = ?", (host_stats[i]["mac"],)).fetchall()[0][0]
					db_cursor.execute('''INSERT INTO stats (device_id, download, upload, timestamp)
					                   	 VALUES (?, ?, ?, ?)''', (device_id, temp[i]['d_download'], temp[i]['d_upload'], timestamp))
					db_conn.commit()

					hour = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')[11:13]
					minute = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')[14:16]
					if minute == "00" or minute == "30":
						hr_sum = db_cursor.execute('''SELECT sum(download) as download, sum(upload) as upload
													FROM stats
													WHERE timestamp > ?
													GROUP BY device_id''', (int(timestamp) - 3600,)).fetchall()
						db_cursor.execute('''INSERT INTO archived_stats (device_id, download, upload, timestamp)
					                   	 VALUES (?, ?, ?, ?)''', (device_id, hr_sum[i][0], hr_sum[i][1], timestamp))
						print("***Archived one set of data!!***")
						db_conn.commit()
			
			prev_host_stats = host_stats.copy()
			
			print("***Got one set of data!***")
	except Exception as e:
		print(e)

@app.route('/devices')
def get_devices():
	devices = db_cursor.execute("SELECT id, mac, name FROM devices").fetchall()
	devices_dict = []

	for i in devices:
		devices_dict.append({
			"id": i[0],
			"mac": i[1],
			"name": i[2]
		})
	
	return {"devices" : devices_dict}


@app.route('/')
def send_static_html():
	return app.send_static_file('index.html')

@app.route('/app.css')
def send_static_css():
	return app.send_static_file('app.css')

@app.route('/app.js')
def send_static_js():
	return app.send_static_file('app.js')
	
@app.route('/rename', methods = ['POST'])
def rename_device():
	device_id = request.form.get("device_id")
	newname = request.form.get("newname")
	db_cursor.execute('''UPDATE devices
						 SET name = ?
						 WHERE id = ?''', (newname, device_id))
	db_conn.commit()
	return ''

@app.route('/viewSince')
def get_info():
	view_since = request.args.get("view_since")
	device_id = request.args.get("device_id")
	interval_by = request.args.get("interval_by")
	stats = db_cursor.execute('''SELECT id, device_id, sum(download) as download, sum(upload) as upload, timestamp
	                           FROM stats 
							   WHERE timestamp > ? AND device_id = ?
							   GROUP BY CAST(timestamp / ? as int)''', (time.time() - float(view_since), device_id, interval_by)).fetchall()
	stats_dict = []
	
	for i in stats:
		stats_dict.append({
			#"id": i[0],
			"device_id": i[1],
			"download": i[2],
			"upload": i[3],
			"timestamp": i[4]
		})

	return {
		"stats" : stats_dict,
	}

@app.route('/needArchive')
def checkIfNeedArchive():
	device_id = request.args.get('device_id')
	by_year = request.args.get('by_year')
	by_month = request.args.get('by_month')
	by_date = request.args.get('by_date')

	if by_year == -1:
		archived_stats = db_cursor.execute('''SELECT sum(download), sum(upload), strftime("%Y"), datetime(timestamp, 'unixepoch')) as t
											FROM archived_stats
											WHERE device_id = ?
											GROUP BY t''', (device_id,)).fetchall()
	elif by_month == -1:
		archived_stats = db_cursor.execute('''SELECT sum(download), sum(upload), strftime("%m"), datetime(timestamp, 'unixepoch')) as t
											FROM archived_stats
											WHERE device_id = ? AND strftime("%Y"), datetime(timestamp, 'unixepoch')) = ?
											GROUP BY t''', (device_id,by_year)).fetchall()
	elif by_date == -1:
		archived_stats = db_cursor.execute('''SELECT sum(download), sum(upload), strftime("%d"), datetime(timestamp, 'unixepoch')) as t
											FROM archived_stats
											WHERE device_id = ? AND strftime("%Y%m"), datetime(timestamp, 'unixepoch')) = ? 
											GROUP BY t''', (device_id, str(by_year) + str(by_month))).fetchall()
	else:
		archived_stats = db_cursor.execute('''SELECT sum(download), sum(upload), timestamp
											FROM archived_stats
											WHERE device_id = ? AND strftime("%Y%m%d"), datetime(timestamp, 'unixepoch')) = ?''', (device_id, str(by_year) + str(by_month) + str(by_date))).fetchall()
	
	archived_dict = []
	for i in archived_stats:
		archived_dict.append({
			"download": i[0],
			"upload": i[1],
			"t": i[2]
		})
	
	return {
		"archived_dict" : archived_dict
	}

if __name__ == '__main__':
	app.run(debug = True, host="0.0.0.0")