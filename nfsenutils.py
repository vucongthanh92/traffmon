#!/usr/bin/env python
import ipaddress
import re
import requests
from bs4 import BeautifulSoup
import time
import subprocess
from pprint import pprint
import os
import threading

#===================================================================================================
#To avoid complaints regarding SSL certs...
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#===================================================================================================

NFSEN_REGEX = r'^(.*? .*?) * (.*?) * (.*?) * (.*?) * (.*?\)) * (.*?\)) * (.*?\)) * (\S+(?: \S)?) * (\S+(?: \S)?) * (\S+(?: \S)?)'
NFSEN_META_REGEX = r"(?:(?:(?:(?P<command>\*\*.+)\nnfdump filter:\n)?(?P<filter>.+)\n)?(?P<title>Top .*:)\n)?(?P<header>.*Bytes\(%\).*)\n"

DATE = 0
DURATION = 1
PROTOCOL = 2
AS = 3 # It may also be named 'STAT_CRITERIA'
IP = 3
STAT_CRITERIA = 3
FLOWS = 4
PACKETS = 5
BYTES = 6
PPS = 7
BPS = 8
BPP = 9

MULTIPLIERS = {"": 1,
               "K": 1000,
               "M": 1000000,
               "G": 1000000000,
               "T": 1000000000000}


def get_sdump_meta(nfsen_dump_string):
    # We expect to get only one value

    meta = [m.groupdict() for m in re.finditer(NFSEN_META_REGEX, nfsen_dump_string)]
    try:
        return meta.pop()
    except IndexError:
        return {"command": None, "filter": None, "title": None, "header":None}


def get_dump_meta(nfsen_dump_file):
    nfsen_dump_string = open(nfsen_dump_file).read()
    
    return get_sdump_meta(nfsen_dump_string)


def get_dump_entries(nfsen_dump_file):
    
    nfsen_dump_string = open(nfsen_dump_file).read()
    
    return get_sdump_entries(nfsen_dump_string)

    
def get_sdump_entries(nfsen_dump_string):
    nfsen_dump_string = nfsen_dump_string.split("by bytes:").pop()
    nfsen_entries = re.findall(NFSEN_REGEX, nfsen_dump_string, re.MULTILINE)

    if len(nfsen_entries):
        if "Bytes(%)" in nfsen_entries[0]:
            # We strip header.
            return nfsen_entries[1:]
        else:
            return nfsen_entries
    else:
        return []


def val_to_traff(val):
    import math
    size = ["", "K", "M", "G", "T"]
    factor = math.floor((len(str(val)) - 2) / 3)
    return str(round(val / (1000 ** factor), 1)) + " " +size[factor]


def get_traffic(traff_statistic):
    return traff_statistic.split("(")[0]


def traff_to_val(traff_statistic):
    traff = get_traffic(traff_statistic)
    traff_multiplier_pair = traff.split()
    traff_num = traff_multiplier_pair[0]
    traff_multiplier = traff_multiplier_pair[1] if len(traff_multiplier_pair) > 1 else ""
    traff_val = float(traff_num) * MULTIPLIERS[traff_multiplier]
    
    return traff_val


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

    
def to_nfsen_time(timestamp=None):
    return time.strftime("%Y%m%d%H%M", time.gmtime(timestamp))


def get_fqdn(ip):
    #it may probably be a good idea to point to IPTP DNS
    try:
        #ip = subprocess.check_output('nslookup %s | grep name | sed "s/.*name = //"' % ip, shell=True).decode().strip()
        nslookup = subprocess.check_output('nslookup %s' % ip, shell=True).decode()
    except subprocess.CalledProcessError:
        return ""

    ip = re.findall(r"Nombre: *(.*)|name = (.*)", nslookup) # get only first value
    
    if len(ip):

        if os.name == "nt":
            return ip.pop()[0].strip()
        else:
            return ip.pop()[1].strip()

    else:
        return ""
    
    
