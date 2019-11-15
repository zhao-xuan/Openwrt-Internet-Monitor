from flask import Flask, escape, request
import sqlite3
import csv
import requests
import time
import json

app = Flask(__name__)

url = 'http://192.168.1.1/cgi-bin/luci/admin/nlbw/data?type=csv&group_by=mac&order_by=-rx,-tx'
cookies = dict(sysauth='2e4b73938d45e6ec2ad930b46cb9d4d8')
host_stats_by_interval = []
prev_host_stats = []
db_conn = sqlite3.connect('example.db', check_same_thread = False)
db_cursor = db_conn.cursor()
#create table stats (mac text, download integer, upload integer)


def get_stats():
	global prev_host_stats
	host_stats = []
	
	r = requests.get(url, cookies = cookies)
	reader = csv.reader(r.text.split('\n'), delimiter=';', quotechar='"')
	for row in reader:
		if len(row) == 0 or row[0] == "mac" :
			continue
		host_stats.append({
			"mac" : row[0],
			"download" : int(row[2]),
			"upload" : int(row[4])
		})
	if prev_host_stats != []:
		temp = []
		timestamp = time.time()
		for i in range(0, len(host_stats)):
			temp.append({
				"mac" : host_stats[i]["mac"],
				"d_download" : host_stats[i]["download"] - prev_host_stats[i]["download"],
				"d_upload" : host_stats[i]["upload"] - prev_host_stats[i]["upload"]
			})
			db_cursor.execute("INSERT INTO stats VALUES (?, ?, ?, ?)", (temp[i]['mac'], temp[i]['d_download'], temp[i]['d_upload'], timestamp))
		db_conn.commit()
	
	prev_host_stats = host_stats.copy()
	
	print(host_stats_by_interval)

@app.route('/')
def get_info():
	jsonList = json.dumps(db_cursor.execute("SELECT * FROM stats").fetchall())
	return jsonList