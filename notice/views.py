# encoding:utf-8
'''完成对通知公告的增删改查操作'''
# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect

from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage

import time
import datetime

import json
import logging
from django.db.models import Q

from teachers.models import Teacher
from notice.models import Notice
from adminsys.views import add_record

def noticeManage(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	noticeselect=''
	notices = Notice.objects.order_by('-id')

	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']
		notices=notices.filter(Q(survery__icontains=querytext)|Q(content__icontains=querytext))
		noticeselect=querytext
	if 'noticeselect' in request.GET:
		notices = Notice.objects.order_by('-id')
		querytext = request.GET.get("noticeselect")
		notices=notices.filter(Q(survery__icontains=querytext)|Q(content__icontains=querytext))
		noticeselect=querytext
	after_range_num=10
	befor_range_num=4
	try:
		page = int(request.GET.get("page",1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1
	paginator = Paginator(notices,10)
	try:
		notices_list = paginator.page(page)
	except(EmptyPage,InvalidPage,PageNotAnInteger):
		notices_list = paginator.page(paginator.num_pages)
	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:int(page)+befor_range_num]
	return render_to_response('templates/notice.html',{'noticeselect':noticeselect,'noticels':notices_list,'notices':notices,'page_range':page_range},context_instance=RequestContext(request))

def add(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	if request.method == 'POST':
		survery = request.POST['survery']
		content = request.POST['content']
		notice = Notice(survery=survery,content=content,createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),createbytea_id=request.session["userid"])
		notice.save()
	add_record(request.session['useraccount'], u'发布公告：' + request.POST['content'], 1)
	return HttpResponseRedirect('/notice/')

def editGetInfo(request,nid):
	returnLogin=0
	if 'stuno' in request.session:
		returnLogin+=1
	if 'username' in request.session:
		returnLogin+=1
	if returnLogin==0:
		return HttpResponseRedirect('/Login/')

	try:
		nid=int(nid)
		notice = Notice.objects.get(id=nid)
	except:
		logger.error("notice")
		raise Http404()
	datas={
		'nsurvery':notice.survery,
		'ncontent':notice.content,
		'nid':nid,
	}
	return HttpResponse(json.dumps(datas))



def editSubmit(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	if request.method == 'POST':
		try:
			nid=int(request.POST['hideid'])
			notice = Notice.objects.get(id=nid)
		except:
			logger.error("notice")
			raise Http404()

		notice.survery = request.POST['editsurvery']
		notice.content = request.POST['editcontent']
		notice.edittime=datetime.datetime.now()
		notice.save()
	return HttpResponseRedirect('/notice/')

def deltinoce(request,nid):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	if request.method == 'POST':
		try:
			nid=int(nid)
			notice = Notice.objects.get(id=nid)
		except:
			logger.error("notice")
			raise Http404()
		notice.delete()
	return HttpResponseRedirect('/notice/')

def readnotice(request):
	returnLogin=0
	if 'stuno' in request.session:
		returnLogin+=1
	if 'username' in request.session:
		returnLogin+=1
	if returnLogin==0:
		return HttpResponseRedirect('/Login/')

	noticeselect=''
	notices = Notice.objects.order_by('-id')

	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']
		notices=notices.filter(Q(survery__icontains=querytext)|Q(content__icontains=querytext))
		noticeselect=querytext
	if 'noticeselect' in request.GET:
		notices = Notice.objects.order_by('-id')
		querytext = request.GET.get("noticeselect")
		notices=notices.filter(Q(survery__icontains=querytext)|Q(content__icontains=querytext))
		noticeselect=querytext
	after_range_num=10
	befor_range_num=4
	try:
		page = int(request.GET.get("page",1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1
	paginator = Paginator(notices,10)
	try:
		notices_list = paginator.page(page)
	except(EmptyPage,InvalidPage,PageNotAnInteger):
		notices_list = paginator.page(paginator.num_pages)
	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:int(page)+befor_range_num]
	return render_to_response('templates/readnotice.html',{'noticeselect':noticeselect,'noticels':notices_list,'notices':notices,'page_range':page_range},context_instance=RequestContext(request))
