#!/usr/bin/python3
from config import COUNTRIES, TRAFFMON_DEBUG

DEBUG = TRAFFMON_DEBUG

import time
import datetime
import nfsenutils
from pprint import pprint
import json


if not DEBUG:
	from influxdb import InfluxDBClient

# For some reason now most of supicious traffic in r0.f1k12 moved from
# as 0 to as 3549. Bolivia still only shows AS 0. We are adding this
# to also check for results in AS 3549
# We could also fix this by simply adding 3549 to the as 0 fix filer
# (or src as 3549). But we will keep this in order to monitor its behaviour.
# IMPORTANT: this increased taken time from 54/80 seconds to 150/140 seconds.
# Maybe we could also add the 'bad traffic' to the DB. Not doing it for now.	
BAD_AS_LIST = ["0", "3549"]


AS_RANGE_FILTERS = {}


def round_time(dt=None, round_to=60):
	if dt == None: 
		dt = datetime.datetime.now()
	seconds = (dt - dt.min).seconds
	rounding = (seconds+round_to/2) // round_to * round_to
	return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)


def search_nfsen_entry(nfsen_entries, match):
	for entry in nfsen_entries:
		if entry[nfsenutils.STAT_CRITERIA] == str(match):
			return entry


def intialize_influx():
	if DEBUG:
		return

	return InfluxDBClient(host='localhost', port=8086)


def to_influx(db, time, customer_data, country=None):
	if DEBUG:
		print("INFLUXING>>>>>>>>>>")
	points = []
	for measurement, measurement_data in customer_data["resource_usage"].items():
		point = {
				 "time": time,
				 "measurement": measurement,
				 "tags": {
				 	"customer": customer_data["name"],
				 	"country": country
				 },
				 "fields": {}
		        }
		for field, field_value in customer_data["resource_usage"][measurement].items():
			point["fields"][field] = field_value

		points.append(point)
	if DEBUG:
		print(points)
	
	#points = json.dumps(points)
	
	if not DEBUG:
		db.write_points(points, database="traffic" ,time_precision="s")


def load_as_range_filters():
	global AS_RANGE_FILTERS

	try:
		with open("as_range_filters") as f:
			AS_RANGE_FILTERS = json.loads(f.read())
	except (FileNotFoundError, json.JSONDecodeError):
		AS_RANGE_FILTERS = {}


def as_0_fix(nfsen, query, timestamp, as_resource, bad_as_list):
	as_num = as_resource["match"]
	if DEBUG:
		print("AS 0 FIX %s AS %s<----------------" % (as_resource["name"], as_num))
	as_range_filter = AS_RANGE_FILTERS.get(as_num,[])
	if not as_range_filter:
		return 0
	as_usage = 0
	for bad_as in bad_as_list:
		for range_filter in as_range_filter.get("filters",[]):
			range_query = dict(query)
			range_query["filter"] = f"({query['filter']}) and src as {bad_as} and ({range_filter})"

			if len(range_query["filter"]) > 10240:
				print("ERROR: FILTER TOO BIG. %s length." % len(range_query["filter"]))
				raise

			nfsen_output = nfsen.query(range_query, timestamp)
			if DEBUG:
				print(nfsen_output)

			nfsen_dump = nfsenutils.get_sdump_entries(nfsen_output)

			evaluated_entry = search_nfsen_entry(nfsen_dump, bad_as)

			if evaluated_entry is not None:
				resource_raw = int(round(nfsenutils.traff_to_val(evaluated_entry[nfsenutils.BPS]), 0))
			# TODO: It should probably be a good idea to check if is too low or too wild and adjust.
			else:
				resource_raw = 0

			as_usage += resource_raw

		print("AS 0 CUMULATED AS %s USAGE: %s------------>" % (bad_as, as_usage))
	if DEBUG:
		print("AS 0 USAGE: %s------------>" % as_usage)
	return as_usage


