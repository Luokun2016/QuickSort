# -*- coding: UTF-8 -*-

'''
1. 显示物理设备界面：调用mgrdevice方法；
2. 添加物理设备：调用adddevice方法，将物理设备信息，以及连接到服务器上的端口号保存到数据库中；
3. 编辑物理设备：调用editdevice方法，修改物理设备信息；
4. 删除物理设备：调用deldevice方法，从数据库中删除该物理设备信息；
'''

# Create your views here.
import sys
from django.shortcuts import render_to_response
from devices.models import Device
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import json
import logging
from django.utils import simplejson
from django.core import serializers
from django.db.models import Q
import os
from tsssite.settings import HERE
reload(sys)
sys.setdefaultencoding('UTF-8')

logger = logging.getLogger('mysite.log')
class QuerySetEncoder( simplejson.JSONEncoder ):
    		"""
    		Encoding QuerySet into JSON format.
    		"""
		def default( self, object ):
        			try:
            				return serializers.serialize( "python", object, ensure_ascii = False )
        			except:
            				return simplejson.JSONEncoder.default( self, object )
def dictostring(dic):
	result = "{"
	for key, value in dic.items():
		if result != '{':
			result = result + ','
		result = result + '\"%s\":\"%s\"' %(key, value)
	result = result + '}'
	return result
