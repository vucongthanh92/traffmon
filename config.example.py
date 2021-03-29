PREFIX_CHECKER_DEBUG = True
AS_EXPLORER_DEBUG = True
TRAFFMON_DEBUG = True


#####################PERU############################

BERNARDO_FILTER = {"name": "Bernardo", "interface": "140", "resources": {"uplinks": {"query":{"filter": "out if 140", "stattype": 8}}, "as": {"query":{"filter": "out if 140", "stattype": 11}}}}
BERNARDO2_FILTER = {"name": "Bernardo 2", "interface": "150", "resources": {"uplinks": {"query":{"filter": "out if 150", "stattype": 8}}, "as": {"query":{"filter": "out if 150", "stattype": 11}}}}
CABLE_SANTA_FE_FILTER = {"name": "Cable Santa Fe", "interface": "69", "resources": {"uplinks": {"query":{"filter": "out if 69", "stattype": 8}}, "as": {"query":{"filter": "out if 69", "stattype": 11}}}}
MEGA_ANDINA_FILTER = {"name": "Mega Andina", "interface": "102", "resources": {"uplinks": {"query":{"filter": "out if 102", "stattype": 8}}, "as": {"query":{"filter": "out if 102", "stattype": 11}}}}
ECONOCABLE_FILTER = {"name": "Econocable", "interface": "130", "resources": {"uplinks": {"query":{"filter": "out if 130", "stattype": 8}}, "as": {"query":{"filter": "out if 130", "stattype": 11}}}}
GGC_GOOGLE_DOWNLINK_FILTER = {"name": "GGC Google DOWN", "interface": "164", "resources": {"uplinks": {"query":{"filter": "out if 164", "stattype": 8}}, "as": {"query":{"filter": "out if 164", "stattype": 11}}}}

PERU_CUSTOMERS = [ECONOCABLE_FILTER, BERNARDO_FILTER, BERNARDO2_FILTER, CABLE_SANTA_FE_FILTER, MEGA_ANDINA_FILTER, GGC_GOOGLE_DOWNLINK_FILTER]

WAVE1_FILTER = {"name": "WAVE 1", "match": "157"}
WAVE2_FILTER = {"name": "WAVE 2", "match": "159"}
HSIP_FILTER =  {"name": "HSIP", "match": "98"}
FACEBOOK1_FILTER =  {"name": "FACEBOOK PNI 1", "match": "161", "check": True, "assoc_as": "32934"} # For some reason facebook only shows one direction
FACEBOOK2_FILTER =  {"name": "FACEBOOK PNI 2", "match": "162", "check": True, "assoc_as": "32934"} # on nfsendump, clarify
GGC_GOOGLE_FILTER = {"name": "GGC Google", "match": "164", "check": True}

CACHES = [FACEBOOK1_FILTER, FACEBOOK2_FILTER, GGC_GOOGLE_FILTER]

PERU_UPLINKS = [WAVE1_FILTER, WAVE2_FILTER, HSIP_FILTER] + CACHES

GOOGLE = {"name": "Google", 'match':"15169"}
FACEBOOK = {"name": "Facebok", 'match':"32934"}
AKAMAI = {"name": "Akamai", 'match':"20940"}
NETFLIX = {"name": "Netflix", 'match':"2906"}
TELEFONICA = {"name": "Telefonica", 'match':"6147", "priority": 1}
AMAZON = {"name": "Amazon", 'match':"16509"}
YACHAY = {"name": "Yachay", 'match':"3132", "priority": 1}

AS_LIST = [GOOGLE, FACEBOOK, AKAMAI, NETFLIX, TELEFONICA, AMAZON, YACHAY]

PERU_RESOURCES = {"uplinks": PERU_UPLINKS, "as": AS_LIST}

#####################BOLIVIA############################

SIRIO_FILTER = {"name": "SIRIO", "interface": "87", "resources": {"as": {"query":{"filter": "out if 87", "stattype": 11}}}}
MEGALINK_FILTER = {"name": "Megalink", "interface": "92", "resources": {"as": {"query":{"filter": "out if 92", "stattype": 11}}}}

BOLIVIA_CUSTOMERS = [SIRIO_FILTER, MEGALINK_FILTER]
BOLIVIA_RESOURCES = {"as": AS_LIST}


COUNTRIES = [{"name": "Peru", "router": "r0-l3-lim-pe", "customers": PERU_CUSTOMERS, "resources": PERU_RESOURCES},
             {"name": "Bolivia", "router": "r0-sql-lim-pe", "customers": BOLIVIA_CUSTOMERS, "resources": BOLIVIA_RESOURCES}]
