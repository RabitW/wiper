#!/usr/bin/env python
#-*- coding: UTF-8 -*-

'''
Wiper, an assistant tool for web penetration test.
Copyright (c) 2014-2015 alpha1e0
See the file COPYING for copying detail
'''

import os
import time

from thirdparty.dns import resolver, reversename, query
from thirdparty.dns.exception import DNSException
#from dns import resolver, reversename, query
#from dns.exception import DNSException

from config import CONF



class DnsResolver(object):
    '''
    Dns operation.
    The records format is [domain, value, type]
    '''
    def __init__(self, domain=None, timeout=None):
        self.domain = domain

        self.resolver = resolver.Resolver()
        self.resolver.nameservers = CONF.dns.servers
        self.resolver.timeout = timeout if timeout else CONF.dns.timeout

        self.axfr = query.xfr


    def domain2IP(self, domain=None):
        '''
        Parse domain to IP.
        '''
        domainToResolve = domain if domain else self.domain
        try:
            response = self.resolver.query(domainToResolve, "A")
        except DNSException:
            return None
        else:
            return response[0].to_text()
            #return [x.to_text for x in response]


    def IP2domain(self, ip):
        '''
        Parse IP to domain. The most dns server dose not support this operation.
        '''
        return reversename.from_address(ip)


    def getRecords(self, rtype, domain=None):
        '''
        Get dns records, records type supports "A", "CNAME", "NS", "MX", "SOA", "TXT"
        Example:
            dns.getRecords("A")
        '''
        if not rtype in ["A", "CNAME", "NS", "MX", "SOA", "TXT", "a", "cname", "ns", "mx", "soa", "txt"]:
            return []

        domainToResolve = domain if domain else self.domain
        try:
            response = self.resolver.query(domainToResolve, rtype)
        except DNSException:
            return []

        if not response:
            return []

        if rtype in ["MX","mx"]:
            return [[domainToResolve, line.to_text().rstrip(".").split()[-1], rtype] for line in response]
        return [[domainToResolve, line.to_text().rstrip("."), rtype] for line in response]


    def getZoneRecords(self, domain=None):
        '''
        Check and use dns zone transfer vulnerability. This function will traverse all the 'ns' server
        Usage:
            dnsresolver = DnsResolver('aaa.com')
            records = dnsresolver.getZoneRecords()
        '''
        domainToResolve = domain if domain else self.domain

        records = list()
        nsRecords = self.getRecords("NS", domainToResolve)
        for serverRecord in nsRecords:
            xfrHandler = self.axfr(serverRecord[1], domainToResolve)
            try:
                for response in xfrHandler:
                    topDomain = response.origin.to_text().rstrip(".")
                    for line in response.answer:
                        # A records
                        if line.rdtype == 1:
                            lineSplited = line.to_text().split()
                            if lineSplited[0] != "@":
                                subDomain = lineSplited[0] + "." + topDomain
                                ip = lineSplited[-1]
                                records.append([subDomain, ip, "A"])
                        # CNAME records
                        elif line.rdtype == 5:
                            lineSplited = line.to_text().split()
                            if lineSplited[0] != "@":
                                subDomain = lineSplited[0] + "." + topDomain
                                aliasName = lineSplited[-1]
                                records.append([subDomain, aliasName, "CNAME"])
            except:
                pass

        return records


    def getZoneRecords2(self, server, domain=None):
        '''
        Use the specified ns server, check and use dns zone transfer vulnerability.
        Usage:
            dnsresolver = DnsResolver('aaa.com')
            records = dnsresolver.getZoneRecords2()
        '''
        domainToResolve = domain if domain else self.domain

        records = list()

        xfrHandler = self.axfr(server, domainToResolve)

        try:
            for response in xfrHandler:
                topDomain = response.origin.to_text().rstrip(".")
                for line in response.answer:
                    # A records
                    if line.rdtype == 1:
                        lineSplited = line.to_text().split()
                        if lineSplited[0] != "@":
                            subDomain = lineSplited[0] + "." + topDomain
                            ip = lineSplited[-1]
                            records.append([subDomain, ip, "A"])
                    # CNAME records
                    elif line.rdtype == 5:
                        lineSplited = line.to_text().split()
                        subDomain = lineSplited[0] + "." + topDomain
                        if lineSplited[0] != "@":
                            aliasName = lineSplited[-1]
                            records.append([subDomain, aliasName, "CNAME"])
        except:
            pass

        return records


    def resolveAll(self, domain=None):
        domainToResolve = domain if domain else self.domain
        types = ["A", "CNAME", "NS", "MX", "SOA", "TXT"]
        records = list()

        for t in types:
            records += self.getRecords(t, domainToResolve)

        records += self.getZoneRecords(domainToResolve)

        return records


