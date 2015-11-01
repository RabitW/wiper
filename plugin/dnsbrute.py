#!/usr/bin/env python
#-*- coding: UTF-8 -*-

'''
Wiper, an assistant tool for web penetration test.
Copyright (c) 2014-2015 alpha1e0
See the file COPYING for copying detail
'''

import os
import socket
import re

#from config import RTD
from plugin.lib.dictparse import DictFileEnum
from plugin.lib.plugin import Plugin, PluginError
from plugin.lib.dnsresolve import DnsResolver
from model.model import Host
from config import RTD


class DnsBrute(Plugin):
	'''
	Use wordlist to bruteforce subdomain.
	'''
	def __init__(self, dictlist):
		super(DnsBrute, self).__init__()

		self.urlPattern = re.compile(r"^(?:http(?:s)?\://)?((?:[-0-9a-zA-Z_]+\.)+(?:[-0-9a-zA-Z_]+))")
		self.dictlist = [os.path.join("plugin","wordlist","dnsbrute",x) for x in dictlist]
		
		self.dns = DnsResolver()


	def checkDomain(self, domain):
#		try:
#			ip = socket.gethostbyname(domain)
#		except:
#			return False
#		return ip
		ips = self.dns.domain2IP(domain)
		if ips:
			return ips[0]


	def handle(self, data):
		if not isinstance(data, Host):
			self.put(data)
			return

		try:
			dataDomain = self.urlPattern.match(data.url).groups()[0].lower()
		except AttributeError:
			raise PluginError("dns brute plugin, domain format error")

		#partDoman示例：aaa.com partDomain为aaa，aaa.com.cn partDomain为aaa
		pos = dataDomain.rfind(".com.cn")
		if pos==-1: pos = dataDomain.rfind(".")
		partDomain = dataDomain if pos==-1 else dataDomain[0:pos]

		if dataDomain.startswith("www."):
			dataDomain = dataDomain[pos+4:]
		#RTD.log.debug(self.dictlist+self.projectID+dataDomain+partDomain)


		dlist = os.path.join("plugin","wordlist","toplevel.txt")
		for line in DictFileEnum(dlist):
			domain = partDomain + "." + line
			RTD.log.debug(domain)
			ip = self.checkDomain(domain)
			if ip:
				self.put(Host(url=domain, ip=ip))

		for dlist in self.dictlist:
			for line in DictFileEnum(dlist):
				domain = line + "." + dataDomain
				#RTD.log.debug(domain)
				ip = self.checkDomain(domain)
				if ip:
					self.put(Host(url=domain, ip=ip))



