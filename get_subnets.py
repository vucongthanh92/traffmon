import nfsenutils
import requests
import re

from bs4 import BeautifulSoup
import ipaddress
import pprint

#===================================================================================================
#To avoid complaints regarding SSL certs...
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#===================================================================================================

PRIVATE_NETWORKS = [ipaddress.ip_network("10.0.0.0/8"),
					ipaddress.ip_network("172.16.0.0/12"),
					ipaddress.ip_network("192.168.0.0/16"),]


def get_subnet_from_looking_glass_bgp(ip, looking_glass_router_id, debug=False):
	r = requests.get("https://www.iptp.net/en_US/iptp-tools/lg/?command=bgp&query={ip}&router={router}&protocol=ipv4".format(ip=ip,router=looking_glass_router_id),
					 verify=False)

	#print("Asking to %s" % r.url)

	#with open("lg.html", "wb") as f:
    #		f.write(r.content)

	html = BeautifulSoup(r.content,
						 features="html.parser")

	content = html.find(id="content")
	result =  content.code.text

	if debug:
		print("Query IP: %s" % ip)
		print("Result:")
		print(result)

	try:
		subnet = re.findall(r"BGP routing table entry for (.*\/\d+)", result).pop()
		#paths = re.findall(r"^  (\d+ )*(\d+)$", result, flags=re.MULTILINE)
		paths = re.findall(r"^  (\d+ )*(\d+)(?:,.*)?$", result, flags=re.MULTILINE)
		#print(paths)
		as_num = paths.pop(0)[-1]
	except IndexError:
		print("ERROR NOT FOUND")
		print("Looking glass output: ")
		print(result)
		return None, None

	if subnet == "0.0.0.0/0":
		print("DEFAULT ROUTE")
		return None, None

	subnet = ipaddress.ip_network(subnet)

	print(as_num, subnet)

	return as_num, subnet


def get_subnets(nfsendump, looking_glass_router_id, deep=False, debug=False):
	# deep is used to ask looking glass for every single IP, 
	# normal behaviour is to compare first with already collected
	# subnets, if not found ask looking glass

	nfsen_entries = nfsenutils.get_dump_entries(nfsendump)

	networks = []
	not_founds = []
	privates = []

	for entry in nfsen_entries:
		# get ip address
		ip = ipaddress.IPv4Address(entry[nfsenutils.STAT_CRITERIA])

		if ip.is_private:
			privates.append(ip)
		else:
			for network in networks:
				if ip in network:
					break
			else:
				# The ip is not in any of our known networks, ask looking glass
				as_num, network = get_subnet_from_looking_glass_bgp(ip, looking_glass_router_id, debug)
				if network:
					networks.append(network)
				else:
					not_founds.append(ip)

	print("Networks Found: ")
	for network in networks:
		print(network)

	# A good idea could be to recheck only the not_founds

	if not_founds:
		print("UNABLE TO GET SUBNET FOR THE FOLLOWING IPs: ")
		for not_found in not_founds:
			print(not_found)


if __name__ == "__main__":
	import sys

	"""if len(sys.argv) != 2:
		print("Usage: [nfsendump with ip sources] [router id taken from looking glass]")
		return -1"""
	# Peru 18228f6a4bd5
	#get_subnets(*sys.argv[1:])
	get_subnet_from_looking_glass_bgp(*sys.argv[1:])

#	get_subnet_from_looking_glass_bgp(*sys.argv[1:])
