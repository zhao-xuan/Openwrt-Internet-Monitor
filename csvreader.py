from flask import Flask, escape, request, render_template
import sqlite3
import csv
import requests
import time
import json

app = Flask(__name__, static_url_path='/static')

url = 'http://192.168.1.1/cgi-bin/luci/admin/nlbw/data?type=csv&group_by=mac&order_by=-rx,-tx'
login_cred = {'luci_username': 'root', 'luci_password': '59fa5JpTTbknQu6'}

cookies = dict(sysauth='83063fd9dd72bf35ff40c6a6231aa39e')
host_stats_by_interval = []
prev_host_stats = []
host_mac_address = []
db_conn = sqlite3.connect('example.db', check_same_thread = False)
db_cursor = db_conn.cursor()
#create table stats (mac text, download integer, upload integer)

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
					device_id = db_cursor.execute("SELECT id FROM devices WHERE mac=?", (host_stats[i]["mac"],)).fetchall()[0][0]
					db_cursor.execute("INSERT INTO stats (device_id, download, upload, timestamp) VALUES (?, ?, ?, ?)", (device_id, temp[i]['d_download'], temp[i]['d_upload'], timestamp))
				db_conn.commit()
			
			prev_host_stats = host_stats.copy()
			
			print("***Got one set of data!***")
	except Exception as e:
		print(e)

@app.route('/getdata')
def get_info1():
	stats = db_cursor.execute("SELECT id, device_id, download, upload, timestamp FROM stats").fetchall()
	devices = db_cursor.execute("SELECT id, mac, name FROM devices").fetchall()

	stats_dict = []
	devices_dict = []
	
	for i in stats:
		stats_dict.append({
			"id": i[0],
			"device_id": i[1],
			"download": i[2],
			"upload": i[3],
			"timestamp": i[4]
		})
	
	for i in devices:
		devices_dict.append({
			"id": i[0],
			"mac": i[1],
			"name": i[2]
		})
	return {
		"stats" : stats_dict,
		"devices" : devices_dict
	}


@app.route('/')
def send_static():
	return app.send_static_file('index.html')

@app.route('/app.css')
def send_static_css():
	return app.send_static_file('app.css')
	
@app.route('/rename', methods = ['POST'])
def rename_device():
	device_id = request.form.get("device_id")
	newname = request.form.get("newname")
	db_cursor.execute("UPDATE devices SET name = ? WHERE id = ?", (newname, device_id))
	db_conn.commit()
	return ''
	
if __name__ == '__main__':
	app.run(debug = True)