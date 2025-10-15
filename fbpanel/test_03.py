import ipwhois

ips = [
    "103.25.250.239",
    "103.25.251.219",
    "103.25.251.201",
    "103.25.251.198",
    "103.25.251.202",
    "103.25.251.193",
    "103.25.251.211",
    "103.25.248.196"
]

for ip in ips:
    try:
        obj = ipwhois.IPWhois(ip)
        res = obj.lookup_rdap()
        print(ip, "-", res['asn_description'])
    except Exception as e:
        print(ip, "- error:", e)
