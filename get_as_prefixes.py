def get_as_prefixes(as_num):
	
	output = subprocess.check_output("whois -h whois.radb.net %s" % ip, shell=True).decode()
	print(output)

	if re.findall(r'%  No entries found', output):
		return get_subnet_from_looking_glass_bgp(ip, "18228f6a4bd5")
	else:
		as_nums = re.findall(r'origin:\s*[Aa][Ss](\d*)',output)
		networks = re.findall(r'^route:\s*([0-9,\/,.]*)', output, flags=re.MULTILINE)

		print(as_nums)
		print(networks)

		if len(as_nums) != len(networks):
			print("SOMETHING WENT WRONG DURING IP RANGE/AS PARSING")
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

if __name__ == '__main__':
	import sys

	get_as_prefixes(*sys.agrv[1:])
