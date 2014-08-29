#-------------------------------------------------------------------------------
# Name:         webserviceUtil
# Purpose:
#
# Author:      limin
#
# Created:     05/06/2013
# Copyright:   (c) limin 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

'''
Notes:
This is a  module for requesting web service to interact with SCTM web service.
Each method will return a non-None value if your request are correct, otherwise
please check the ServerURL and the parameter to guarantee the resouce are existed
'''

import  urllib2, logging ,urllib , time,socket, types
import json

class SCTM(object):


    HEADFORMATER = 'application/json'
    ERRORCODE_SERVER = 500
    ERRORCODE_CLIENT = 404

    TESTDEFROLE_NORMAL = 'NORMAL' ##CLEANUP   SETUP
    TESTDEFROLE_CLEANUP = 'CLEANUP' ##CLEANUP   SETUP
    TESTDEFROLE_SETUP = 'SETUP' ##CLEANUP   SETUP

    EXECSERVER_STATE_ACTIVE = 1
    EXECSERVER_STATE_INACTIVE = 0
    EXECSERVER_STATE_FAILURE= 2



    def __init__(self, serverURL, username, password):
        self.server = str(serverURL)
        self.user = str(username)
        self.pwd = str(password)
        self.sessionid = 0

    def getServerURL(self):
        self.server = self.server.strip()
        if self.server.endswith('/'):
            return self.server.rstrip('/')
        else:
            return self.server



    def login(self):
        '''
        Logs on with a given username and password.
        The returned session identifier can be used in subsequent calls.
        It acts as a unique key.

        retun: void
        throws: SCTMException
        '''

        url = self.getServerURL() +'/user/sessionid'
        data = {'username':self.user,'password':self.pwd}
        data = urllib.urlencode(data)
        req = urllib2.Request(url, data)
        req.add_header('accept',self.HEADFORMATER)

        userLogin={}

        try:
            resp = urllib2.urlopen(req)
            userLogin = json.loads(resp.read())
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise SCTMException(self.ERRORCODE_CLIENT,'[404]Can\'t find the resource, please check server URL or username')
            else:
                raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception, e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not userLogin is None and userLogin.has_key('sessionid'):
            self.sessionid = userLogin['sessionid']
        elif userLogin is None:
            raise SCTMException(self.ERRORCODE_CLIENT,'Can not get sessionId with name('+self.user+')')
        elif not userLogin.has_key('sessionid'):
            raise SCTMException(self.ERRORCODE_CLIENT,'no key sessionid in the result entity')


    def __checkSession(self):
        '''
        refresh session id

        retun: void
        throws: SCTMException

        '''
        url = self.getServerURL() +'/app_module/modules?sessionid='+self.sessionid

        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        result = {}

        try:
            resp = urllib2.urlopen(req)
            result =  json.loads(resp.read())
        except urllib2.HTTPError, e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_CLIENT, e)

        false = 'false'

        if not result is None and result.has_key('result') and (result['result'] == false):
            self.login()
        elif result is None:
            raise SCTMException(self.ERRORCODE_CLIENT,'Can not get application modules, please make sure the sessionid is validate')
        elif not result.has_key('result'):
            raise SCTMException(self.ERRORCODE_CLIENT, 'no key named result, check the key is validate')



    def getExecDefinesByName(self, projectid, executionname):
        '''
        get executions with the special name in the project, the result is a array of 'executionDefine'
        the type of nodes contains execution defintions, folder and configurationsuit

        return: a array or None
        [{ u'execuName': u'pro Execution1', u'typeName': u'EXECUTIONDEFINITION', u'execuId': u'111116',  u'type': u'3'},
        { u'execuName': u'test', u'typeName': u'FOLDER', u'execuId': u'111765',  u'type': u'2'}]
        throws: SCTMException
        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')



        data = {'sessionid': self.sessionid, 'projectid': projectid,'name':executionname}
        data = urllib.urlencode(data)
        queryUrl = self.getServerURL() + '/execution/execdefs/by_name?'+data

        req = urllib2.Request(queryUrl)
        req.add_header('accept', self.HEADFORMATER)

        executions = []
        try:
            resp = urllib2.urlopen(req)
            executions = json.loads(resp.read())
        except urllib2.HTTPError, e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception, e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not executions is None and executions.has_key('executionDefineSimple'):
            if type(executions['executionDefineSimple']) is types.ListType:
                return executions['executionDefineSimple']
            elif type(executions['executionDefineSimple']) is types.DictType:
                return [executions['executionDefineSimple']]
            else:
                raise TypeError,'the result\'s type is not dict or list, can not convert it to list'

        elif executions is None:
            return None
        elif not executions.has_key('executionDefineSimple'):
            raise SCTMException(self.ERRORCODE_CLIENT,' No key named executionDefineSimple, check the key is validate.')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getChildExecDefineByParentId(self, projectid, parentid, isgetall):
        '''
        get direct child execution defines, not contains configuration, folder

        return None| a array of 'executionDefine'
        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(parentid) is types.StringType:
            parentid = parentid.strip()
            if parentid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'parentid should not be empty')
            if not parentid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'parentid must be a mumber')

        s_isgetall = str(isgetall)
        s_isgetall = s_isgetall.strip()
        s_isgetall = s_isgetall.lower()
        if s_isgetall != 'true' and s_isgetall != 'false':
            raise SCTMException(self.ERRORCODE_CLIENT, 'the isgetall should be true or false')


        data = {'sessionid': self.sessionid, 'projectid': projectid,'parentid':parentid, 'isgetall':s_isgetall}
        data = urllib.urlencode(data)
        queryUrl = self.getServerURL() + '/execution/childnodes/by_parent_nodeid?'+data

        req = urllib2.Request(queryUrl)
        req.add_header('accept', self.HEADFORMATER)
        executions = []
        try:
            resp = urllib2.urlopen(req)
            executions = json.loads(resp.read())
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception, e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not executions is None and executions.has_key('executionDefine'):
            return executions['executionDefine']
        elif executions is None:
            return None
        elif not executions.has_key('executionDefine'):
            raise SCTMException(self.ERRORCODE_CLIENT,' No key named executionDefine, check the key is validate.')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')


    def getAssignedTestDefsByExecId(self,projectid, executionid, def_param_name='DefineID'):
        '''
        get assigined testdefines according to executionid and parameter name

        return None or a array of 'testDefine'
        [{u'paramValue': u'', u'defineId': u'690817', u'defineName': u'DataSet test', u'roleInExecution': u'NORMAL'},
         {u'paramValue': u'', u'defineId': u'1403709', u'defineName': u'P4checkoutest', u'roleInExecution': u'NORMAL'},
          {u'paramValue': u'', u'defineId': u'1919812', u'defineName': u'case1', u'roleInExecution': u'NORMAL'},
           {u'paramValue': u'', u'defineId': u'1919813', u'defineName': u'wsh_case2', u'roleInExecution': u'NORMAL'},
           {u'paramValue': u'', u'defineId': u'1919814', u'defineName': u'Pro Test Definition', u'roleInExecution': u'NORMAL'}]

        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(executionid) is types.IntType:
            executionid = str(executionid)

        if type(def_param_name) is types.StringType:
            def_param_name = def_param_name.strip()




        data = {'sessionid':self.sessionid, 'projectid':projectid,'def_param_name': def_param_name}
        data = urllib.urlencode(data)
        if type(executionid) is types.StringType:
            executionid = executionid.strip()
        url = self.getServerURL() +'/execution/execdef/'+executionid+'/testdefs?'+data
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        testDefine = []
        try:
            resp = urllib2.urlopen(req)
            testDefine =  json.loads(resp.read())
        except urllib2.HTTPError, e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception, e:
            raise SCTMException(self.ERRORCODE_SERVER, e)


        if not testDefine is None and testDefine.has_key('testDefine'):
            return testDefine['testDefine']
        elif testDefine is None:
            return None
        elif not testDefine.has_key('testDefine'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named testDefine')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')


    def startExecution(self,projectid, executionid, version, build,execservernameorip,port=19124):
        '''
        run a execution time stamp(ExecutionTimeStamp)
        return a time stamp
        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(port) is types.StringType:
            port = port.strip()
            if port != '' and not port.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')




        data = {'sessionid':self.sessionid,'projectid':projectid,'executionid':executionid,'version':version, 'build':build,'hostname':execservernameorip, 'port': port}
        data = urllib.urlencode(data)
        url = self.getServerURL() +'/execution/execution_run'
        req = urllib2.Request(url,data)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result = resp.read()
            if result == '':
                return None
            result =  json.loads(result)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())

        if not result is None and result.has_key('timestamp'):
            return result['timestamp']
        elif result is None:
            return None
        elif not result.has_key('timestamp'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named timestamp')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')


    def queryExcutionRunState(self,projectid, executionid, timestamp, execserver, port=19124):
        '''
        get the running state of execution on specific execution server

        return running | finished
        '''
        self.__checkSession()
        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(port) is types.StringType:
            port = port.strip()
            if port != '' and not port.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'port must be a mumber')

        if type(timestamp) is types.StringType:
            timestamp = timestamp.strip()
            if timestamp == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'timestamp must should not be empty')
            if not timestamp.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'timestamp must be a mumber')



        data = {'sessionid':self.sessionid,'projectid':projectid,'executionid':executionid,'timestamp': timestamp,'hostname':execserver, 'port': port}
        data = urllib.urlencode(data)
        url = self.getServerURL() +'/execution/execution_run/state?'+data
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result = resp.read()
            if result == '':
                return None
            result =  json.loads(result)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not result is None and result.has_key('state'):
            return result['state']
        elif result is None:
            return None
        elif not result.has_key('state'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named state')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getExecServersByExecId(self, projectid,executionid):
        '''
        Get execution services according to execution id

        a dictionary list will be returned  like:
            [{u'executionId': u'111110', u'hostName': u'10.28.9.20', u'port': u'19124', u'isActive': u'true', u'state': u'1'}]

        '''
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(executionid) is types.IntType:
            executionid = str(executionid)


        params = {'executionId': executionid,'projectid':projectid, 'sessionid': self.sessionid}
        params = urllib.urlencode(params)
        url = self.getServerURL() + '/execution/execdef/'+executionid+'/exec_servers?'+params
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        execServers = []
        try:
            resp = urllib2.urlopen(req)
            execServers =  json.loads(resp.read())
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e)


        if not execServers is None and execServers.has_key('execServer'):
            return execServers['execServer']
        elif execServers is None:
            return None
        elif not execServers.has_key('execServer'):
            raise SCTMException(self.ERRORCODE_CLIENT,' No key named execServer, check the key is validate.')


    def addVersion(self,productname,versionname):
        '''
        add verion, make sure the productname is exist.
        return true | false
        '''
        self.__checkSession()
        params = {'sessionid': self.sessionid, 'productname':productname, 'versionname':versionname}
        params = urllib.urlencode(params)

        url = self.getServerURL() +'/product/version'
        req = urllib2.Request(url, params)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result = resp.read()
            result =  json.loads(result)
        except urllib2.HTTPError, e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not result is None and result.has_key('result'):
            return result['result']
        elif result is None:
            raise Exception, 'can not get the result of adding version'
        elif not result.has_key('result'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named result')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def addBuild(self, productname,versionname,buildname):
        '''
        add verion, make sure the productname is exist.
        return true | false
        '''
        if  type(versionname) is types.IntType:
            versionname = str(versionname)
        versionname = versionname.strip()
        if len(versionname) == 0:
            raise SCTMException(self.ERRORCODE_CLIENT, 'versionname should not be empty.')


        self.__checkSession()
        params = {'sessionid': self.sessionid,  'productname':productname, 'buildname':buildname}
        params = urllib.urlencode(params)

        versionname = urllib.quote(versionname)

        url = self.getServerURL() +'/product/version/'+versionname+'/build'

        req = urllib2.Request(url,params)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result =resp.read()
            result =  json.loads(result)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER,e)


        if not result is None and result.has_key('result'):
            return result['result']
        elif result is None:
            raise Exception, 'can not get the result of adding version'
        elif not result.has_key('result'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named result')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getAllProjects(self):
        '''
        Get all projects assigned to the logged in User

        return  array
        [{u'active': u'true', u'id': u'202', u'name': u'@ [Training] VSCAN 2.0'},
         {u'active': u'true', u'id': u'63', u'name': u'@ETSDemoProjectTest (copy)'},
        {u'active': u'true', u'id': u'390', u'name': u'@LargeProjectForTesting'}]

        throw: SCTMException
        '''
        self.__checkSession()

        params = {'sessionid':self.sessionid}
        params = urllib.urlencode(params)

        url = self.getServerURL() + '/project/list?'+params
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        proejects = []
        try:
            resp = urllib2.urlopen(req)
            proejects = resp.read()
            if proejects == '':
                return None
            proejects =  json.loads(proejects)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_CLIENT,e)


        if not proejects is None and proejects.has_key('projectEntity'):
             if type(proejects['projectEntity']) is types.ListType:
                return proejects['projectEntity']
             elif type(proejects['projectEntity']) is types.DictType:
                return [proejects['projectEntity']]

        elif proejects is None:
            return None
        elif not proejects.has_key('projectEntity'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named projectEntity')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getProjectsByName(self, projectname):
        '''
        Get all projects assigned to the logged in User
        return array
        [{u'active': u'true', u'id': u'49', u'name': u'@SCTM'}]

        throw SCTMException
        '''

        self.__checkSession()

        params = {'sessionid':self.sessionid, 'projectname':projectname}
        params = urllib.urlencode(params)

        url = self.getServerURL() +'/project/by_name?'+params
        req = urllib2.Request(url)
        req.add_header('accept','application/json')

        proejects = []
        try:
            resp = urllib2.urlopen(req)
            proejects = resp.read()
            if proejects == '':
                return None
            proejects =  json.loads(proejects)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_CLIENT,e)


        if not proejects is None and proejects.has_key('projectEntity'):
             if type(proejects['projectEntity']) is types.ListType:
                return proejects['projectEntity']
             elif type(proejects['projectEntity']) is types.DictType:
                return [proejects['projectEntity']]

        elif proejects is None:
            return None
        elif not proejects.has_key('projectEntity'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named projectEntity')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')


    def __queryExcutionRunStateByHandle(self,projectid, executionid, timestamp):
        '''
        get the running state of execution by execution handle

        return None | finished
        '''
        self.__checkSession()
        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(timestamp) is types.StringType:
            timestamp = timestamp.strip()
            if timestamp == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'timestamp must should not be empty')
            if not timestamp.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'timestamp must be a mumber')


        data = {'sessionid':self.sessionid,'projectid':projectid,'executionid':executionid,'timestamp': timestamp}
        data = urllib.urlencode(data)
        url = self.getServerURL() +'/execution/execution_run/state_by_handle?'+data
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result = resp.read()
            if result == '':
                return None
            result =  json.loads(result)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e)

        if not result is None and result.has_key('state'):
            return result['state']
        elif result is None:
            return None
        elif not result.has_key('state'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named state')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def startExecutionSync(self,projectid, executionid, version, build,timeout, execservernameorip,port=19124 ):
        '''
        trigger an execution and wait until finished. The unit of 'timeout' is minute.
        return state[finished| None]
        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(port) is types.StringType:
            port = port.strip()
            if port != '' and not port.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'port must be a mumber')

        if type(timeout) is types.StringType:
            timeout = timeout.strip()
            if timeout == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'timeout must should not be empty')
            if not timeout.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'timeout must be a mumber')


        data = {'sessionid':self.sessionid,'projectid':projectid,'executionid':executionid,'version':version, 'build':build,'hostname':execservernameorip, 'port': port, 'timeout':timeout}
        data = urllib.urlencode(data)

        url = self.getServerURL() +'/execution/execution_run_sync'
        req = urllib2.Request(url,data)
        req.add_header('accept',self.HEADFORMATER)

        result = {}
        try:
            resp = urllib2.urlopen(req)
            result = resp.read()
            if result == '':
                return None
            result =  json.loads(result)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER, e.read())

        if not result is None and result.has_key('state'):
            return result['state']
        elif result is None:
            return None
        elif not result.has_key('state'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named state')
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getAllVersion(self, productname):
        '''
        Get all projects assigned to the logged in User
        return array or None
        [{name: build1, product: productname},
            {name:build2,product:product}]}


        throw SCTMException
        '''

        self.__checkSession()

        params = {'sessionid':self.sessionid, 'productname':productname}
        params = urllib.urlencode(params)

        url = self.getServerURL() +'/product/version/by_product?'+params
        req = urllib2.Request(url)
        req.add_header('accept','application/json')

        version = []
        try:
            resp = urllib2.urlopen(req)
            version =resp.read()
            if version == '':
                return None
            else:
                version = json.loads(version)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_CLIENT,e)


        if not version is None and version.has_key('version'):
             if type(version['version']) is types.ListType:
                return version['version']
             elif type(version['version']) is types.DictType:
                return [version['vesrion']]

        elif version is None:
            return None
        elif not version.has_key('version'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named version')

    def getVersionNameByExecId(self,projectid, executionid):
        '''
        get assigined version's name of execution defition node

        return versionname or null if the execution is read build

        '''
        ##check session
        self.__checkSession()

        if type(projectid) is types.StringType:
            projectid = projectid.strip()
            if projectid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid should not be empty')
            if not projectid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'projectid must be a mumber')


        if type(executionid) is types.StringType:
            executionid = executionid.strip()
            if executionid == '':
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid should not be empty')
            if not executionid.isdigit():
                raise SCTMException(self.ERRORCODE_CLIENT, 'executionid must be a mumber')

        if type(executionid) is types.IntType:
            executionid = str(executionid)



        data = {'sessionid':self.sessionid, 'projectid':projectid,'nodeid': executionid}
        data = urllib.urlencode(data)

        url = self.getServerURL() +'/execution/execdefs/by_id?'+data
        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        version = {}
        try:
            resp = urllib2.urlopen(req)
            version = resp.read()
        except urllib2.HTTPError, e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception, e:
            raise SCTMException(self.ERRORCODE_SERVER, e)


        if not version is None and version != '':
            return version
        elif version == '':
            return None
        else:
            raise SCTMException(self.ERRORCODE_CLIENT, 'unexpected error happend')

    def getAllBuilds(self, productname,versionname):
        '''
        get all builds according to version name
        return an array or None
        [{name: build1, product: productname, version: versionname},
        {name:build2,product:product,version:versionname}]

        '''
        self.__checkSession()
        params = {'sessionid': self.sessionid,  'productname':productname}
        params = urllib.urlencode(params)

        if type(versionname) is types.IntType:
            versionname = str(versionname)


        versionname = urllib.quote(versionname)

        url = self.getServerURL() +'/product/version/'+versionname+'/build/by_version?'+params

        req = urllib2.Request(url)
        req.add_header('accept',self.HEADFORMATER)

        builds = []
        try:
            resp = urllib2.urlopen(req)
            builds = resp.read()
            if builds == '':
                return None
            else:
                builds =  json.loads(builds)
        except urllib2.HTTPError,e:
            raise SCTMException(self.ERRORCODE_SERVER,e.read())
        except Exception,e:
            raise SCTMException(self.ERRORCODE_SERVER,e)

        if not builds is None and builds.has_key('build'):
             if type(builds['build']) is types.ListType:
                return builds['build']
             elif type(builds['build']) is types.DictType:
                return [builds['build']]


        if builds is None:
            return None
        elif not builds.has_key('build'):
            raise SCTMException(self.ERRORCODE_CLIENT,'No key named build')



class SCTMException(Exception):
    def __init__(self, code, msg ):
        self.code = code
        self.msg = msg


    def __str__(self):
        return 'Error %s: %s' % (self.code, self.msg)








