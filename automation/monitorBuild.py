import os
from ftplib import FTP
import socket
import tarfile
import shutil
import datetime
import time
import logging
import sys
from post import *
from sctmwebservice import *
host = '10.204.16.2'
username ='test'
password = 'testtest'
buildPath =r'build/itis/5.0/MacOS/en'
#buildPath =r'/project/iTIS/resource/Test'
remotePath = r'/project/iTIS/resource/BuildForTest/'

global builds_num
builds_num = 0

logfile = logging.FileHandler("log.txt","w")
#logfile.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO,filename="log.txt"
,format='%(asctime)s\t%(levelname)s\t[%(module)s.%(funcName)s]\t%(message)s',datefmt='[%d/%b%Y %H:%M:%S]')
streamHandle = logging.StreamHandler(sys.stdout)
logging.getLogger().addHandler(streamHandle)

def loginFTP(buildPath):
	try:
		f =FTP(host)
	except (socket.errorTab,socket.gaierror),e:
		logging.error( "ERROR: can not reach %r"% host)
	try:
		f.login(username,password)
	except Exception as e:
		logging.error( "ERROR: can not login")
		f.quit()
		return
	logging.info( "Welcome: %s"%f.getwelcome())
	return f

def getBuild(f,buildPath,test=False):
    try:
        f.cwd(buildPath)
    except ftplib.error_perm:
        logging.error( "ERROR: can not CD to %r"%buildPath)
        f.quit()
        return
    logging.info( "***change to %r folder"% buildPath)
		# get the config file, modify it and then upload
    try:
        files = f.nlst()
        global builds_num
        print len(files),builds_num
        if len(files)==builds_num:
            logging.info( "no new builds in the server")
            return
        builds_num = len(files)
        folder = files[-1] if test else files[-2]
        fullPath = r"//"+host+r"/"+buildPath+r"/"+folder
        with open('build.txt','w')as  fp:
            fp.write(folder)
        print fullPath
        #print "3###",f.nlst(r"//10.204.16.2")
        image = 'iTIS_5.0_image.tar.gz'
        print f.nlst()
        print fullPath+"/"+image,os.path.isfile(fullPath+"/"+image)
        if not os.path.isfile(fullPath+"/"+image):
            time.sleep(600)

        tarobj = tarfile.open(fullPath+"/"+image,"r:gz")
        for targinfo in tarobj:
            if targinfo.name.find('Trend Micro')<>-1:
                tarobj.extract(targinfo.name,r"c:/temp/")
        local = r"c:/temp/image/Consumer_CD/Release"
        logging.info( "finish unzip package to %r"%local)
        tarobj.close()
        localbuild = os.listdir(local)

        for x in range(len(localbuild)):
            if localbuild[0].startswith('._'):
                del localbuild[0]
        return  local+"/"+localbuild[-1]

    except Exception as e :
		logging.error( e)
		return

def uploadBuild(f,local,remote):
    try:
        f.cwd(remotePath)
    except Exception as e:
        logging.error( "ERROR: can not CD to %r"%remotePath)
        f.quit()
        return
    logging.info( "***change to %r folder"% remotePath)

    try:
        fd = open(local,"rb")
        f.storbinary('STOR %s'%os.path.basename(local),fd)
        fd.close()
        logging.info( "new build %r is uploaded to %r"%(local,remote))
        ##  write bvt task to db

        buildPath = r"//10.204.16.2%s%s"%(remote,local.split('/')[-1])
        buildPath = buildPath.replace('/','\\')
        triggerBVT(buildPath)
        print "####"
        with open('build.txt','r')as  fp:
            r=fp.read()
        print "####",r
        addBuildNumber(r)
##        with open('buildTarget.txt','r')as fp:
##            with open('build.txt','r')as fp2:
##                if fp.read(4) == fp2.read(4):
##                    logging.info("new build founds, need trigger BVT")
##                    triggerBVT(buildPath)
##                else:
##                    logging.info("no need to trigger BVT")
        logging.info("trigger bvt test for build %s"%buildPath)

    except Exception as e:
        logging.error( "%s, ERROR: can not read file %r"%(e,local))
        os.unlink(local)
        return
    shutil.rmtree(r"c:/temp")



def  addBuildNumber(buildnumber):
    s = SCTM("http://10.28.9.23:8080/sctmservice/rest","jim_wan_auto","Let'sgo!")
    s.login()
    print "login sctm successful"
    builds= s.getAllBuilds('iTIS','5.0')
    flag = False
    for each in builds:
       if buildnumber == each['name']:
           flag = True
           break
    if not flag:
        s.addBuild("iTIS",'5.0',buildnumber)
        print "add build number %s"%buildnumber
    else:
        print "%s already exist"%buildnumber



if __name__ == '__main__':
    while 1:
        logging.info( datetime.datetime.now())
        f=loginFTP(buildPath)
        build = getBuild(f,buildPath)
        if build:
            f=loginFTP(remotePath)
            uploadBuild(f,build,remotePath)
        time.sleep(600)