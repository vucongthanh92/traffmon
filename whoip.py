from time import time
import nfsenutils
import subprocess
import re
import ipaddress
import json
from get_subnets import get_subnet_from_looking_glass_bgp


CACHE = "network_cache"


def whois(ip):
	try:
		output = subprocess.check_output("whois -h whois.radb.net %s" % ip, shell=True).decode()
		#print(output)
	except (UnicodeDecodeError, subprocess.CalledProcessError):
		output = '%  No entries found'

	if re.findall(r'%  No entries found', output):
		return get_subnet_from_looking_glass_bgp(ip, "18228f6a4bd5")
	else:
		as_nums = re.findall(r'^origin:\s*[Aa][Ss](\d*)',output, flags=re.MULTILINE)
		networks = re.findall(r'^route:\s*([0-9,\/,.]*)', output, flags=re.MULTILINE)

		#print(as_nums)
		#print(networks)

		if len(as_nums) != len(networks):
			print("SOMETHING WENT WRONG DURING IP RANGE/AS PARSING %s" % ip)
			raise

		list_nets = []
		for index, net in enumerate(networks):
			as_num = as_nums[index]
			net = ipaddress.ip_network(net)
			list_nets.append({"as_num": as_num,
							  "subnet": net})

		def func(e):
			return e["subnet"]

		list_nets.sort(key=func)

		print(list_nets)
		as_num = list_nets[-1]["as_num"]
		subnet = list_nets[-1]["subnet"]

		#subnet = ipaddress.ip_network(network)

	return as_num, subnet


def whoipe(nfsen_dump):
	#nfsen_dump = nfsenutils.get_dump_entries(dump_file)

	try:
		cache = json.loads(open(CACHE).read())
	except (json.JSONDecodeError, FileNotFoundError):
		cache = {"time": 0, "networks": []}

	networks_cache = cache.get("networks")

	networks = []

	for network_cache in networks_cache:
		networks.append({"network": ipaddress.ip_network(network_cache["network"]),
						 "as_num": network_cache["as_num"]})

	not_founds = []

	#Expire cache every 24h
	if cache["time"] + 60 * 60 * 24 < time():
		renew_cache = True
	else:
		renew_cache = False

	entries_count = 0
	query_count = 0

	for entry in nfsen_dump:
		ip = ipaddress.IPv4Address(entry[nfsenutils.STAT_CRITERIA])

		#print(ip)

		for network in networks:
			if ip in network["network"]:
				break
		else:
			as_num, network = whois(ip)
			print(as_num, network)
			if network:
				networks.append({"network": network,
								 "as_num": as_num})
				renew_cache = True
			else:
				not_founds.append("%s" % ip)
			query_count += 1
		entries_count += 1

	if renew_cache:

		networks_cache = [] 

		for network in networks:
			networks_cache.append({"network": "%s" % network["network"],
								   "as_num": network["as_num"]})

		cache = {"time": time(),
		         "networks": networks_cache}

		with open(CACHE, "w") as f:
			f.write(json.dumps(cache, indent=4))


	#print(networks)
	#print(not_founds)
	print("Entries: %s" % entries_count)
	print("Queries: %s" % query_count)
	print("Ratio: %s" % (query_count / entries_count))

	with open("not_founds", "a") as f:
		f.writelines(not_founds)


def whoip(dump_file):
	nfsen_dump = nfsenutils.get_dump_entries(dump_file)

	whoipe(nfsen_dump)


if __name__ == '__main__':
	whoip()