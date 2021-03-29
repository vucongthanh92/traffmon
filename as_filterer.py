import json
import ipaddress
import subprocess
import re
from pprint import pprint

import config
import time

from nfsenutils import is_subnet, remove_subnets

MAX_FILTER_LENGTH = 10240
FILTER_GUARD = 70


def _mass_whois(AS):
	output = subprocess.check_output("whois -h whois.radb.net -- '-i origin AS%s' | grep ^route:" % AS,
									 shell=True).decode()
	# print(output)
	networks = []
	for net in output.splitlines():
		# print(net)
		network = re.findall(r'^route:\s*([0-9,\/,.]*)', net).pop(0)
		subnet = ipaddress.ip_network(network)

		networks.append(subnet)

	return networks


def mass_whois(AS):
	mass_whois_range = _mass_whois(AS)

	start = time.time()

	mass_whois_range = remove_subnets(mass_whois_range)
	subnet = time.time()
	print("Subnet removal mass whois duration %s" % ((subnet - start) / 60))
	mass_whois_range.sort()
	print("SORT mass whois duration %s" % ((time.time() - subnet) / 60))

	return mass_whois_range


def ip_sumarizing(ip_list):
	import netaddr

	ip_list = [netaddr.IPNetwork("%s" % subn) for subn in ip_list]
	ip_list = netaddr.cidr_merge(ip_list)

	return ip_list


