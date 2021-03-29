from config import COUNTRIES, AS_EXPLORER_DEBUG

DEBUG = AS_EXPLORER_DEBUG

import nfsenutils
import whoip
import time
from pprint import pprint
import ipaddress
import json
import requests
import copy

if not DEBUG:
	from influxdb import InfluxDBClient


BAD_AS_LIST = ["0", "3549"]

CACHE = "network_cache"
AS_CACHE = "as_cache"

AS_QUERY_CACHE = {}

ASN_QUERY = """
query {
        asn(asn:"%s") {
            asn
            asnName
            organization {
                orgName
            }
            country {
                name
            }
        }
}
"""

def intialize_influx():
        if DEBUG:
                return

        return InfluxDBClient(host='localhost', port=8086)


def _get_AS_country_info(asn):
    if asn in AS_QUERY_CACHE:
        as_info = AS_QUERY_CACHE[asn]
    else:
        req = requests.post("https://api.asrank.caida.org/v2/graphql", 
                            data=json.dumps({"query": ASN_QUERY % asn}),
                            headers={'content-type': 'application/json'})
        as_info = json.loads(req.text)
        
        AS_QUERY_CACHE[asn] = as_info

    return as_info


def get_AS_name(asn):
    as_info = _get_AS_country_info(asn)

    #print(as_info)
    
    if as_info["data"]["asn"] is not None:
        if as_info["data"]["asn"]["asnName"]:
            return as_info["data"]["asn"]["asnName"]
        elif as_info["data"]["asn"]["organization"]:
        	return as_info["data"]["asn"]["organization"]["orgName"]
    # try second source?
    return "NO_INFO"


def load_cache():
	try:
		cache_f = open(CACHE)
		cache = json.loads(cache_f.read())
		cache_f.close()
	except (json.JSONDecodeError, FileNotFoundError):
		cache = {"time": 0, "networks": []}

	networks_cache = cache.get("networks")

	networks = []

	for network_cache in networks_cache:
		networks.append({"network": ipaddress.ip_network(network_cache["network"]),
						 "as_num": network_cache["as_num"]})
	
	return networks


def load_as_cache():
	try:
		cache_f = open(AS_CACHE)
		cache = json.loads(cache_f.read())
		cache_f.close()
	except (json.JSONDecodeError, FileNotFoundError):
		cache = {}

	global AS_QUERY_CACHE
	AS_QUERY_CACHE = cache


def save_as_cache():
	global AS_QUERY_CACHE
	with open(AS_CACHE, "w") as f:
		f.write(json.dumps(AS_QUERY_CACHE))


def calculate_bw(entry):
	#bits = bytes_in_G * 1024 * 1024 * 1024 * 8
	bytes_count = nfsenutils.traff_to_val(nfsenutils.get_traffic(entry[nfsenutils.BYTES]))
	bits = bytes_count * 8
	bps = bits/(60*5)

	return bps

#23.201.23.163
def _find_limit(entries):
	traffic_list = [nfsenutils.traff_to_val(nfsenutils.get_traffic(entry[nfsenutils.BYTES])) for entry in entries]
	traffic_list = set(traffic_list)
	traffic_list = list(traffic_list)
	traffic_list.sort(reverse=True)

	limit = traffic_list[-2]

	first_appearance = 0

	for index, entry in enumerate(entries):

		#print(nfsenutils.traff_to_val(entry[nfsenutils.BPS]))

		if nfsenutils.traff_to_val(entry[nfsenutils.BYTES]) == limit:
			#print("Ocurrence found")
			first_appearance = index
			break

	ignore_list = [ipaddress.IPv4Address(entry[nfsenutils.IP]) for entry in entries[first_appearance:]]

	return limit, ignore_list


