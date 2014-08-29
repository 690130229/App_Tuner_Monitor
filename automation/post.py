#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jim_wan
#
# Created:     16/12/2013
# Copyright:   (c) jim_wan 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

#!/usr/bin/python
#coding=utf-8

import urllib
import urllib2
import logging

def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    #enable cookie
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()

def triggerBVT(buildPath):
    posturl = "http://10.204.210.160:8000/ci/bvt/"
    data = {'user':'jim_wan','task_template_id':27,'taskName':'iTISBVT',
    'buildPath':buildPath
    }
##    logging.info("#####")
    try:
       post(posturl, data)
    except Exception as e:
        logging.info("hhhh %s"%e)

if __name__ == '__main__':
    triggerBVT()

