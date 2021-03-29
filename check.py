import json
import requests
import json
import ipaddress
from bs4 import BeautifulSoup
import maxmind
import subprocess
import re
from pprint import pprint


def router(AS):

	data =  """*b  31.13.24.0/21    157.240.73.136           0    115      0 32934 i
 *b  31.13.64.0/19    157.240.73.136           0    115      0 32934 i
 *b  31.13.64.0/18    157.240.73.136           0    115      0 32934 i
 *b  31.13.96.0/19    157.240.73.136           0    115      0 32934 i
 *>  45.64.40.0/22    157.240.73.136           0    115      0 32934 i
 *b  66.111.48.0/24   157.240.73.136           0    115      0 32934 11917 i
 *b  66.111.48.0/22   157.240.73.136           0    115      0 32934 11917 i
 *b  66.111.49.0/24   157.240.73.136           0    115      0 32934 11917 i
 *b  66.111.50.0/24   157.240.73.136           0    115      0 32934 11917 i
 *b  66.111.51.0/24   157.240.73.136           0    115      0 32934 11917 i
 *b  66.220.144.0/21  157.240.73.136           0    115      0 32934 i
 *b  66.220.144.0/20  157.240.73.136           0    115      0 32934 i
 *b  66.220.152.0/21  157.240.73.136           0    115      0 32934 i
 *b  69.63.176.0/21   157.240.73.136           0    115      0 32934 i
 *b  69.63.176.0/20   157.240.73.136           0    115      0 32934 i
 *b  69.171.224.0/20  157.240.73.136           0    115      0 32934 i
 *b  69.171.224.0/19  157.240.73.136           0    115      0 32934 i
 *b  69.171.240.0/20  157.240.73.136           0    115      0 32934 i
 *b  69.171.250.0/24  157.240.73.136           0    115      0 32934 i
 *b  74.119.76.0/22   157.240.73.136           0    115      0 32934 i
 *b  102.132.96.0/20  157.240.73.136           0    115      0 32934 i
 *b  103.4.96.0/22    157.240.73.136           0    115      0 32934 i
 *b  129.134.0.0/17   157.240.73.136           0    115      0 32934 i
 *b  129.134.30.0/24  157.240.73.136           0    115      0 32934 i
 *b  129.134.30.0/23  157.240.73.136           0    115      0 32934 i
 *b  129.134.31.0/24  157.240.73.136           0    115      0 32934 i
 *b  157.240.0.0/17   157.240.73.136           0    115      0 32934 i
 *b  157.240.192.0/18 157.240.73.136           0    115      0 32934 i
 *b  157.240.197.0/24 157.240.73.136           0    115      0 32934 i
 *b  163.114.128.0/20 157.240.73.136           0    115      0 32934 54115 ?
 *b  163.114.130.0/24 157.240.73.136           0    115      0 32934 54115 ?
 *b  173.252.64.0/19  157.240.73.136           0    115      0 32934 i
 *b  173.252.88.0/21  157.240.73.136           0    115      0 32934 i
 *b  173.252.96.0/19  157.240.73.136           0    115      0 32934 i
 *b  179.60.192.0/22  157.240.73.136           0    115      0 32934 i
 *b  185.60.216.0/22  157.240.73.136           0    115      0 32934 i
 *b  185.89.218.0/24  157.240.73.136           0    115      0 32934 i
 *b  185.89.218.0/23  157.240.73.136           0    115      0 32934 i
 *b  185.89.219.0/24  157.240.73.136           0    115      0 32934 i
 *b  199.201.64.0/22  157.240.73.136           0    115      0 32934 54115 i
 *b  204.15.20.0/22   157.240.73.136           0    115      0 32934 i"""

	networks = []

	for line in data.splitlines():
		subnet = ipaddress.ip_network(line.split()[1])
		networks.append(subnet)

	return networks


def mass_whois(AS):
	output = subprocess.check_output("whois -h whois.radb.net -- '-i origin AS%s' | grep ^route:" % AS, shell=True).decode()
	#print(output)
	networks = []
	for net in output.splitlines():
		print(net)
		network = re.findall(r'^route:\s*([0-9,\/,.]*)', net).pop(0)
		subnet = ipaddress.ip_network(network)

		networks.append(subnet)

	return networks


