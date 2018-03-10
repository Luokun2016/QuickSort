#-*- coding: utf-8 -*-
import threading
import Queue
import time
from xlogging import xlogger

class vmManager(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.RequestList = Queue.Queue()
		self.IsUsing = False
		self._isExist = threading.Event()
		self.start()

	def run(self):
		i=0
		while not self._isExist.isSet():
			dom = self.RequestList.get()
			xlogger.info("vmMgr is running!!!!!!!!!!!!!!!!!!!!")
			xlogger.info(dom)
			dom.create()
			time.sleep(3)
			i=i+1
			if i>200:
				break
	def stop(self):
		self._isExist.set()

vmMgr = vmManager()
# vmMgr.isDaemon(True)
