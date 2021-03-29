import config

DEBUG = config.PREFIX_CHECKER_DEBUG

from nfsenutils import remove_subnets
from device_console import Device
import traffmon
import re
import ipaddress
import json
import subprocess


class NetEncoder(json.JSONEncoder):
	def default(self, o):
		return "%s" % o


def upload_to_traffmon():
	if not DEBUG:
		subprocess.run("scp interfaces_prefixes danielpl@traffmon.pe.iptp.net:/home/danielpl/traffmon/interfaces_prefixes",
					   shell=True)


def prefix_checker(hostname, prompt):
	interfaces_prefixes = {}

	router = Device(hostname, prompt)
	router.login()

	ifindexes = router.show("show snmp mib ifmib ifindex")
	neighbors = router.show("show ip bgp summary")

	neighbors_addresses = re.findall(r'^\d*\.\d*\.\d*\.\d*',neighbors, flags=re.MULTILINE)
	neighbors_addresses = [ipaddress.IPv4Address(ip) for ip in neighbors_addresses]

	static_routes = router.show("show ip route static")

	if DEBUG:
		print(static_routes)
		#print(ifindexes)
		print(neighbors_addresses)

	for uplink in config.CACHES:
		if uplink.get("check", 0):
			if DEBUG:
				print("="*70)
				print(uplink)
			interface = re.findall(r'^(.*):.*= '+ uplink["match"] + r'\r$' , #\r added due to unable to override $ behaviour
								   ifindexes,
								   flags=re.MULTILINE)
			if DEBUG:
				print(interface)

			if not interface:
				print("ERROR: Seems interface with index %s does not exist anymore, skipping %s." % (uplink["interface"], uplink["name"]))
				continue
			else:
				interface = interface.pop()

			interface_config = router.show("show run interface %s" % interface)
			#print(interface_config)
			interface_range = re.findall(r'ip address (.*) (.*)\r', interface_config).pop()
			interface_range = ipaddress.IPv4Interface("%s/%s"%interface_range)

			if DEBUG:
				print(interface_range)

			neighbor_ip = None
			for neighbor in neighbors_addresses:
				if neighbor in interface_range.network:
					neighbor_ip = neighbor
					break
			else:
				print("INFO: BGP Neighbor not found for %s" % uplink["name"])

			if neighbor_ip:
				neighbor_bgp_routes = router.show("show ip bgp neighbor %s route" % neighbor_ip)
				# [network, 	nexthop]
				neighbor_bgp_routes = re.findall(r'\*>  (\d*\.\d*\.\d*\.\d+(?:/\d*)?)\s*(\d*\.\d*\.\d*\.\d*)',
												 neighbor_bgp_routes,
												 flags=re.MULTILINE)
				if DEBUG:
					print(neighbor_bgp_routes)

			nexthop = set(ipaddress.IPv4Address(subnet[1]) for subnet in neighbor_bgp_routes)
			
			if len(nexthop) == 1:
				nexthop = nexthop.pop()
			elif len(nexthop) == 0:
				nexthop = None
			else:
				print(nexthop)
				print("POSSIBLE ERROR: Found more than one nexthop in BGP prefixes list.")
				raise

			neighbor_bgp_subnets = [ipaddress.IPv4Network(subnet[0]) for subnet in neighbor_bgp_routes]
			simplified_neighbor_bgp_subnets = remove_subnets(neighbor_bgp_subnets)
			if DEBUG:
				print(simplified_neighbor_bgp_subnets)
			excluded_ranges = []
			for subnet in simplified_neighbor_bgp_subnets:
				longer_prefixes = router.show("show ip route %s %s longer-prefixes" % (subnet.network_address, subnet.netmask))
				# [subnet, via, interface]
				#print(longer_prefixes)
				longer_prefixes = re.findall(r'^[^L\s]\s*(\d*\.\d*\.\d*\.\d+(?:/\d*)?)(?:(?:.*via (\d*\.\d*\.\d*\.\d*))|.*connected, (.*)\r)',
											 longer_prefixes,
											 flags=re.MULTILINE)
				if DEBUG:
					print(longer_prefixes)

				diff_hop_prefixes = []
				same_hop_prefixes = []

				for prefix, via, prefix_interface in longer_prefixes:
					prefix = ipaddress.IPv4Network(prefix)
					if via:
						via = ipaddress.IPv4Address(via)
						if via != nexthop:
							diff_hop_prefixes.append(prefix)
						else:
							same_hop_prefixes.append(prefix)
							for diff_prefix in diff_hop_prefixes:
								if prefix in diff_prefix:
									print(prefix, diff_prefix)
									print("ISSUE, Found same hop prefix inside diff prefixes. We should fix this...")
									raise
					else:
						if interface != prefix_interface:
							diff_hop_prefixes.append(prefix)
						else:
							same_hop_prefixes.append(prefix)
							for diff_prefix in diff_hop_prefixes:
								if prefix in diff_prefix:
									print(prefix, diff_prefix)
									print("ISSUE, Found same hop prefix inside diff prefixes. We should fix this...")
									raise
				excluded_ranges += diff_hop_prefixes
				if DEBUG:
					print(diff_hop_prefixes)
					print("/////////////////////////////////////////////")

			interfaces_prefixes[uplink["match"]] = {"included": list([interface_range.network]) + simplified_neighbor_bgp_subnets,
													"excluded": excluded_ranges}
			#break
	with open("interfaces_prefixes", "w") as f:
		f.write(json.dumps(interfaces_prefixes, indent=4, cls=NetEncoder))

	upload_to_traffmon()


if __name__ == '__main__':
	prefix_checker("91.194.117.217", "r0.f1k12.l3.lim.pe")
