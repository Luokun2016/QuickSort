# -*- coding: UTF-8 -*-
'''
实现上传工具，删除工具，以及对工具的信息修改功能
'''

# Create your views here.
import sys
from sysmgr.models import *
from tsssite.server import ConnServer
from django.shortcuts import render_to_response
from Tools.models import Tool
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
from urllib import unquote,quote
import datetime
import json
import logging
from django.db.models import Q
import os
import re
from collections import namedtuple 
import profile

logger = logging.getLogger('mysite.log')
path='/home/adp/product/web/document/uploadtools/'
reload(sys)
sys.setdefaultencoding('UTF-8')
# 获取所有工具信息
def showtool(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	# if request.session['userroletype']==0:
	# 	return HttpResponseRedirect('/Login/')
	#获取所有信息         
	tools = Tool.objects.order_by('-id')
	#翻页参数设置
	toolselect=''
	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']
		#筛选匹配的字段
		tools=tools.filter(Q(toolname__icontains=querytext)|Q(toolmessage__icontains=querytext))
		toolselect=querytext
	if 'toolselected' in request.GET:
		tools= Tool.objects.order_by('-id')
		querytext = request.GET.get("toolselected")
		tools=tools.filter(Q(toolname__icontains=querytext)|Q(toolmessage__icontains=querytext))
		toolselect=querytext
	after_range_num=5
	befor_range_num=4
	try:
		page = int(request.GET.get("page",1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1
	paginator = Paginator(tools,10)
	try:
		t_list = paginator.page(page)
	except(EmptyPage,InvalidPage,PageNotAnInteger):
		t_list = paginator.page(paginator.num_pages)
	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:int(page)+befor_range_num]

	return render_to_response('templates/tool.html',{'toolselect':toolselect,'tool_list':t_list,'tools':tools,'page_range':page_range},context_instance=RequestContext(request))

# 上传文件存储方式
def uploadtool(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	errors = []
	if request.method == 'POST':
		
	    data=request.FILES["data"]
	    name = request.POST["name"];
	    # path =os.path.join( HERE , folder+'/')
	    if not os.path.exists(path):
	    	os.makedirs(path)
	    fullname=path+str(name)
        f=open(fullname, 'a+')   
        with f as info:
            for chunk in data.chunks():
                info.write(chunk)  
        f.close() 
	return HttpResponseRedirect('/tools/')

# 添加新工具方法
def addtool(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	errors = []
	if request.method == 'POST':
		#添加信息
		too = Tool(toolname=request.POST['toolname'], toolmessage=request.POST['toolmessage'],toolcreatetime=datetime.datetime.now(),toolinformation=request.POST['toolinformation'])
		getname=request.POST['toolfilename']
		too.toolfile = getname
		too.save()
	return HttpResponseRedirect('/tools/')


# 上传工具文件方法
def handle_uploaded_file(f,path):
	with open(path, 'a+') as info:
		for chunk in f.chunks():
			info.write(chunk)
	return f

# 删除工具方法
def deltool(request, did):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')  
	global logger
	try:
		did = int(did)
		too = Tool.objects.get(id=did)

		if too.toolfile:
			if not os.path.isdir(path):
				pass
			else:  
				# path =os.path.join(HERE , folder+'/')
				cmd = "rm -rf " + path + "'"+too.toolfile+"'"
				os.system(cmd)		
		too.delete()
	except ValueError:
		logger.error("tools")
		raise Http404()
	return HttpResponseRedirect('/tools/')


# 点击取消按钮删除已经上传的文件
def cancelupload(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data = {}
	if request.method == 'POST':
		file_name="'"+request.POST['toolfilename']+"'"
		# path =os.path.join( HERE , folder+'/')
		try:
			cmd = "rm -rf "+path+file_name
			os.system(cmd)
			data['result']=cmd
		except Exception, e:
			data['result']=1

	return HttpResponse(json.dumps(data))

# 编辑时获取当前工具现有信息
def toolinfo(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	to = ''
	if request.method == 'POST':
		try:
			toolid = request.POST['toolid']
			to = Tool.objects.get(id=toolid)
		except ValueError:
			logger.error("tools")
			raise Http404()
	data = {}
	data["toolid"] = to.id
	data["toolname"] = to.toolname
	data["toolmessage"] = to.toolmessage
	data["toolinformation"] = to.toolinformation
	data["toolfile"] = to.toolfile 
	return HttpResponse(json.dumps(data))

# 编辑工具更新信息方法
def edittool(request):
	global logger
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	errors = ''
	try:
		did = int(request.POST['toolid'])
		too = ''
		too = Tool.objects.get(id=did)
	except ValueError:
		logger.error("tools")
		raise Http404()
	if request.method == 'POST':
		# path =os.path.join( HERE , folder+'/')#获取文件保存路径
		#如果存在新的上传工具文件，则删除原文件，上传新文件
		new_fileneme=request.POST['toolfilename']
		#检查是否存在document文件夹，没有则新建
		if not os.path.isdir(path):
			comd = "mkdir "+path
			os.system(comd)
		#删除原文件		
		if new_fileneme:
			cmd = "rm -rf "+path+"'"+too.toolfile+"'"
			os.system(cmd)
			too.toolfile=new_fileneme

		#更改信息
		too.toolname=request.POST['toolname']
		too.toolmessage=request.POST['toolmessage1']
		too.toolinformation=request.POST['toolinformation1']
		too.toolcreatetime=datetime.datetime.now()
		too.save()
	tools= Tool.objects.order_by('-id')
	return HttpResponseRedirect('/tools/')

# 检测工具同名request方法
def namechecktool(request):
	global logger
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	judgedevname=0
	if request.method == 'POST':
		try:
			newtoolname = ''
			newtoolname = request.POST['toolname']
			judgedevname=namechecktoolfun(newtoolname,'')
		except ValueError:
			logger.error("tools")
			raise Http404()
	data = {}
	data['judgename']=judgedevname
	return HttpResponse(json.dumps(data))

# 检测文件同名request方法
def filechecktool(request):
	global logger
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	judgedevname=0
	if request.method == 'POST':
		try:
			newtoolname = ''
			newtoolfile=''
			newtoolname = request.POST['toolname']
			newtoolfile = request.POST['toolfilename']
			judgedevname=namechecktoolfun(newtoolname,newtoolfile)
			if judgedevname==0:
				if newtoolfile!=None:
					filenamecheckfun(newtoolfile)
		except ValueError:
			logger.error("tools")
			raise Http404()
		# re.search(u'^[a-zA-Z0-9\u4e00-\u9fa5（）——_!@#$<>《》？|=-]+$',newtoolname):
	data = {}
	data['judgename']=judgedevname
	return HttpResponse(json.dumps(data))


# 检测工具同名具体方法
def namechecktoolfun(newtoolname,newtoolfile):
	judgedevname=0
	tooltotal=Tool.objects.order_by('id')
	for to in tooltotal:
		if to.toolname == newtoolname:
			judgedevname=1
		if to.toolfile == newtoolfile:
			judgedevname=2
	return judgedevname

# 检测文件同名具体方法
def filenamecheckfun(fielname):
	# path =os.path.join( HERE , folder+'/')
	if not os.path.exists(path):
		return 0
	if fielname in os.listdir(path):
		cmd = "rm -rf " + path + "'"+fielname+"'"
		os.system(cmd)	
		return 0
	else:
		return 1

# 检测磁盘剩余空间
def lengthchecktool(request):
    host = Host.objects.get(id=1)
    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        disk_usage = conn.disk_get_usage()

	dk={}
	dk['available']=disk_usage[2]
	return HttpResponse(json.dumps(dk))

