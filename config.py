PREFIX_CHECKER_DEBUG = False
AS_EXPLORER_DEBUG = True
TRAFFMON_DEBUG = True


#####################BRAZIL############################
#CABLE_SANTA_FE_FILTER = {"name": "Cable Santa Fe", "interface": "dummy", "resources": {"uplinks": {"query":{"filter": "out dst mac c4:ad:34:ea:47:11 or out dst mac c4:ad:34:ea:47:47 or out dst mac c4:ad:34:49:b9:0d or out dst mac ac:1f:6b:a5:89:24 or out dst mac 02:2f:7e:ed:9d:00", "stattype": 8}}, "as": {"query":{"filter": "out dst mac c4:ad:34:ea:47:11 or out dst mac c4:ad:34:ea:47:47 or out dst mac c4:ad:34:49:b9:0d or out dst mac ac:1f:6b:a5:89:24 or out dst mac 02:2f:7e:ed:9d:00", "stattype": 11}}}}
BRAZIL_LUMEN= {"name": "Brazil Lumen", "interface": "17", "resources": {"as": {"query":{"filter": "in if 17", "stattype": 12}}}}
BRAZIL_IX= {"name": "Brazil IX", "interface": "30", "resources": {"as": {"query":{"filter": "in if 30", "stattype": 12}}}}

BRAZIL_CUSTOMERS = [BRAZIL_LUMEN, BRAZIL_IX]

IPTP_PERU = {"name": "IPTP Peru DIA customers", "match": "263681"}
BERNARDO = {"name": "Bernardo", "match": "270007"}
ECONOCABLE = {"name": "Econocable", "match": "267749"}
FIBERTEL = {"name": "Fibertel", "match": "266732"}
MEGA_ANDINA = {"name": "Mega Andina", "match": "269826"}
CONEX = {"name": "Conex", "match": "269975"}

BRAZIL_AS_LIST = [IPTP_PERU, BERNARDO, ECONOCABLE, FIBERTEL, MEGA_ANDINA, CONEX]
BRAZIL_RESOURCES = {"as": BRAZIL_AS_LIST}


#####################PERU############################

BERNARDO_FILTER = {"name": "Bernardo", "interface": "140", "resources": {"uplinks": {"query":{"filter": "out if 140", "stattype": 8}}, "as": {"query":{"filter": "out if 140", "stattype": 11}}}}
BERNARDO2_FILTER = {"name": "Bernardo 2", "interface": "150", "resources": {"uplinks": {"query":{"filter": "out if 150", "stattype": 8}}, "as": {"query":{"filter": "out if 150", "stattype": 11}}}}
#CABLE_SANTA_FE_FILTER = {"name": "Cable Santa Fe", "interface": "69", "resources": {"uplinks": {"query":{"filter": "out if 69", "stattype": 8}}, "as": {"query":{"filter": "out if 69", "stattype": 11}}}}
MEGA_ANDINA_FILTER = {"name": "Mega Andina", "interface": "102", "resources": {"uplinks": {"query":{"filter": "out if 102", "stattype": 8}}, "as": {"query":{"filter": "out if 102", "stattype": 11}}}}
ECONOCABLE_FILTER = {"name": "Econocable", "interface": "130", "resources": {"uplinks": {"query":{"filter": "out if 130", "stattype": 8}}, "as": {"query":{"filter": "out if 130", "stattype": 11}}}}
#GGC_GOOGLE_DOWNLINK_FILTER = {"name": "GGC Google DOWN", "interface": "164", "resources": {"uplinks": {"query":{"filter": "out if 164", "stattype": 8}}, "as": {"query":{"filter": "out if 164", "stattype": 11}}}}
GGC_GOOGLE_DOWNLINK_FILTER = {"name": "GGC Google DOWN", "interface": "166", "resources": {"uplinks": {"query":{"filter": "out if 66 and dst net 45.236.173.97/27", "stattype": 8}}, "as": {"query":{"filter": "out if 66 and dst net 45.236.173.97/27", "stattype": 11}}}}
CIAL_FILTER = {"name": "Cial", "interface": "121", "resources": {"uplinks": {"query":{"filter": "out if 121", "stattype": 8}}, "as": {"query":{"filter": "out if 121", "stattype": 11}}}}

#PERU_CUSTOMERS = [ECONOCABLE_FILTER, BERNARDO_FILTER, BERNARDO2_FILTER, CABLE_SANTA_FE_FILTER, MEGA_ANDINA_FILTER, GGC_GOOGLE_DOWNLINK_FILTER]
PERU_CUSTOMERS = [ECONOCABLE_FILTER, BERNARDO_FILTER, BERNARDO2_FILTER, MEGA_ANDINA_FILTER, GGC_GOOGLE_DOWNLINK_FILTER]

WAVE1_FILTER = {"name": "WAVE 1", "match": "157"}
WAVE2_FILTER = {"name": "WAVE 2", "match": "159"}
HSIP_FILTER =  {"name": "HSIP", "match": "168"}
FACEBOOK1_FILTER =  {"name": "FACEBOOK PNI 1", "match": "161", "check": True, "assoc_as": "32934"} # For some reason facebook only shows one direction
FACEBOOK2_FILTER =  {"name": "FACEBOOK PNI 2", "match": "162", "check": True, "assoc_as": "32934"} # on nfsendump, clarify
GGC_GOOGLE_FILTER = {"name": "GGC Google", "match": "164", "check": True}

