#-*- coding: utf-8 -*- 
#教练控制台部分，显示哪些学员在实训
# Create your views here.
# Create your views here.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from client.models import *
from outlines.models import Outline,Chapter,Outlinerelation,Exprelation
from students.models import Student
from teachers.models import Teacher
from experiments.models import Experiment
from django.template import RequestContext
from vms.models import *
import datetime, time
import json
from adminsys.models import Records
from django.db.models import Q


def sysadmin(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	errors = []			
	return render_to_response('templates/teacheradmin.html', {'errors': errors}, context_instance=RequestContext(request))


def seesight(request):
	errors = []			
	# return render_to_response('templates/teacherlook.html', context_instance=RequestContext(request))
	return render_to_response('templates/teacherlook.html', context_instance=RequestContext(request))


def realtimeinfor(request):
	clients=[]
	client= Client.objects.order_by('id')
	for cl in client:
		#check the vm
		idlist=[]
		# course = Course.objects.filter(cname=cl.coursename)
		# course = Course.objects.filter(cname__exact=cl.coursename)
		# for c in course:
		# 	if c.cname==cl.coursename:
		# 		course = c
		# 		break
		course = Course.objects.filter(cname__exact=cl.coursename)
		if course.count()==1:
			course = course[0]
		elif course.count()>1:
			for c in course:
				if c.cname==cl.coursename:
					course = c
					break
		else:
			continue

		ct = course.courseteacher_set.all()
		for c in ct:
			idlist.append(c.teacherid_id)

		if request.session['userid'] in idlist or request.session['userroletype']==1:
			contr=Res.objects.filter(userid=cl.studentid,isconsole=True,restype=0)
			if contr:
				for cn in contr:
					vm = Vm.objects.get(name=cn.rname)
					vmid=vm.id
			else:
				vmid=0
			strStartTime = cl.lasttime.strftime('%Y-%m-%d %H:%M:%S')
			starttime = datetime.datetime.strptime(strStartTime, '%Y-%m-%d %H:%M:%S')
			#starttime = starttime+datetime.timedelta(hours=8)
			if (datetime.datetime.now()-starttime).seconds<150:
				if cl.coursename =='':
					cl.coursename='--'
				stu = Student.objects.filter(id=cl.studentid)
				if stu.count()==1:
					if cl.expid_id!=None:
						clients.append([stu[0].stuname,cl.coursename,cl.expid.expname,vmid])
					else:
						clients.append([stu[0].stuname,cl.coursename,'--',vmid])
			# else:
			# 	client.delet();

	data={}
#	data['num_pages']=clients_list.paginator.num_pages
#	data['number']=clients_list.number
	data["realtimeinfor"]=clients
	return HttpResponse(json.dumps(data))

def funcando(request,createtea):
	cando = "true"
	currenttea = Teacher.objects.get(id=request.session['userid'])
	if currenttea.roletype == 1:#管理员对教师的
			cando = "true"
	elif currenttea.roletype ==0 and createtea.id == request.session['userid']:#自己对自己的
			cando = "true"
	else:
			cando= "false"
			return cando


def add_record(user, operate, re, type=0):
	if type == 0:
		tea = Teacher.objects.get(account=user)
		# tea = Teacher.objects.extra(where=["binary account='" + user + "'"])[0]
		if tea.roletype == 1:
			type = 2
	record = Records(userid=user, usertype=type,operate=operate, result=re)
	record.save()
	return record.id