class NFSENServer():
    def __init__(self, url):
        self.url = url
        self.auth = ("nfsen_username", "nfsen_password")
        self.nfsen = None
        self.routers = None
        self._page = None
        self._size = None
        self.last_details_tab = None
        self._time = None
        
    def login(self):

        nfsen = requests.Session()

        resp = nfsen.get(self.url, auth=self.auth, verify=False)
        
        self.nfsen = nfsen

        #print("Logged into NFSEN")
        
    def load_details_tab(self):
        if self.nfsen:
            
            if self._page == "DETAILS":
                return self.last_details_tab
            
            resp = self.nfsen.get(self.url + "/nfsen.php?tab=2", 
                                  auth=self.auth,
                                  verify=False,
                                  headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
            self._page = "DETAILS"
            self._last_details_tab = resp
            
            return resp
        
        else:
            raise Exception
        
    def set_window_size(self, size):
        self.load_details_tab()

        if self.nfsen:
            if size == self._size:
                return None

            resp = self.nfsen.post(self.url + "/nfsen.php",
                                   data={"wsize": size},
                                   auth=self.auth,
                                   verify=False,
                                   headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})

            self._size = size

            return resp

        else:
            raise Exception

    def set_slot_range(self, time):
        if self.nfsen:
            if time == self._time:
                return None
            
            resp = self.nfsen.post(self.url + "/nfsen.php", 
                                   data={"cursor_mode": 0, "tleft": time, "tright":time}, 
                                   auth=self.auth,
                                   verify=False,
                                   headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
            
            self._time = time
            
            return resp
        
        else:
            raise Exception

    def _get_router_responses(self, router_name, query_time, router_responses_storage):
        start = time.time()

        try:
            router_responses_storage[router_name] = (self.query({"srcselector[]": router_name,
                                                                "stattype": 15},
                                                                query_time))

        except requests.exceptions.ConnectionError:
            print("ERROR POLLING ROUTER %s" % router_name)
            end = time.time()
            print("Time taken to FAIL discover router %s: %s" % (router_name, end-start))
        
        end = time.time()

        print("%s Time taken to discover router %s: %s" % (self.url, router_name, end-start))
        return
    
    def discover_routers(self):
        print("Getting routers list")
        details_tab = self.load_details_tab()
        
        if os.name == "nt":
            html = BeautifulSoup(details_tab.text,features="html.parser")
        else:
            html = BeautifulSoup(details_tab.text)
        
        src_selector = html.find(id="SourceSelector").find_all("option")
        routers_name = [router.text for router in src_selector]
        
        not_found = []
        routers = {}
        
        print("Getting routers details")
        #essentially, now
        query_time = int(time.time()) - (int(time.time()) % (5*60))-10*60
        
        router_dumps = {}
        threads = []

        THREAD_COUNT = 3
        start = time.time()

        for index, router_name in enumerate(routers_name):
            t = threading.Thread(target=self._get_router_responses, 
                                 args=(router_name, query_time, router_dumps))
            t.start()
            threads.append(t)
                                                              # 2 - 1 - 0     < 2
            if len(threads) == THREAD_COUNT or (len(routers_name) - 1 == index):
                print("Threads %s: %s" % (self.url, len(threads)))

                for t in threads:
                    t.join()

                threads = []

        end = time.time()

        print("Time taken to poll all routers %s: %s" % (self.url, end - start))

        for router_name in routers_name:
            
            if router_dumps.get(router_name):
                nfsen_entries = get_sdump_entries(router_dumps[router_name])
                if router_name == "r0-203-sp3":
                    print(router_dumps[router_name])
                if len(nfsen_entries):
                    router_ip = nfsen_entries[0][STAT_CRITERIA]
                    routers[router_name] = {"router_ip": router_ip}
                    """router_fqdn = get_fqdn(router_ip)
                
                    routers[router_name] = {"router_ip": router_ip,
                                            "router_fqdn": router_fqdn}"""
                else:
                    not_found.append(router_name)
            else:
                not_found.append(router_name)

        start = time.time()

        for router in routers:
            router_fqdn = get_fqdn(routers[router]["router_ip"])

            routers[router]["router_fqdn"] = router_fqdn

        end =  time.time()

        print("FINISHED TO GET FQDN FOR %s: %s" % (self.url, end - start))

        self.routers = routers

        if not_found:
            print("NOT FOUND", not_found)
            
    def query(self, query, time):
        QUERY_DEFAULTS = {"aggr_dstnetbits": 24,
                          "aggr_dstselect": 0,
                          "aggr_srcnetbits": 24,
                          "aggr_srcselect": 0,
                          "customfmt": "",
                          "DefaultFilter": -1,
                          "filter": "",
                          "filter_name": "none",
                          "limithow": 0,
                          "limitscale": 0,
                          "limitsize": 0,
                          "limitwhat": 0,
                          "listN": 0,
                          "modeselect": 1,
                          "output": "auto",
                          "process": "process",
                          "srcselector[]": "",
                          "statorder": 2,
                          "stattype": 2,
                          "topN": 0}

        query = merge_two_dicts(QUERY_DEFAULTS, query)

        #Load Details tab
        self.load_details_tab()

        #Set time slot/range
        self.set_slot_range(time)
        
        #Make query
        resp = self.nfsen.post(self.url + "/nfsen.php", data=query, verify=False, auth=self.auth, headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})

        #print(resp)
        if os.name == "nt":
            html = BeautifulSoup(resp.text,features="html.parser")
        else:
            html = BeautifulSoup(resp.text,features="html.parser")

        flowchart = html.find(class_="flowlist").pre.find_all(text=True)

        nfsen_dump = "".join(flowchart)

        #print(nfsen_dump)
        return nfsen_dump

        
