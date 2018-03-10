#-*- coding: utf-8 -*- 
'''教练或管理员登陆功能'''

# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from teachers.models import *
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import json
import os, sys
from adminsys.views import add_record
from django.contrib import auth
def index(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	else:
		return render_to_response('templates/index.html', context_instance=RequestContext(request))

def loginIni(request):
	errors = []
	request.session.set_expiry(60*60*24) 
	if request.method == 'POST':
		txtaccount = request.POST["txtaccount"]
		try:
			tea = Teacher.objects.get(account=txtaccount)  # 不区分大小写
			# tea = Teacher.objects.extra(where=["binary account='" + txtaccount + "'"])[0]  # 区分大小写
			if tea.needaudit==1:
				data["judge"] = 1
			else:
				if tea.pwd == request.POST["txtpwd"]:
					request.session["userroletype"] = tea.roletype
					request.session["useraccount"] = tea.account
					request.session["username"] = tea.teaname
					request.session["userid"] = tea.id
					data = {}
					data["judge"] = 0

					add_record(txtaccount, "登录", 1)

					return HttpResponse(json.dumps(data))
				else:
					data = {}
					data["judge"] = 1
					add_record(txtaccount, "登陆密码错误", 0)
					return HttpResponse(json.dumps(data))
		except Exception:
			data = {}
			data["judge"] = 2
			add_record('admin', u"登陆失败，用户{0}未注册".format(txtaccount), 0)
			return HttpResponse(json.dumps(data))
	return render_to_response('templates/login.html', {'errors': errors}, context_instance=RequestContext(request))

def logout(request):
	try:
		add_record(request.session['useraccount'], "登出", 1)
		auth.logout(request)
		# del request.session['userroletype']
		# del request.session['username']
		# del request.session['useraccount']
		# del request.session['userid']
	except KeyError:
		pass
	return HttpResponseRedirect('/Login/')

def shutdown(request):
	try:
		data={}
		# print "777777777777777"
		# del request.session['userroletype']
		# del request.session['username']
		# del request.session['useraccount']
		# del request.session['userid']
		# print "888888888888888"
		# os.system("reboot")#重启服务器
		os.system("shutdown -h now")#关闭服务器
		# print "999999999999999"
		data["result"]='shutdown'
	except KeyError:
		pass
	return HttpResponse(json.dumps(data))
	