def is_subnet(net, supernet):
	lower_bound	= ipaddress.IPv4Address(int.from_bytes(net.network_address.packed, "big") & ((0xFFFFFFFF >> (32 - supernet.prefixlen)) << (32 - supernet.prefixlen)))
	upper_bound	= ipaddress.IPv4Address(int.from_bytes(net.broadcast_address.packed, "big") & ((0xFFFFFFFF >> (32 - supernet.prefixlen)) << (32 - supernet.prefixlen)))

	if lower_bound == supernet.network_address and upper_bound == supernet.network_address:
		#print([net, lower_bound, upper_bound, supernet])
		return True
	return False


def remove_subnets(iprange):
	asinfo_range = list(iprange)
	asinfo_full_range = list(asinfo_range)

	checked = []
	#asinfo_range = []
	print("-------------------------------------------------")
	for index, subnet in enumerate(asinfo_full_range):
		#print("CHECKING SUBNET", subnet,'***********************************************')
		checked.append(subnet)
		for net in asinfo_range:
			#print("EVALUATED NET", net, '++++++++++++++++++++++++++++++++++++++')
			if subnet == net:
				#print(" ///////////////////////SAME OBJECT///////////////////////////")
				continue

			#	is_subnet(net, net_test)


			if is_subnet(subnet, net):
				#print(subnet, net, "SUBNET")
				#del asinfo_range[index]
				asinfo_range.remove(subnet)
				#print(" ///////////////////////SUBNET FOUND///////////////////////////")
				#raise
				break

	return asinfo_range


AS = 3132

asinfo_req = requests.get("https://ipinfo.io/AS%s" % AS)

asinfo_html = BeautifulSoup(asinfo_req.content)

ipv4_data_html = asinfo_html.find(id="ipv4-data")
#print(ipv4_data_html.find("tbody").find_all("a"))

asinfo_range = ipv4_data_html.find("tbody").find_all("a")
asinfo_range = [ipaddress.ip_network(net.text.strip()) for net in asinfo_range]

print(asinfo_range)

#Remove containeds

asinfo_range = remove_subnets(asinfo_range)

pprint(asinfo_range)
print("*"*50)

maxmind_range = maxmind.maxmind(AS)
#pprint(maxmind_range)
#print(len(maxmind_range))
#print("////////////////////////////////////////////////")
maxmind_range = remove_subnets(maxmind_range)
pprint(maxmind_range)
print(len(maxmind_range))
print("*"*50, "MASS WHOIS")


mass_whois_range = mass_whois(AS)
mass_whois_range = remove_subnets(mass_whois_range)
pprint(mass_whois_range)
print(len(mass_whois_range))
print("*"*50, "ROUTER")

router_range = router(AS)
router_range = remove_subnets(router_range)
pprint(router_range)
print(len(router_range))
print("*"*50, "")

#google_range = requests.get("https://www.gstatic.com/ipranges/goog.json")
#google_range = json.loads(google_range.content)

#google_range = [ipaddress.ip_network(net["ipv4Prefix"]) for net in google_range["prefixes"] if net.get("ipv4Prefix")]
#print(google_range)

a = json.load(open("network_cache"))

blanks = [net for net in a["networks"] if net["as_num"] == "%s" %AS]

print("****************************************")
ips = []
for blank in blanks:
	ips.append(ipaddress.ip_network(blank["network"]))

print(ips)


#check if every ip of the NFSEN LIST is in the official list
for nfsen_ip in ips:
	is_in_official = False
	for google_subn in asinfo_range:
		if nfsen_ip.overlaps(google_subn):
			print(nfsen_ip, "in",google_subn)
			is_in_official = True
			break

	if not is_in_official:
		print("ASINOF NET %s NOT IN OFICIAL LIST" % nfsen_ip)
		raise

print("ALL NFSEN IP ARE IN ASINFO LIST")



#filt = " or src net ".join(ips)

#print(filt)