def get_nfsen_available_as(interface, router, timestamp, nfsen):
	query = {"filter": "out if %s" % interface, 
			 "stattype": 11,
			 "topN": 3}

	query["srcselector[]"] = router

	nfsen_output = nfsen.query(query, timestamp)
		
	if DEBUG:
		print(nfsen_output)
		
	nfsen_dump = nfsenutils.get_sdump_entries(nfsen_output)

	as_traffic = {}

	has_as_zero = False
	for entry in nfsen_dump:
		as_num = entry[nfsenutils.AS]

		if as_num in BAD_AS_LIST:
			has_as_zero = True
			continue

		bps = nfsenutils.traff_to_val(entry[nfsenutils.BPS])
		calc_bps = calculate_bw(entry)

		as_traffic[as_num] = {"nfsen_bw": bps,
							  "calc_bw": calc_bps}

	#print(as_traffic)
	#print("HAS ZERO ", has_as_zero)

	return as_traffic, has_as_zero


def as_explorer(interface, router, AS_CAPTURE=None, timestamp=None, silent=False):

	if timestamp is None:
		timestamp = int(time.time()) - (5*60)

	nfsen = nfsenutils.NFSENServer("https://nfsen.us.iptp.net")

	nfsen.login()

	as_traffic, has_as_zero = get_nfsen_available_as(interface, router, timestamp, nfsen)

	if has_as_zero:
		#limit_size is the parameter to change in bps

		query = {"filter": "out if %s and (src as 0 or src as 3549)" % interface,
				 "stattype": 2,
				 "srcselector[]": router,
				 "topN": 5,                  # Top 500
				 #"statorder": 4				 # Order by bps
				 #"limitoutput": "checked"    # Limit True
				 #"limitwhat": 1,             # Limit according to Traffic
				 #"limitsize": 0             # Limit to at max 0 bps
				}

		#{traffic: "ETC NETWORKS"}
		#as_traffic = {}
		as_captured = []
		ignore_list = []
		unknown = []
		unknown_nfsen_traff = 0
		unknown_calc_traff = 0
		passes = 0
		#while True:
		for a in range(3):
			passes += 1
			nfsen_output = nfsen.query(query, timestamp)
			
			if DEBUG:
				print(nfsen_output)
			
			nfsen_dump = nfsenutils.get_sdump_entries(nfsen_output)
			whoip.whoipe(nfsen_dump)

			networks = load_cache()

			for entry in nfsen_dump:
				ip = ipaddress.IPv4Address(entry[nfsenutils.IP])
			
				if ip in ignore_list:
					continue
			
				bps = nfsenutils.traff_to_val(entry[nfsenutils.BPS])
				calc_bps = calculate_bw(entry)

				as_num = None

				for net in networks:
					if ip in net["network"]:
						as_num = net["as_num"]
						break

				if as_num is None:
					unknown.append(ip)
					unknown_nfsen_traff += bps
					unknown_calc_traff += calc_bps
				else:
					if not as_traffic.get(as_num, 0):
						as_traffic[as_num] = {"nfsen_bw": 0,
										  	  "calc_bw": 0}
					as_traffic[as_num] = {"nfsen_bw": as_traffic[as_num]["nfsen_bw"] + bps,
										  "calc_bw": as_traffic[as_num]["calc_bw"] + calc_bps}

					if as_num == AS_CAPTURE:
						as_captured.append(ip)

			if len(nfsen_dump) < 500:
				if DEBUG:
					print("NO MORE DUMPS, FINISHING")
				break

			limit, ignore_list = _find_limit(nfsen_dump) 
			print(limit)
			#pprint(ignore_list) 
			query["limitoutput"] = "checked"    # Limit True
			query["limitwhat"] = 1            # Limit according to Traffic
			query["limithow"] = 1            # Limit according to Traffic
			query["limitsize"] = int(round(limit, 0))             # Limit to at max bps


	as_traffic = {k: v for k, v in sorted(as_traffic.items(), 
										  key=lambda item: item[1]["calc_bw"])}
										  #key=lambda item: item[1]["nfsen_bw"])}

	load_as_cache()

	#pprint(as_traffic)

	result_traffic = copy.deepcopy(as_traffic)

	for as_num, traffic in as_traffic.items():
		#print(traffic)
		ratio = round((traffic["nfsen_bw"] / traffic["calc_bw"]) * 100, 2)
		nfsen_traffic = int(round(traffic["nfsen_bw"], 0))
		as_traffic[as_num]["nfsen_bw"] = nfsenutils.val_to_traff(nfsen_traffic)
		calc_traffic = int(round(traffic["calc_bw"], 0))
		as_traffic[as_num]["calc_bw"] = nfsenutils.val_to_traff(calc_traffic)

		as_name = get_AS_name(as_num)
		result_traffic[as_num]["nfsen_bw"] = int(round(result_traffic[as_num]["nfsen_bw"],0))
		result_traffic[as_num]["calc_bw"] = int(round(result_traffic[as_num]["calc_bw"],0))
		result_traffic[as_num]["ratio"] = ratio
		result_traffic[as_num]["as_name"] = as_name
		
		if not silent:
			print("{:<8} {:<30} {:>10} {:>10} {:>10}%".format(as_num, as_name, 
														  	  as_traffic[as_num]["nfsen_bw"],
														  	  as_traffic[as_num]["calc_bw"],
														  	  ratio))

	save_as_cache()

	if silent:
		return result_traffic

	#print("///////////////////////////////////////////////////")
	#pprint(as_traffic)

	unknown_nfsen_traff = int(round(unknown_nfsen_traff, 0))
	unknown_nfsen_traff = nfsenutils.val_to_traff(unknown_nfsen_traff)
	unknown_calc_traff = int(round(unknown_calc_traff, 0))
	unknown_calc_traff = nfsenutils.val_to_traff(unknown_calc_traff)
	print("TOTAL PASSES: %s" % passes)
	pprint("Unknown traffic: %s" % unknown_nfsen_traff)
	pprint("Unknown CALC traffic: %s" % unknown_calc_traff)
	pprint("Unknowns: " )
	pprint(unknown)

	print("AS Captured: ")
	pprint(as_captured)
	return result_traffic


