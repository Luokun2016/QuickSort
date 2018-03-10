#-*- coding: utf-8 -*- 
'''
完成对系统管理模块中，数据字典的增删改查操作
'''
from myexp.models import *
from django.shortcuts import render_to_response,render
from classes.models import Class,Department
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import json

enmupages = 1
informationpages = 1
# 展示页面信息
def myexpinitial(request):
	global enmupages
	global informationpages
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	DicTypes = DicType.objects.order_by('-id')
	DicContents=DicContent.objects.order_by('-id')
	types = request.GET.get("type","1")

	after_range_num = 4
	befor_range_num = 5
	try:
		page = int(request.GET.get("page", 1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1


	if types=='1':
		mtype="1"
		enmupages = page
	else:
		mtype="2"
		informationpages=page


	paginator0 = Paginator(DicTypes, 10)

	paginator = Paginator(DicContents, 10)

	try:
		eList = paginator0.page(enmupages)
	except(EmptyPage, InvalidPage, PageNotAnInteger):
		eList = paginator0.page(paginator0.num_pages)
		
	try:
		cList = paginator.page(informationpages)
	except(EmptyPage, InvalidPage, PageNotAnInteger):	
		cList = paginator.page(paginator.num_pages)

	if page >= after_range_num:
		page_range0 = paginator0.page_range[enmupages-after_range_num:enmupages+befor_range_num]

		page_range = paginator.page_range[informationpages-after_range_num:informationpages+befor_range_num]
	else:
		page_range0 = paginator0.page_range[0:enmupages+befor_range_num]

		page_range = paginator.page_range[0:informationpages+befor_range_num]

	return  render_to_response('templates/myexp.html',{
		'eList':eList,
		'page_range0':page_range0,
		'cList':cList,
		'page_range':page_range,
		'tabtype':mtype,
		},context_instance=RequestContext(request))
# 编辑页面获取信息
def GetEnumEditConfig(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			eid = int(request.POST.get("id"))

			dicType= DicType.objects.get(id =eid )
			data["id"] = dicType.id
			data["key"]=dicType.enumtype
			data["value"]=dicType.enumdesc
	except Exception as e:
		data["error"]=e.strerror
	else:
		data["error"]=""

	return HttpResponse(json.dumps(data))
# 删除功能
def DeleteEnumSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			eid = int(request.POST.get("id"))

			DicContents = DicContent.objects.filter(enumid_id=eid )
			for x in DicContents:
				x.delete()
			dicType= DicType.objects.get(id =eid )
			dicType.delete()

	except Exception, e:
		data["error"]=e.strerror
	else:
		data["error"]=""
	
	return HttpResponse(json.dumps(data))
# 添加功能
def AddEnumSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			key = request.POST.get("enumKey")
			value = request.POST.get("enumDescription")
			dics= DicType.objects.filter(enumtype = key )
			if len(dics)>0:
				data["error"]="1"
			else:
				dt=DicType(enumtype =key , enumdesc=value)
				dt.save()
				data["error"]=""
	except Exception, e:
		data["error"]="2"
	
	return HttpResponse(json.dumps(data))
# 编辑功能
def EditEnumSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			eid = int(request.POST.get("id"))
			key = request.POST.get("enumKey")
			value = request.POST.get("enumDescription")
			dics= DicType.objects.order_by('-id')
			dicType= DicType.objects.get(id =eid )
			checkdics=dics.filter(enumtype =key)
			repeat=0
			if len(checkdics)>0:
				for checkdic in checkdics:
					if checkdic.id!=eid:
						repeat=1
				if repeat==1:
					data["error"]="1"
			if repeat==0:
				dicType.enumtype = key
				dicType.enumdesc = value
				dicType.save()
				data["error"]=""
	except Exception, e:
		data["error"]="2"
	return HttpResponse(json.dumps(data))


# 获取编辑信息
def GetContentEditConfig(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			cid = int(request.POST.get("id"))
			if cid != -1:
				diccontent= DicContent.objects.get(id = cid )
				data["id"] = diccontent.id
				data["key"]=diccontent.enumid.id
				data["value"]=diccontent.typename
	except Exception, e:
		data["error"]=e.strerror
	else:
		data["error"]=""
	finally:
		enums=[]
		DicTypes = DicType.objects.order_by('-id')
		for x in DicTypes:
			enum={}
			enum["id"]=x.id
			enum["key"]=x.enumtype
			enum["value"]=x.enumdesc
			enums.append(enum)
		data["enums"] = enums
		return HttpResponse(json.dumps(data))
# 删除功能
def DeleteContentSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	page=0
	try:
		if request.method == 'POST':
			eid = int(request.POST.get("id"))
			dicContent= DicContent.objects.get(id =eid )
			dicContent.delete()
	except Exception, e:
		data["error"]=e.strerror
	else:
		data["error"]=""
	
	return HttpResponse(json.dumps(data))
# 添加功能
def AddContentSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			key = request.POST.get("contentKey")
			value = request.POST.get("contentDescription")
			dts= DicContent.objects.filter(typename = value )
			if len(dts)>0:
				data["error"]="1"
			else:
				dt=DicContent(enumid_id=int(key), typename=value)
				dt.save()
				data["error"]=""
	except Exception, e:
		data["error"]="2"

	return HttpResponse(json.dumps(data))

# 编辑功能
def EditContentSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	try:
		if request.method == 'POST':
			cid = int(request.POST.get("id"))
			key = request.POST.get("contentKey")
			value = request.POST.get("contentDescription")

			dcs= DicContent.objects.order_by('-id')
			checkdics=dcs.filter(typename =value)
			dicContent= DicContent.objects.get(id =cid )
			repeat=0
			if len(checkdics)>0:
				for checkdic in checkdics:
					if checkdic.id!=cid:
						repeat=1
				if repeat==1:
					data["error"]="1"
			if repeat==0:			
				dicContent.enumid_id = key
				dicContent.typename = value
				dicContent.save()
				data["error"]=""
	except Exception, e:
		data["error"]="2"
	return HttpResponse(json.dumps(data))