#CACHES = [FACEBOOK1_FILTER, FACEBOOK2_FILTER, GGC_GOOGLE_FILTER]
CACHES = [FACEBOOK1_FILTER, FACEBOOK2_FILTER]

PERU_UPLINKS = [WAVE1_FILTER, WAVE2_FILTER, HSIP_FILTER] + CACHES

GOOGLE = {"name": "Google", 'match':"15169"}
FACEBOOK = {"name": "Facebok", 'match':"32934"}
AKAMAI = {"name": "Akamai", 'match':"20940"}
NETFLIX = {"name": "Netflix", 'match':"2906"}
TELEFONICA = {"name": "Telefonica", 'match':"6147", "priority": 1}
AMAZON = {"name": "Amazon", 'match':"16509"}
YACHAY = {"name": "Yachay", 'match':"3132", "priority": 1}
INTERNEXA = {"name": "Internexa", 'match':"28032", "priority": 1}
LEVEL3 = {"name": "Level 3", 'match':"3356", "priority": 1}
CDN77 = {"name": "CDN77", 'match':"60068"}
EDGEUNO = {"name": "EDGEUNO", 'match':"7195"}
FASTLY = {"name": "Fastly", 'match':"54113"}
ORACLE = {"name": "ORACLE", 'match':"31898"}
JUSTINTV = {"name": "Twitch", 'match':"46489"}
CLOUDFLARE = {"name": "Cloudflare", 'match':"13335"}
ROBLOX = {"name": "Roblox", 'match':"22697"}
HIGHWINDS = {"name": "Highwinds", 'match':"20446"}
MEDIAFIRE = {"name": "Mediafire", 'match':"46179"}
LLNW = {"name": "Limelight", 'match':"22822"}
ZNET = {"name": "Zenlayer", 'match':"21859"}
CACHENETWORKS = {"name": "Cache Networks", 'match':"30081"}
GCORE = {"name": "GCORE", 'match':"199524"}

#AS_LIST = [GOOGLE, FACEBOOK, AKAMAI, NETFLIX, TELEFONICA, AMAZON, YACHAY, INTERNEXA]
AS_LIST = [GOOGLE, FACEBOOK, AKAMAI, NETFLIX, TELEFONICA, AMAZON, YACHAY, INTERNEXA,
		   LEVEL3, CDN77, EDGEUNO, FASTLY, ORACLE, JUSTINTV, CLOUDFLARE, ROBLOX, HIGHWINDS, MEDIAFIRE, LLNW, ZNET, CACHENETWORKS, GCORE]
#AS_LIST = [GOOGLE, LEVEL3]
#AS_LIST = [AKAMAI, TELEFONICA]
#AS_LIST = [ROBLOX]
#AS_LIST = [ZNET]

PERU_RESOURCES = {"uplinks": PERU_UPLINKS, "as": AS_LIST}

GGC_GOOGLE_EXTRA_RESOURCE = {"name": "GGC Google","resource_type": "uplinks", "query": {"filter": "in if 66 and src net 45.236.173.97/27", "stattype": 9}}

PERU_EXTRA_RESOURCES = [GGC_GOOGLE_EXTRA_RESOURCE]
#####################PERU DOWN ############################
HSIP_DOWN_FILTER = {"name": "HSIP", "interface": "168", "resources": {"as_down_src": {"query":{"filter": "in if 168", "stattype": 11}}}}

PERU_DOWN_INTERFACES = [HSIP_DOWN_FILTER]

PERU_DOWN_RESOURCES = {"as_down_src": AS_LIST}
#####################BOLIVIA############################
"""
SIRIO_FILTER = {"name": "SIRIO", "interface": "87", "resources": {"as": {"query":{"filter": "out if 87", "stattype": 11}}}}
MEGALINK_FILTER = {"name": "Megalink", "interface": "92", "resources": {"as": {"query":{"filter": "out if 92", "stattype": 11}}}}
FIBERTEL_FILTER = {"name": "Fibertel", "interface": "119", "resources": {"as": {"query":{"filter": "out if 119", "stattype": 11}}}}

BOLIVIA_CUSTOMERS = [SIRIO_FILTER, MEGALINK_FILTER, FIBERTEL_FILTER]
BOLIVIA_RESOURCES = {"as": AS_LIST}
"""

#COUNTRIES = [{"name": "Peru", "router": "r0-l3-lim-pe", "customers": PERU_CUSTOMERS, "resources": PERU_RESOURCES},
COUNTRIES = [
			 {"name": "Peru", "router": "r0-l3-lim-pe", "customers": PERU_CUSTOMERS, "resources": PERU_RESOURCES, "extra_resources": PERU_EXTRA_RESOURCES},
			 {"name": "Peru DOWN", "router": "r0-l3-lim-pe", "customers": PERU_DOWN_INTERFACES, "resources": PERU_DOWN_RESOURCES},
             #{"name": "Peru amtel", "router": "r0-sql-lim-pe", "customers": BOLIVIA_CUSTOMERS, "resources": BOLIVIA_RESOURCES},
             {"name": "Brazil", "router": "r0-203-sp3", "customers": BRAZIL_CUSTOMERS, "resources": BRAZIL_RESOURCES},
             #{"name": "Bolivia", "router": "r0-sql-lim-pe", "customers": BOLIVIA_CUSTOMERS, "resources": BOLIVIA_RESOURCES}
             ]


for country in COUNTRIES:
    for customer in country["customers"]:
        #del customer["resources"]["as"]
        for resource, resource_data in customer["resources"].items():
            if resource == "as":
                resource_data["query"]["topN"] = 1