def as_filterer():
	import time
	time_start = time.time()
	as_ranges = {}

	for AS in config.AS_LIST:
		print("*" * 50, "MASS WHOIS", AS["name"])

		mass_whois_range = mass_whois(AS["match"])
		pprint(mass_whois_range)
		print(len(mass_whois_range))

		as_ranges[AS["match"]] = {"name": AS["name"],
								  "as_num": AS["match"],
								  "range": mass_whois_range,
								  "priority": AS.get("priority", 0)}
		#break

	query_time = time.time()
	print("QUERY DURATION: %s" % ((query_time - time_start)/60))

	prio_as = [AS for AS in as_ranges.values() if AS.get("priority", 0)]
	no_prio_as = [AS for AS in as_ranges.values() if not AS.get("priority", 0)]

	for no_prio in no_prio_as:
		for prio in prio_as:
			for ip_range in no_prio["range"]:
				prio_ranges = list(prio["range"])

				for prio_ip_range in prio_ranges:
					if ip_range.overlaps(prio_ip_range):
						print("FOUND OVERLAPS", ip_range, prio_ip_range)
						if ip_range <= prio_ip_range:
							prio["range"].remove(prio_ip_range)
						else:
							# Lets remove ip_range from prio_ip_range
							new_prio_ip_range = list(prio_ip_range.address_exclude(ip_range))
							prio["range"].remove(prio_ip_range)
							prio["range"] = (prio["range"] + new_prio_ip_range)
							prio["range"].sort()

	# Excluding and Including the router prefixes

	try:
		interfaces_prefixes = json.loads(open("interfaces_prefixes").read())
	except (json.JSONDecodeError, FileNotFoundError):
		interfaces_prefixes = {}

	#print(interfaces_prefixes)
	for AS in as_ranges.values():
		as_range = AS["range"]
		includeds = []
		excludeds = []
		for cache_interface in config.CACHES:
			if cache_interface.get("assoc_as") == AS["as_num"]:
				# I have to ignore all the prefixes going through
				# the PNI/cache
				# So. All the cache_routes has to be ignored
				# All the not_cache_routes has to be included.
				interface_prefixes = interfaces_prefixes.get(cache_interface["match"])
				if not interfaces_prefixes:
					continue
				#print(cache_interface)
				#print(interface_prefixes, "prefixes")
				#print("//////////////////// PREFIXES //////////////////////")
				not_cache_routes = [ipaddress.IPv4Network(subn) for subn in interface_prefixes["excluded"]]
				not_cache_routes.sort()
				cache_routes = [ipaddress.IPv4Network(subn) for subn in interface_prefixes["included"]]
				cache_routes.sort()
				#print(includeds)
				#print("///////////////// INCLUDEDS /////////////////////////")
				includeds += not_cache_routes
				excludeds += cache_routes

		#print(includeds)
		#print("+++++++++++++ INCLUDED+++++++++++++++")
		#print(excludeds)
		#print("+++++++++++++ EXCLUDED+++++++++++++++")
		#print("___________________INCLUDEDS/EXCLUDEDS______________________________")
		includeds.sort()
		excludeds.sort()

		# Check we do not have networks in both sides (in/ex)
		excludeds = remove_subnets(excludeds)
		as_range_copy = list(as_range)
		for in_subnet in as_range_copy:
			excludeds_copy = list(excludeds)
			for ex_subnet in excludeds_copy:
				if in_subnet == ex_subnet:
					as_range.remove(in_subnet)
					excludeds.remove(in_subnet)
				elif is_subnet(in_subnet, ex_subnet):
					print("Please test this use case... in_subnet is subnet of ex_subnet")
					raise
				elif is_subnet(ex_subnet, in_subnet):
					test = list(in_subnet.address_exclude(ex_subnet))
					if len(test) == 1:
						as_range = [test[0] if subn == in_subnet else subn for subn in as_range]
						as_range_copy = [test[0] if subn == in_subnet else subn for subn in as_range_copy]
						excludeds.remove(ex_subnet)
						in_subnet = test[0]

		excludeds_copy = list(excludeds)
		
		for ex_sub in excludeds_copy:
			for in_subnet in as_range:
				if ex_sub.overlaps(in_subnet):
					break
			else:
				excludeds.remove(ex_sub)

		includeds_copy = list(includeds)

		for in_sub in includeds_copy:
			for as_subn in as_range:
				if is_subnet(in_sub, as_subn):
					#print("FOUND", in_sub)
					includeds.remove(in_sub)
					break

		includeds = ip_sumarizing(includeds)
		as_range = ip_sumarizing(as_range)

		AS["range"] = ["%s" % rang for rang in as_range]
		AS["exrange"] = ["%s" % rang for rang in excludeds]
		AS["inrange"] = ["%s" % rang for rang in includeds]

		r1 = len(AS.get("range",[]))
		r2 = len(AS.get("inrange",[]))
		r3 = len(AS.get("exrange",[]))
		prefix_count = r1+r2+r3
		print("Prefixes in filter: %s" % (prefix_count))

		# Creating AS_filters

		# Cada prefijo, en el peor caso cosume 22 caracteres
		# queremos una guardia de FILTER_GUARF carateres
		is_too_big = prefix_count > (MAX_FILTER_LENGTH - FILTER_GUARD) / 30
		if is_too_big and not AS.get("exrange",[]):
			# nice handling
			prefixes_list = list(AS["range"])
			filters = []
			sfilter = ""
			if AS.get("inrange", []):
				prefixes_list += AS["inrange"]
			for prefix in prefixes_list:
				if len(sfilter):
					tail = (" or src net " + prefix)
				else:
					tail = ""
					sfilter = "src net " + prefix

				if len(sfilter) + len(tail) + 2 > MAX_FILTER_LENGTH - FILTER_GUARD:
					filters.append("(" + sfilter + ")")
					sfilter = "src net " + prefix
				else:
					sfilter += tail
			else:
				filters.append("(" + sfilter + ")")

			AS["filters"] = filters

		elif is_too_big and AS.get("exrange",[]):
			print("We should handle this case appropiately. Filter list too big and has exrange")
			raise
		else:
			range_filter = "src net " + " or src net ".join(AS["range"])
			exrange_filter = "src net " + " or src net ".join(AS["exrange"])
			inrange_filter = "src net " + " or src net ".join(AS["inrange"])

			# (range and not exrange) or inrange
			if AS.get("exrange"):
				as_filter = f"(({range_filter}) and not ({exrange_filter}))"
			else:
				as_filter = f"({range_filter})"

			if AS.get("inrange"):
				as_filter += f" or ({inrange_filter})"

			AS["filters"] = [as_filter]

	with open("as_range_filters", "w") as f:
		f.write(json.dumps(as_ranges, indent=4))

	process_time = time.time()
	print("PROCESSING DURATION: %s" % ((process_time - query_time) / 60))


if __name__ == '__main__':
	as_filterer()