def to_influx(db, customer, as_traffic, timestamp):
	if DEBUG:
		print("INFLUXING>>>>>>>>>>")
	points = []
	for as_num, as_data in as_traffic.items():
	#for measurement, measurement_data in customer_data["resource_usage"].items():
		point = {
				 "time": timestamp,
				 "measurement": "as_exploration",
				 "tags": {
				 	"customer": customer,
				 	"as_num": as_num,
				 	"as_name": as_data["as_name"]
				 },
				 "fields": {
				 	"nfsen_bw": as_data["nfsen_bw"],
				 	"calc_bw": as_data["calc_bw"],
				 	"ratio": as_data["ratio"],
				 }
		        }
		#for field, field_value in customer_data["resource_usage"][measurement].items():
			#point["fields"][field] = field_value

		points.append(point)
	if DEBUG:
		print(points)
	
	#points = json.dumps(points)
	
	if not DEBUG:
		if points:
			db.write_points(points, database="traffic" ,time_precision="s")



def runner():
	db = intialize_influx()

	# Reference is 5 minutes before now to match nfsen calculation execution.
	timestamp = int(time.time()) - (5 * 60)

	# We are going to take measurements each 4h hours
	# So we need to decrease in ....... seconds

	lapse = 4 # in hours
	decrease = 4 * 60 * 60

	samples = int(24 / 4)

	for a in range(samples):
		print("*********TIME: %s************" % timestamp)
		for country in COUNTRIES:
			print("===========================COUNTRY: %s======================="%country["name"])
			router = country["router"]
			customers = country["customers"]

			for customer in customers:
				if customer["name"] == "GGC Google DOWN":
					continue
				print("-------------------------CUSTOMER: %s-----------------------"%customer["name"])
				as_traffic = as_explorer(customer["interface"], router,
							 timestamp=timestamp,
							 silent=True)
				#print("AS_TRAFFIC:")
				#print(as_traffic)

				if not DEBUG:
					to_influx(db, customer["name"], as_traffic, timestamp)
		# Decrease to take next sample
		timestamp -= decrease


if __name__ == '__main__':
	import sys

	start = time.time()
	args = sys.argv[1:]
	if len(args):
		as_explorer(*args)
	else:
		runner()
	print("TIME TAKEN: %s" % round((time.time()-start)/60,2))
