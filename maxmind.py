import csv
import ipaddress
from pprint import pprint
import re
AS = 2906


def maxmind(AS, criteria="as"):
	maxmind_range = []

	#OrderedDict([('network', '38.118.195.0/24'), ('autonomous_system_number', '30212'), ('autonomous_system_organization', 'HYPERMEDIA-SYSTEMS')
	with open('/home/iptpnocpe/Downloads/GeoLite2-ASN-Blocks-IPv4.csv', newline='') as f:
		
		reader = csv.DictReader(f)
		for row in reader:
			#print(row)
			if criteria == "as":
				#if re.findall(AS, row["autonomous_system_organization"]):
				if row["autonomous_system_number"] == str(AS):
					maxmind_range.append(ipaddress.IPv4Network(row["network"]))
					#maxmind_range.append([row["autonomous_system_organization"], row["autonomous_system_number"]])
					#maxmind_range.append(list(row.values()))
			else:
				#print(AS,ipaddress.IPv4Network(row["network"]) )
				if ipaddress.IPv4Address(AS) in ipaddress.IPv4Network(row["network"]):
					maxmind_range.append(row)
	#pprint(maxmind_range)
	#print("Network count: %s" % len(maxmind_range))

	return maxmind_range


if __name__ == '__main__':
	import sys
	maxmind_range = maxmind(*sys.argv[1:])

	#pprint(maxmind_range)
	try:
		sys.argv[2] != "as"
		pprint(maxmind_range)
	except IndexError:
		pprint(maxmind_range)
		#for net in maxmind_range:
		#	print([net, net.network_address, net.supernet(prefixlen_diff=1)])
		#	print(["                             ", net.broadcast_address])
		print("Network count: %s" % len(maxmind_range))
