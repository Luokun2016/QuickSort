# -*- coding: utf-8 -*-

import os
import commands
from xlogging import xlogger
import subprocess

def run(cmd, getoutput=True):
	xlogger.info(cmd)
	status = -1
	output = ''
	if getoutput:
		status, output = commands.getstatusoutput(cmd)
	else:
		status = os.system(cmd)
	if getoutput:
		xlogger.info(output)
	xlogger.info('-----------[%d]------------' % status)
	return status, output

def runProcess(cmd):
	xlogger.info(cmd)
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

	retcode = None
	while True:
		retcode = p.poll()
		if retcode is not None:
			break
		line = p.stdout.readline()
		xlogger.info(' %s-------------------------------' % line)
	line = p.stdout.read()
	xlogger.info(' %s-------------------------------' % line)
	xlogger.info('-------------[%d]-----------' % retcode)
	return retcode


