from ipaddress import IPv4Network, IPv4Address

from nfsenutils import is_subnet

a = IPv4Network('192.168.0.0/16')
b = IPv4Network('192.168.0.0/24')
c = IPv4Network('1.168.1.0/24')

ip = IPv4Address('129.134.70.8')
in_list = [IPv4Network('129.134.0.0/16'), IPv4Network('129.134.70.0/24')]
ex_list = [IPv4Network('129.134.0.0/17')]

if (ip in in_list[0] or ip in in_list[1]) and ip not in ex_list[0]:
    print("MAGIC!. All went fine")
else:
    print(ip in in_list[0], "in net 1")
    print(ip in in_list[1], "in net 2")
    print(ip not in ex_list[0], "not in exnet")
    print("damn")
    #raise


assert not is_subnet(a, b)
assert is_subnet(b, a)
assert not is_subnet(a, c)
assert not is_subnet(b, c)
assert not is_subnet(c, a)

print("All test passed")

a = [True, False]
b = [True, False]
c = [True, False]


for A in a:
    for B in b:
        for C in c:
            result = (A and not B) or C
            print(A,B,C,"",result)

for A in a:
    for B in b:
        for C in c:
            result = (A or C) and ((not B) or C)
            print(A,B,C,"",result)