def mgrdevice(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	username = request.session['username']
	devicels = Device.objects.order_by('-id')
	querytext = ''
	#界面上用户按类型搜索输入的是中文，数据库中存的类型是pc，pgate等
	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']
		if querytext in "安全设备".decode('utf8'):
			querytext = "pgate"
		if querytext in "网络设备".decode('utf8'):
			querytext = "pswitch"
		if querytext in "终端设备".decode('utf8'):
			querytext = "pc"
	devicels=devicels.filter(Q(devname__icontains=querytext)|Q(devtype__icontains=querytext))

	# 如果物理设备的脚本文件被删除了，那么就清空pyscript字段
	for d in devicels:
		if d.pyscript and not os.path.exists(HERE + '/document/devpyscript/' + d.pyscript):
			d.pyscript = None
			d.save()

	# if 'sdip' in request.GET and request.GET['sdip']:
	# 	devicels = devicels.filter(devip__contains=request.GET['sdip'])
	# if 'sdname' in request.GET and request.GET['sdname']:
	# 	devicels = devicels.filter(devname__contains=request.GET['sdname'])
	# if 'devstate' in request.GET and request.GET['devstate']:
	# 	if not request.GET['devstate'] == '-1':
	# 		devicels = devicels.filter(state=int(request.GET['devstate']))
	after_range_num = 5
	befor_range_num = 4
	try:
		page = int(request.GET.get("page",1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1
	paginator = Paginator(devicels,10)
	try:
		devicels = paginator.page(page)
	except(EmptyPage,InvalidPage,PageNotAnInteger):
		devicels = paginator.page(paginator.num_pages)
	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:int(page)+befor_range_num]
	# return render_to_response('templates/device.html',{'devicels':devicels, 'page_range':page_range}, context_instance=RequestContext(request))
	
	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']#转换成中文显示
	# return render_to_response('templates/showstate.html',{'querytext':querytext,'devicels':devicels, 'username':username,'page_range':page_range}, context_instance=RequestContext(request))
	return render_to_response('templates/device.html',{'querytext':querytext,'devicels':devicels, 'username':username,'page_range':page_range}, context_instance=RequestContext(request))


def deviceinfo(request):
		dev = ''
		if request.method == 'POST':
			devid = request.POST['devid']
			dev = Device.objects.get(id=devid)
		data = {}
		data["devid"] = dev.id
		data["devname"] = dev.devname
		data["devtype"] = dev.devtype
		data["devxh"] = dev.devxh
		data["devfac"] = dev.devfac
		data["devpub"] = dev.devpub
		data["ethx"] = dev.ethx
		# data["pyscript"]=dev.pyscript
		data["remark"] = dev.remark
		return HttpResponse(json.dumps(data))
def handle_uploaded_file(f,path):
	with open(path, 'wb+') as info:
		for chunk in f.chunks():
			info.write(chunk)
	return f

def adddevice(request):
		if request.method == 'POST':
			if request.POST.get('dname',''):
				eth = request.POST['eth']
				if "eth" not in eth:
					eth = None
				dev1 = Device(devname=request.POST['dname'], devtype=request.POST['dtype'], devxh=request.POST['dxh'], devpub=request.POST['dpub'], devfac=request.POST['dfac'], remark=request.POST['dremark'],ethx=eth)

				if request.FILES:
					if not os.path.isdir("document/devpyscript"):
						comd = "mkdir document/devpyscript"
						os.system(comd)
					path =os.path.join( HERE , 'document/devpyscript/')
					#path ='./document/devpyscript/'  #两种取得根路径的方法
					mfile = request.FILES['uploadadd']
					filepath = path+str(request.POST['dname']+'.py')
					f = handle_uploaded_file(mfile,filepath)
					dev1.pyscript = request.POST['dname']+'.py'
				dev1.save()
		return HttpResponseRedirect('/devices/')

def editdevice(request):
		global logger
		try:
			did = int(request.POST['devid'])
			dev = ''
			dev = Device.objects.get(id=did)
		except ValueError:
			logger.error("devices")
			raise Http404()	
		if not os.path.isdir("document/devpyscript"):
			comd = "mkdir document/devpyscript"
			os.system(comd)
		path =os.path.join( HERE , 'document/devpyscript/')					
		if request.method == 'POST':
			if request.FILES:#上传了新的脚本，脚本名与设备名相同
				mfile = request.FILES['uploadedit']				
				#path ='./document/devpyscript/'  #两种取得根路径的方法		
				if dev.pyscript:
					cmd = "rm -rf "+path+dev.pyscript
					os.system(cmd)
				filepath = path+str(request.POST['dname']+'.py')
				f = handle_uploaded_file(mfile,filepath)
				dev.pyscript = request.POST['dname']+'.py'
			else:#没有上传新的脚本，可能更改了设备名，需要更新脚本名
				if dev.devname != request.POST['dname']:
					cmd = "mv "+path+dev.devname+".py "+path+request.POST['dname']+'.py'
					os.system(cmd)
					dev.pyscript = request.POST['dname']+'.py'
				else:#添加时没有上传脚本，编辑时也没有上传脚本
					pass
			dev.devname = request.POST['dname']
			dev.devtype = request.POST['devtype']
			dev.devxh = request.POST['devxh']
			dev.devpub = request.POST['devpub']
			dev.devfac = request.POST['devfac']
			dev.ethx = request.POST['ethedit']
			dev.remark=request.POST['devremark']
			dev.save()
		return HttpResponseRedirect('/devices/')

def deldevice(request, did):
		global logger
		error = ''
		path =os.path.join( HERE , 'document/devpyscript/')
		try:
			did = int(did)
			dev = Device.objects.get(id=did)

			#删除脚本
			pyname = dev.pyscript
			if pyname:
				cmd = "rm -rf "+path+pyname
				os.system(cmd)
			
			dev.delete()
		except ValueError:
			logger.error("devices")
			raise Http404()	
		return HttpResponseRedirect('/devices/')	

def devicenamecheck(request):
		global logger
		judgedevname=0
		if request.method == 'POST':
				try:
						devicename = request.POST['dname']
				except ValueError:
						logger.error("devices")
						raise Http404()				
				devicetotal=Device.objects.order_by('id')
				for dev in devicetotal:
						if dev.devname == devicename:
								judgedevname=1
								break
		data = {}
		data['judgename']=judgedevname
		return HttpResponse(json.dumps(data))