

#from plugin.lib.dnsresolve import DnsResolver#

#dns = DnsResolver()#

##response = dns.getRecords("ns","www.baidu.com")
##response = dns.getRecords("ns","baidu.com")
##response = dns.getZoneRecords("thinksns.com")#

##types = ["A", "CNAME", "NS", "MX", "SOA", "TXT"]
##response = dns.getRecords("ns","baidu.com")
##response = dns.resolveAll("baidu.com")
#response = dns.domain2IP("baidu.com")#
#

#print response

import config

log1 = config.Log("log1")
log2 = config.Log("log1")
log = config.Log("log1")

log.info(">>>>>>>>>>>>>>>>")