if __name__ == "__main__":
    import sys
    import time
    
    nfsen = NFSENServer("https://nfsen.eu.iptp.net")
    nfsen.login()
    #nfsen_dump = nfsen.query({"filter": "in if 55 and (src net 31.220.24.0/22 or src net 46.229.162.0/23 or src net 46.229.165.0/24 or src net 46.229.166.0/23 or src net 46.229.168.0/23 or src net 46.229.170.0/24 or src net 46.229.171.0/24 or src net 46.229.172.0/24 or src net 46.229.160.0/20 or src net 46.229.174.0/23 or src net 86.104.127.0/25 or src net 88.208.0.0/21 or src net 88.208.10.0/23 or src net 88.208.12.0/23 or src net 88.208.14.0/23 or src net 88.208.16.0/21 or src net 88.208.28.0/23 or src net 88.208.31.0/24 or src net 88.208.32.0/20 or src net 88.208.34.0/23 or src net 88.208.36.0/22 or src net 88.208.40.0/23 or src net 88.208.43.0/22 or src net 93.119.155.0/24 or src net 94.176.210.0/23 or src net 185.56.232.0/22 or src net 185.98.52.0/22 or src net 185.177.92.0/23 or src net 185.189.68.0/22 or src net 192.243.51.0/24 or src net 192.243.48.0/20 or src net 213.174.129.0/24 or src net 213.174.131.0/24 or src net 213.174.132.0/24 or src net 213.174.133.0/24 or src net 213.174.134.0/23 or src net 213.174.148.0/24 or src net 213.174.149/24 or src net 213.174.151/24 or src net 213.174.152.0/23 or src net 213.174.154.0/26 or src net 213.174.157.32/28 or src net 213.174.158.0/23)",
    #                          "topN": 5,
    #                          "srcselector[]": "r1-nkf"}, to_nfsen_time())
    
    #print(get_sdump_entries(nfsen_dump)) 
    
    nfsen.discover_routers()


def is_subnet(net, supernet):
	lower_bound = ipaddress.IPv4Address(int.from_bytes(net.network_address.packed, "big") & (
			(0xFFFFFFFF >> (32 - supernet.prefixlen)) << (32 - supernet.prefixlen)))
	upper_bound = ipaddress.IPv4Address(int.from_bytes(net.broadcast_address.packed, "big") & (
			(0xFFFFFFFF >> (32 - supernet.prefixlen)) << (32 - supernet.prefixlen)))

	if lower_bound == supernet.network_address and upper_bound == supernet.network_address:
		# print([net, lower_bound, upper_bound, supernet])
		return True
	return False


def remove_subnets(iprange):
	asinfo_range = list(iprange)
	asinfo_full_range = list(asinfo_range)

	#checked = []
	print("-------------------------------------------------")
	#for index, subnet in enumerate(asinfo_full_range):
	for subnet in asinfo_full_range:
		# print("CHECKING SUBNET", subnet,'***********************************************')
		#checked.append(subnet)
		for net in asinfo_range:
			# print("EVALUATED NET", net, '++++++++++++++++++++++++++++++++++++++')
			if subnet is net:
				# print(" ///////////////////////SAME OBJECT///////////////////////////")
				continue

			# is_subnet(net, net_test)

			if is_subnet(subnet, net):
				# print(subnet, net, "SUBNET")
				asinfo_range.remove(subnet)
				# print(" ///////////////////////SUBNET FOUND///////////////////////////")
				break

	return asinfo_range