def peru_analyzer(timestamp):
	load_as_range_filters()

	db = intialize_influx()

	nfsen = nfsenutils.NFSENServer("https://nfsen.us.iptp.net")
	nfsen.login()

	# if earlier then 23 hours ago...
	if timestamp < time.time() - 23 * 60 * 60:
		nfsen.set_window_size(3)  # 4 days. This is as back as nfsen alow us to go. November 2020

	report = []

	for country in COUNTRIES:
		if DEBUG:
			print("---------------COUNTRY: %s-------------" % country["name"])
		country_data = {"name": country["name"], "customers": [], "extra_resources": []}

		for customer in country["customers"]:
			if DEBUG:
				print("***************** CUSTOMER: %s ***********************" % customer["name"])

			customer_data = {"name": customer["name"], "resource_usage": {}}
			for resource_type, resource_info in customer["resources"].items()	:
				if DEBUG:
					print("================= Reource: %s ***********************" % resource_type)


				customer_data["resource_usage"][resource_type] = {}

				query = dict(resource_info["query"])
				query["srcselector[]"] = country["router"]

				nfsen_output = nfsen.query(query, timestamp)
				
				if DEBUG:
					print(nfsen_output)
				
				nfsen_dump = nfsenutils.get_sdump_entries(nfsen_output)

				bad_as_list = []
				if "as" in resource_type:
					for bad_as in BAD_AS_LIST:
						as_entry = search_nfsen_entry(nfsen_dump, bad_as)
						if as_entry:
							bad_as_list.append(bad_as)

				if DEBUG:
					print(country["resources"][resource_type])
				for resource in country["resources"][resource_type]:
					evaluated_entry = search_nfsen_entry(nfsen_dump, resource["match"])

					if evaluated_entry is not None:
						resource_raw = int(round(nfsenutils.traff_to_val(evaluated_entry[nfsenutils.BPS]),0))
					else:
						resource_raw = 0

					if "as" in resource_type and bad_as_list:
						as_0_usage = as_0_fix(nfsen, query, timestamp, resource, bad_as_list)
						resource_raw += as_0_usage

					if DEBUG:
						print(customer_data)
					
					customer_data["resource_usage"][resource_type][resource["name"]] = resource_raw


			country_data["customers"].append(customer_data)
			to_influx(db, int(timestamp), customer_data, country["name"])

		for extra_resource in country.get("extra_resources", []):
			if DEBUG:
				print("***************** EXTRA RESOURCE: %s ***********************" % extra_resource["name"])

			#customer_data = {"name": extra_resource["name"], "resource_usage": {}}

			resource_type = extra_resource["resource_type"]

			#customer_data["resource_usage"][resource_type] = {}

			query = dict(extra_resource["query"])
			query["srcselector[]"] = country["router"]

			nfsen_output = nfsen.query(query, timestamp)

			if DEBUG:
				print(nfsen_output)

			nfsen_dump = nfsenutils.get_sdump_entries(nfsen_output)

			for customer in country["customers"]:
				evaluated_entry = search_nfsen_entry(nfsen_dump, customer["interface"])

				if evaluated_entry is not None:
					resource_raw = int(round(nfsenutils.traff_to_val(evaluated_entry[nfsenutils.BPS]), 0))
				else:
					resource_raw = 0

				#customer_data["resource_usage"][resource_type][customer["name"]] = resource_raw

				customer_data = {"name": customer["name"],
								 "resource_usage": {extra_resource["resource_type"]: {extra_resource["name"]: resource_raw}}}

				if DEBUG:
					print(customer_data)

				to_influx(db, int(timestamp), customer_data, country["name"])
				country_data["extra_resources"].append(customer_data)

		report.append(country_data)

	if DEBUG:
		pprint(report)


if __name__ == "__main__":
	import sys
	#1585018800
	start = time.time()

	if sys.argv[1:]:
		peru_analyzer(*sys.argv[1:])
	else:
		peru_analyzer(time.time())

	total_time = time.time() - start

	if DEBUG:
		print("TOTAL TIME: %s" % total_time)

	if total_time >= 5 * 60:
		print("TIME WARNING: Taken time 5 minutes. SHOULD OPTMIZE SCRIPT")
	elif total_time > 4 * 60:
		print("TIME LOW WARNING: Taken time 4 minutes.")
