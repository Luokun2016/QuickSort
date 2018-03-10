#!/usr/bin/python
# -*- coding: utf-8 -*-
# 日志管理
'''
	* 目标：
		* 日志可输出到Console及文件
		* 日志文件大小有限制，个数也有限制，循环使用
		* 未实现：可定义日志产生者name(X)，自动打印调用者名字(X)		
		* 线程安全
		* 使用者可简易使用
	* 使用：
		* from xlogging import xlogger
		* xlogger.info(".................")
		* xlogger.debug("hello %s" % 'world')
		* xlogger.debug("hello %s", 'world')
	* 说明：
		* 默认值：日志文件大小为1M，最多5个，以.N为后缀
		* 全局使用同一个logger，不同使用者不再定义logger，日志产生者名字自己输
		* 使用者不直接创建__xlogger对象
		* 未采用如下方式：每个使用自己getLogger("NEWNAME")，如果
'''
import os
import sys
import logging
import logging.handlers
import inspect
import time

def get_caller(obj = None):
	'''
		* 返回调用者类名及方法
		* 如果obj为None，则不显示类名
	'''
	if obj : 
		return '[%s:%s]' % (obj.__class__.__name__, inspect.currentframe().f_back.f_code.co_name)
	else:
		return '[%s]' % inspect.currentframe().f_back.f_code.co_name

_F = get_caller
_ = get_caller

class __xlogger():
	def __init__(self, filename=None):
		'''
			* 初始化日志
			* 如果filename不为空，则使用该文件
			* 如果filename为空，则使用__main__.__file__
			* http://stackoverflow.com/questions/606561/how-to-get-filename-of-the-main-module-in-python
		'''
		strtime = time.strftime('%Y%m%d%H%M%S')
		if filename == None:
			#import __main__
			#basename = os.path.basename(__main__.__file__)  if hasattr(__main__, '__file__')  else "xlogger"
			basename = '/tmp/xlogger_%s' % strtime
			filename = os.path.splitext(basename)[0] + ".log"
		#formatter = logging.Formatter('[%(asctime)s] %(module)s.%(funcName)s|%(levelname)s: %(message)s')
		self.formatter = logging.Formatter(fmt = '[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
		self.logger = logging.getLogger('main')
		self.logger.setLevel(logging.DEBUG)

		console_handler = logging.StreamHandler()
		file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1024*1024, backupCount=5)
		console_handler.setFormatter(self.formatter)
		console_handler.setLevel(logging.DEBUG)
		file_handler.setFormatter(self.formatter)
		file_handler.setLevel(logging.DEBUG)
		self.logger.addHandler(console_handler)
		self.logger.addHandler(file_handler)
		self.file_handler = file_handler
		self._filename = filename

		self.logger.info('====start===>%s' % filename)

	def __del__(self):
		'''
			* 关闭日志
		'''
		self.logger.info('============= ended =============')

	def get_inst(self):
		'''
			* 获得xlogger象
		'''
		return self

	def get_logger(self):
		'''
			* 获得logging对象
		'''
		return self.logger

	def __debug(self, msg, *args, **kwargs):
		'''
			* 未能正确工作
			* 打印调试信息，目的为自己添加调用者名字
		'''
		caller = inspect.currentframe().f_back.f_code.co_name
		kwargs.update({'name': caller})
		self.logger.debug(msg, args, kwargs)
	def change_log_dir(self,new_dir):
		#strtime = time.strftime('%Y%m%d%H%M%S')
		basename = os.path.basename(self._filename)
		filename = os.path.join(new_dir, basename)
		self.logger.removeHandler(self.file_handler)
		os.system('cp -r %s* %s' % (self._filename, new_dir))
		os.system('rm -f %s*' % self._filename)
		#filename = '%s/xlogger_%s.log' % ( new_dir, strtime) 
		file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1024*1024, backupCount=5)
		file_handler.setFormatter(self.formatter)
		self.logger.addHandler(file_handler)
		self.file_handler = file_handler
		self._filename = filename
		self.logger.info('====start===>%s' % filename)

def change_log_dir(new_dir):
	__xl.change_log_dir(new_dir)

# 以下模块代码只会在第一次import时执行
__xl = __xlogger()
xlogger = __xl.get_logger()
# 测试代码
if __name__ == "__main__":
	xlogger.debug("...............")
