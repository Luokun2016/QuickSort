# -*- coding: UTF-8 -*-
import win32serviceutil   
import win32service   
import win32event   

import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import sys, os
import subprocess
import json
import httplib
import socket
  
class PythonService(win32serviceutil.ServiceFramework):   
    """ 
    Usage: 'PythonService.py [options] install|update|remove|start [...]|stop|restart [...]|debug [...]' 
    Options for 'install' and 'update' commands only: 
     --username domain\username : The Username the service is to run under 
     --password password : The password for the username 
     --startup [manual|auto|disabled|delayed] : How the service starts, default = manual 
     --interactive : Allow the service to interact with the desktop. 
     --perfmonini file: .ini file to use for registering performance monitor data 
     --perfmondll file: .dll file to use when querying the service for 
       performance data, default = perfmondata.dll 
    Options for 'start' and 'stop' commands only: 
     --wait seconds: Wait for the service to actually start or stop. 
                     If you specify --wait with the 'stop' option, the service 
                     and all dependent services will be stopped, each waiting 
                     the specified period. 
    """  
    #server name  
    _svc_name_ = "PythonService"  
    #service display name  
    _svc_display_name_ = "Topsec Python Service"  
    #service description 
    _svc_description_ = "Topsec Python service."  
  
    def __init__(self, args):   
        win32serviceutil.ServiceFramework.__init__(self, args)   
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)  
        self.logger = self._getLogger()  
        self.isAlive = True  
          
    def _getLogger(self):  
        import logging  
        import os  
        import inspect  
          
        logger = logging.getLogger('[PythonService]')  
          
        this_file = inspect.getfile(inspect.currentframe())  
        dirpath = os.path.abspath(os.path.dirname(this_file))  
        handler = logging.FileHandler(os.path.join(dirpath, "service.log"))  
          
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')  
        handler.setFormatter(formatter)  
          
        logger.addHandler(handler)  
        logger.setLevel(logging.INFO)  
          
        return logger  
        
    def SvcDoRun(self):  
        import time
        import os
        self.logger.error("svc do run....")

        ip = self._getIp()
        self.logger.info("Server IP is %s." %ip)
        mac = self._getMac()
        self.logger.info("Server Mac is %s." %mac)
        macs = mac.split(",")
        mac1 = macs[0]
        mac2 = ''
        if len(macs) > 1:
            mac2 = macs[1]
        
        conn = httplib.HTTPConnection('192.168.122.1', 8000)
        conn.request("POST", "/vmconfig/%s/%s/" %(ip, mac2))
        resp = conn.getresponse()
        data = resp.read()
        self.logger.info("Server data is %s." %data)
        conn.close()
        dts = json.loads(data)
        cmd = 'netsh interface ip set address name="local_address2" source=static addr=%s mask=255.255.255.0 gateway=192.168.1.1 gwmetric=0' % dts["Ip"]
        exccmd = cmd.decode('UTF-8').encode('gbk')
        result = os.system(exccmd)
        self.logger.info("response data is %s." %data)
        # cmd = 'netsh interface ip set address name="local_address2" source=static addr=192.168.1.102 mask=255.255.255.0 gateway=192.168.1.1 gwmetric=0'
        # exccmd = cmd.decode('UTF-8').encode('gbk')
        # result = os.system(exccmd)
        #while self.isAlive:  
        #    self.logger.error("I am alive.")  
        #    time.sleep(1)  
        # wait service to stop  
        #win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE) 
    def _getIp(self):
        ip=""
        s=None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('192.169.1.1', 80))
            ip=s.getsockname()[0]
        except:
            self.logger.error("Server get Ip failed.")
        finally:
            s.close()
        return ip
        
    def _getMac(self):
        result = ""
        mac = ""
        if sys.platform == "win32":
            for line in os.popen("ipconfig /all"):
                #print line.lstrip()
                #line = line.decode('gbk').encode('utf-8')
                #if line.lstrip().startswith("ŒÔ¿Ìµÿ÷∑"):
                if line.lstrip().startswith("Physical Address"):
                    #print (line)
                    mac = line.split(":")[1].strip().replace("-", ":")
                    if result != "":
                        result += "," + mac
                    else:
                        result = mac
                    #print(mac)
        else:
            for line in os.popen("ifconfig -a"):
                if 'Ether' in line:
                    mac = line.split()[4]
                    if result != "":
                        result += "," + mac
                    else:
                        result = mac
        return result 
              
    def SvcStop(self):   
        # notify SCM to stop service process   
        self.logger.error("svc do stop....")  
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)   
        # set event  
        win32event.SetEvent(self.hWaitStop)   
        #self.isAlive = False  
  
if __name__=='__main__':   
    win32serviceutil.HandleCommandLine(PythonService)  