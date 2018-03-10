#-*- coding: utf-8 -*- 
'''完成攻防对抗客户端学生答题以及记分与排名的功能'''
from django.shortcuts import render_to_response
from students.models import Student
from client.models import *
from vms.models import *
from courses.models import Course
from outlines.models import Exprelation
from experiments.models import Experiment
from sysmgr.models import *
from vgates.models import *
from vswitches.models import *
from tsssite.server import ConnServer
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.models import Q
import json
import datetime
import logging
import sys, os, libvirt, subprocess
from libvirt import libvirtError
from adminsys.views import add_record
from atkdfs.models import Atkdfs
logger = logging.getLogger('mysite.log')
vmls_pages = 1
imgls_pages = 1

def hacking(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	errors=[]
	uname = request.session['cusername']
	
	return render_to_response('templates/hack.html',{'errors': errors, 'uname':uname}, context_instance=RequestContext(request))

def flags(request):
	try:
		hack_id = request.GET['hack_id']
		request.session['hack_id'] = hack_id
		content={}
		uname = request.session['cusername']
		content["uname"]=uname
		content["hhdata"]=hack_id
    		add_record(request.session["stuno"], operate=u'开始攻防:'+Atkdfs.objects.get(id=hack_id).atkdfsNo, re=1, type=1)

		return render_to_response('templates/flags.html',content,context_instance=RequestContext(request))
	except: 
		content={}
		uname = request.session['cusername']
		try:    
		    content["hhdata"]=request.session['hack_id']
		except:
			pass
		    # print "the page has not hack_id!!!"
		content["uname"]=uname
    		add_record(request.session["stuno"], operate=u'开始攻防:'+Atkdfs.objects.get(id=request.session['hack_id']).atkdfsNo, re=1, type=1)

		return render_to_response('templates/flags.html',content,context_instance=RequestContext(request))

def ranking(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	errors=[]
	uname = request.session['cusername']
	return render_to_response('templates/ranking.html',{'errors': errors, 'uname':uname}, context_instance=RequestContext(request))

#vm:imgls/vgate:imgvgtls
def Getid(request,vtype,name):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')

	if vtype == "imgls":
		vm = Vm.objects.get(name=name)
		data = {}
		data["vmid"] = vm.id
		data["vmname"] = vm.name
		data["vmtype"] = vm.imgtype.id
		data["vmram"] = vm.memory
		data["vmcpu"] = vm.cpu    
		data["vmmgrip"] = vm.mgrip
		data["vmmgrport"] = vm.mgrport
		data["remark"] = vm.remark
	if vtype == "imgvgtls":
		vgt = Vgate.objects.get(name=name)
		data = {}
		data["vgtid"] = vgt.id
		data["vgtname"] = vgt.name
		data["vgttype"] = vgt.imgtype.id
		data["vgtmgrip"] = vgt.mgrip
		data["vgtmgrport"] = vgt.mgrport
		data["vgtram"] = vgt.memory
		data["vgtcpu"] = vgt.cpu   
		data["remark"] = vgt.remark
	return HttpResponse(json.dumps(data))

def netsource(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	errors=[]
	username = request.session['cusername']
	userid = request.session['cuserid']

	gms=GroupMembers.objects.filter(studentid=userid)
	res=[]
	for g in gms:
 		groupid=g.groupid_id	
 		m_res=Res.objects.filter(restype = 2,usebygroup=groupid, resid=request.session['hack_id'])
 		m_res=m_res.exclude(rtype="imgvshls")

		res.extend(m_res)
		print res
	return render_to_response('templates/netsource.html',{'res': res, 'username':username}, context_instance=RequestContext(request))