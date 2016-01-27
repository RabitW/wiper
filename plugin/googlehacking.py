#!/usr/bin/env python
#-*- coding: UTF-8 -*-

'''
Wiper, an assistant tool for web penetration test.
Copyright (c) 2014-2015 alpha1e0
See the file COPYING for copying detail
'''

import re
import itertools

from plugin.lib.plugin import Plugin, PluginError
from plugin.lib.searchengine import Query
from model.model import Host

class GoogleHackingPlugin(Plugin):
    def __init__(self, size=200):
        super(GoogleHackingPlugin, self).__init__()
        self.size = size
        self.urlPattern = re.compile(r"^(?:http(?:s)?\://)?((?:[-0-9a-zA-Z_]+\.)+(?:[-0-9a-zA-Z_]+))")

    def handle(self, data):
        if not isinstance(data, Host):
            self.put(data)
        else:
            try:
                domain = data.url[4:] if data.url.startswith("www.") else data.url
            except AttributeError:
                raise PluginError("GoogleHackingPlugin plugin got an invalid model")
            query = Query(site=domain) | -Query(site="www."+domain)
            resultBaidu = query.doSearch(engine="baidu", size=10)
            resultBing = query.doSearch(engine="bing", size=10)

            urlSet = set()
            for line in itertools.chain(resultBaidu,resultBing):
                try:
                    url = self.urlPattern.match(line.url).groups()[0]
                except AttributeError:
                    continue
                else:
                    if url not in urlSet:
                        urlSet.add(url)
                        description = "Generated by googlehacking plugin.\r\n" + "href: " + line.url + "\r\n" + "description: " + line.brief
                        host = Host(title=line.title,url=url,description=description)
                        self.put(host)
