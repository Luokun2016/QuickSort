#-*- coding: utf-8 -*- 
'''
1. 学员在登陆页面输入账号密码，调用mgrclient方法，验证账号密码是否正确

2. 登陆客户端，账号密码正确，调用clientindex方法，返回客户端html页面

3. 页面加载过程中，调用students模块中的views.py文件中的coursecheck方法，返回该学员参加的所有课程，
然后调用examgetinfo获取该学员参加的所有竞赛(已开启的)，最后调用hackgetinfo获取该学院参加的所有攻防(
已开启的);

4. 退出登录，调用clogout方法；

5. 修改密码，调用modifypwd方法；

6. 点击某个实训课程，调用lab方法，返回lab.html页面用于显示课程中所有的实验，页面加载过程中调用
outlines.views.outtreeDetails方法，获取该课程的所有实验；

7. 如果某个实验有拓扑图，则可以在实验设施中，点击启动试验台，首先清除空闲的实验环境controlChecklab，然后
调用selectVM方法，从多台服务器中选择最合适的一台服务器用于启动拓扑图，调用该服务器上的startBench方法，
为拓扑图中的设备分配虚拟机，并创建虚拟交换机用于虚拟机之间的组网。
'''

# Create your views here.
from django.shortcuts import render_to_response,render
from students.models import Student
from questions.models import Question
from questions.models import *
from examinations.models import *
from atkdfs.models import *
from papers.models import *
from groups.models import *
from client.models import *
from courses.models import Course,Coursestudent
from outlines.models import Exprelation
from experiments.models import Experiment
from sysmgr.models import *
from vms.models import *
from vgates.models import *
from vswitches.models import *
from devices.models import *
from tsssite.server import *
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.models import Q
import json
import datetime
import sys, os, libvirt, subprocess
from libvirt import libvirtError
import urllib
import urllib2
import sys

from xml.etree import cElementTree as ET
from  xml.dom import minidom
import time
from collections import OrderedDict
from adminsys.views import *
import logging
from django.contrib import auth
#from singleton import vmMgr

logger = logging.getLogger('mysite.log')

reload(sys)
sys.setdefaultencoding("utf8")

vm_ovs ={}
vm_vgt = {}
g_ethlist = {}
rectFlag = {}
IsStartingVm=False
br_MacAddr={}#vgate的mac地址
br_Addr={}#ovs和终端的ip

container_ip = ""
records = {}  # 记录学生启动实验时，在数据库中相应操作记录的id

groQueInfilTopo=None
def clientindex(request):
	if not 'stuno' in request.session:
		return HttpResponseRedirect('/Login/')
	else:
		uname = request.session['cusername']
		return render_to_response('templates/NewClientIndex.html',{'uname':uname}, context_instance=RequestContext(request))

def mgrclient(request):
	request.session.set_expiry(60*60*24) 
	errors=[]
	if request.method == 'POST':
		if 'ctxtaccount' in request.POST:
			txtaccount = request.POST["ctxtaccount"]
		else:
			txtaccount = False
		try:
			tea = Student.objects.get(stuno=txtaccount)
			if tea.needaudit==1:
				data["judge"] = 1
			else:
				if tea.pwd == request.POST["ctxtpwd"]:
					request.session["stuno"] = tea.stuno
					request.session["cusername"] = tea.stuname
					request.session["cuserid"] = tea.id
					data = {}
					data["judge"] = 0

					add_record(request.session["stuno"], operate='登录', re=1, type=1)

					return HttpResponse(json.dumps(data))
				else:
					data = {}
					data["judge"] = 1
					return HttpResponse(json.dumps(data))
		except Exception:
			data = {}
			data["judge"] = 2
			return HttpResponse(json.dumps(data))
	return render_to_response('templates/login.html',{'errors': errors}, context_instance=RequestContext(request))

def examgetinfo(request):
		exams={}
		compt=[]
		groupmb = GroupMembers.objects.filter(studentid_id=request.session["cuserid"])
		for ins in groupmb:
			try:
				student_exams=ExamGroup.objects.filter(groupID_id=ins.groupid_id)
				if len(student_exams) > 0:
					for sx in student_exams:
						try:
							exam = Examinations.objects.get(id=sx.examID_id)
							if exam.examStatus == 2:
								compt.append([exam.examNo, exam.examName, exam.id, exam.examPaperID_id])
						except:
							# print "errors"
							pass
			except:
				# print "this is not in exams"
				pass
		exams["competiname"] = compt
		return HttpResponse(json.dumps(exams))
#获取已开启的对抗
def hackgetinfo(request):
	hacks={}
	compts=[]
	groupmb = GroupMembers.objects.filter(studentid_id=request.session["cuserid"])
	for ins in groupmb:
		try:
			student_hacks=AtkdfsGroup.objects.filter(groupID_id=ins.groupid_id)
			if len(student_hacks) > 0:
				for sx in student_hacks:
					try:
						hack = Atkdfs.objects.get(id=sx.atkdfsID_id)
						if hack.atkdfsStatus == 2:
							request.session['group_id'] = ins.groupid_id
							compts.append([hack.atkdfsNo, hack.atkdfsName, hack.id, hack.atkdfsPaperID_id])
					except:
						# print "errors"
						pass
		except:
			# print "this is not in hack"
			pass
	hacks["hackname"] = compts
	return HttpResponse(json.dumps(hacks))

#获取参加对抗的团队以及各个团队题目中预制的key
def getgroups(request):
	data = {}
	groupname = []
	hack_id = request.session['hack_id']
	#groupids = AtkdfsGroup.objects.filter(atkdfsID_id=request.session['hack_id'])
	#获取参加对抗的团队
	groups = AtkdfsGroup.objects.filter(atkdfsID_id=hack_id)
	groupss = GroupMembers.objects.filter(studentid_id=request.session['cuserid'])
	#获取唯一的参加对抗的团队ID
	for gr in groups:
		for gs in groupss:
			if gr.groupID_id == gs.groupid_id:
				gro_id =  gr.groupID_id
				g_name =Group.objects.get(id=gro_id)
				data["groupid"] = gro_id
				data["groupname"] = g_name.gname

	if len(groups) > 0:
		for i in groups:
			name = Group.objects.get(id=i.groupID_id)
			quest = Infiltration.objects.get(queid_id=i.quesID_id)
			groupname.append([name.gname,quest.result,i.quesID_id,quest.link,name.id])#团队名称+key答案+题目ID
			# data["topo"] = quest.topo

	data["groups"] = groupname #参加对抗的团队名称
	return HttpResponse(json.dumps(data))

def clogout(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	add_record(request.session["stuno"], operate='退出登录', re=1, type=1)
	try:
		auth.logout(request)
		# del request.session['cusername']
		# del request.session['stuno']
		# del request.session['cuserid']
		# del request.session['exam_id']
	except KeyError:
		pass
	return HttpResponseRedirect('/Login/')

def modifypwd(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	result = 1
	if request.method == 'POST':
		userid = request.session['cuserid']
		st = Student.objects.filter(id=userid)
		if not st:
			return HttpResponseRedirect('/Login/')
		stu = Student.objects.get(id=userid)
		try:
			if request.POST["spwd"] == stu.pwd:
				if request.POST["npwd"] and request.POST["repwd"]:
					if request.POST["npwd"] == request.POST["repwd"]:
						if stu.pwd == request.POST["npwd"]:
							result = 4  #  新密码不能和原有密码相同
						else:
							stu.pwd = request.POST["npwd"]
							stu.save()
					else:
						result = 3#两次输入密码不一致
				else:
					result = 2#修改的密码有空的情况
			else:
				result = 0#输入的原密码不正确
		except Exception:
			result = 0
	add_record(request.session["stuno"], operate='修改密码', re=1, type=1)

	return HttpResponse(result)
	
def lab(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	errors=[]
	uname = request.session['cusername']
	vmid = 0
	selcourse = None
	coursename = None
	curexp = 0
	if request.method == 'GET':
		# if 'selcourse' in request.POST:
			coursename = request.GET['courname']
			selcourse = request.GET['selcourse']
			cuserid = request.session['cuserid']
			clientres = Res.objects.filter(userid=cuserid).order_by('-id')
			if len(clientres) > 0:
				for res in clientres:
					if res.isconsole:
						vm = None
						vm = Vm.objects.get(name=res.rname)
						curexp = res.resid
						if vm:
							vmid = vm.id
	# add_record(request.session["stuno"], operate=u'进入课程:'+coursename, re=1, type=1)

	csts = Coursestudent.objects.filter(studentid_id=cuserid)
	if len(csts)==0:
		return clientindex(request)
	return render_to_response('templates/lab.html',{'errors': errors, 'uname':uname, 'selcourse':selcourse, 'coursename':coursename, 'vmid':vmid, 'curexp':curexp }, context_instance=RequestContext(request))

#add contest model information
def examinfo(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	uname = request.session['cusername']
	errors=[]
	return render_to_response('templates/contest.html',{'errors': errors, 'uname':uname}, context_instance=RequestContext(request))

def Getaddbutton(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	data={}
	if request.method == 'POST':	
		cuserid = request.session['cuserid']	
		curexp = int(request.POST['curexp'])
		clientre = Res.objects.filter(userid=cuserid).order_by('-id')
		if len(clientre) > 0:
			data['started']="true"
		clientres=clientre.filter(Q(resid=curexp))
		if len(clientres) > 0:
			for res in clientres:
				if res.rtype=="imgls" and not res.isconsole:
					vm = Vm.objects.get(name=res.rname)
					data[res.rname]=vm.id
	return HttpResponse(json.dumps(data))
def clientinfor(request):
	if not 'cusername' in request.session:
		return HttpResponseRedirect('/Login/')
	clients=0
	if request.method == 'POST':
		if not request.POST.get('expid',''):
			errors.append('expid')
		
		clientid =  Client.objects.filter(studentid= request.session['cuserid'])
		
		expr= Exprelation.objects.order_by('id')

		if len(clientid) == 0:
			if request.POST['expid'] =='0' and request.POST['courname']=='0':	
				client = Client(studentid=request.session['cuserid'],expid_id=None, coursename='',lasttime=datetime.datetime.now())
				# client = Client(studentid=request.session['cuserid'],expid_id=None, copytopo=None,coursename='',lasttime=datetime.datetime.now())
				
				client.save()
			elif  request.POST['expid'] !='0' and request.POST['courname']=='0':
				for ex in expr:
					if ex.id==int(request.POST['expid']):
						client = Client(userid=request.session['cuserid'], expid_id=int(request.POST['expid']),coursename='',lasttime=datetime.datetime.now())
						# client = Client(userid=request.session['cuserid'], expid_id=int(request.POST['expid']),copytopo=ex.exp.topo,coursename='',lasttime=datetime.datetime.now())
						
						client.save()
						break
			elif  request.POST['expid'] =='0' and request.POST['courname']!='0':
				client = Client(studentid=request.session['cuserid'],expid_id=None,coursename=request.POST['courname'],lasttime=datetime.datetime.now())
				# client = Client(studentid=request.session['cuserid'],expid_id=None,copytopo=None,coursename=request.POST['courname'],lasttime=datetime.datetime.now())
				
				client.save()
			else :
				for ex in expr:
					if ex.id==int(request.POST['expid']):
						client = Client(studentid=request.session['cuserid'], expid_id=int(request.POST['expid']),coursename=request.POST['courname'],lasttime=datetime.datetime.now())
						# client = Client(studentid=request.session['cuserid'], expid_id=int(request.POST['expid']), copytopo=ex.exp.topo,coursename=request.POST['courname'],lasttime=datetime.datetime.now())
						
						client.save()
						break
		else:

			client=Client.objects.get(studentid= request.session['cuserid'])
			if request.POST['expid'] =='0' and request.POST['courname']=='0' :
				client.coursename=''
				client.expid_id=None
				# client.copytopo=None
				client.lasttime=datetime.datetime.now()
				client.save()
			elif  request.POST['expid'] !='0' and request.POST['courname']=='0' :
				for ex in expr:
					if ex.id==int(request.POST['expid']):
						client.coursename=''
						client.expid_id=int(request.POST['expid'])
						# client.copytopo=ex.exp.topo
						client.lasttime=datetime.datetime.now()
						client.save()
						break
			elif  request.POST['expid'] =='0' and request.POST['courname']!='0' :
				client.coursename=request.POST['courname']
				client.expid_id=None
				# client.copytopo=None
				client.lasttime=datetime.datetime.now()
				client.save()
			else :
				for ex in expr:
	
					if ex.id==int(request.POST['expid']):
						client.coursename=request.POST['courname']
						client.expid_id=int(request.POST['expid'])
						# client.copytopo=ex.exp.topo
						client.lasttime=datetime.datetime.now()
						client.save()
						break

		clients=client.id
	data={}
	data["clientid"]=clients
	return HttpResponse(json.dumps(data))
def topoToJson(topo1):
	topo = topo1
	topo = topo.replace('{', '{\"')
	topo = topo.replace('}', '\"}')
	topo = topo.replace(',', '\",\"')
	topo = topo.replace(':','\":\"')
	topo = topo.replace('\'', '')
	topo = topo.replace(':\"{', ':{')
	topo = topo.replace('}\",', '},')
	topo = topo.replace('}\"}', '}}')
	topo = topo.replace('}\"}', '}}')
	topo = topo.replace(' ', '')
	topo = topo.replace('{\"\"}', '{}')

	jsondata = json.loads(topo)
	return jsondata

def jsonToTopo(topo1):

	topo = json.dumps(topo1)

	topo = topo.replace('\"', '\'')
	topo = topo.replace(': ', ':')
	topo = topo.replace('\':', ':')
	topo = topo.replace(', \'',',')
	topo = topo.replace(',\'', ',')
	topo = topo.replace(':{\'', ':{')
	topo = topo.replace('{\'', '{')
	topo = topo.replace('\'[]\'', '[]')


	# topo = topo.replace('', ' ')
	# topo = topo.replace('{}', '{\"\"}')

	# topo = json.dumps(topo)
	return topo


def getServerIp(request):
	if "vmid" in request.POST:
		vid = int(request.POST['vmid'])
		try:
			vm = Vm.objects.get(id=vid)
		except Exception:
			return HttpResponse(json.dumps(''))
	elif "vgtid" in request.POST:
		vid = int(request.POST['vgtid'])
		vm = Vgate.objects.get(id=vid)
	ip = vm.containerIP
	return HttpResponse(json.dumps(ip))


def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()


# 这个函数用来获取前台的请求数据，并判断需要将数据转发给哪个服务器
# 前台启动虚拟机时，会调用startBench方法，在urls.py中修改，改为调用selectVM方法
def selectVM(request):
    if request.method == 'POST':
        if not 'cusername' in request.session:
            return HttpResponseRedirect('/Login/')

        cuserid = request.session['cuserid']
        curexp = int(request.POST['curexp'])
        expid = int(request.POST['expid'])
        courname = request.POST['courname']
        curvms = int(request.POST['curvms'])
        stuno = request.session["stuno"]
        datas = {'cuserid': cuserid, 'curexp': curexp, 'expid': expid, 'courname': courname, 'curvms': curvms, 'stuno': stuno}

        # 计算拓扑图中各种类型虚拟设备的数量
        topo = Experiment.objects.get(id=curexp).topo
        jsondata = topoToJson(topo)

        # 检测拓扑图中是否使用了物理设备，如果使用了，就固定使用主服务器
        ip = ""
        for k, v in jsondata["states"].items():
            t = v["type"]
            if t == "pc" or t == "pswitch" or t == "pgate":
                ip = Host.objects.get(id=2).hostname

        if ip == "":
            img_counts = {}  # 记录每种虚拟终端的数量，名字是固定的imgls,imgvgtls
            for k, v in jsondata["states"].items():
                t = v["props"]["type"]["value"]
                if t == "imgls" or t == "imgvgtls":
                    if t not in img_counts:
                        img_counts[t] = {}
                    ins = v["props"]["instance"]["value"]
                    if ins not in img_counts[t]:
                        img_counts[t][ins] = 1
                    else:
                        img_counts[t][ins] += 1

            # 找出剩余虚拟机能够满足拓扑图的所有服务器
            servers = Host.objects.order_by('id')[1:]
            # 首先清除空闲的实验环境controlChecklab
            logger.info('control check lab start')
            for server in servers:
                try:
                    logger.info('control check lab. start clear ' + server.hostname)
                    post("http://" + server.hostname + "/tools/controlChecklab/", {"containerIP": server.hostname})
                except Exception, diag:
                    logger.error('control check lab failed ' + server.hostname)
                    logger.exception(str(diag))
                logger.info('control check lab. end clear ' + server.hostname)
            logger.info('control check lab end')
            re = []
            flag = True
            for server in servers:
                for type, value in img_counts.items():
                    if type == "imgls":
                        for item in value:
                            img_id = Img.objects.get(name=item).id
                            free_count = len(Vm.objects.filter(containerIP=server.hostname, imgtype_id=img_id, state=0))
                            if free_count < value[item]:
                                flag = False
                    if type == "imgvgtls":
                        for item in value:
                            img_id = ImgVgt.objects.get(name=item).id
                            free_count = len(Vgate.objects.filter(containerIP=server.hostname, imgtype_id=img_id, state=0))
                            if free_count < value[item]:
                                flag = False

                if flag:
                    re.append(server)

                flag = True

            if len(re) == 0:
                logger.warning('resource is not enough')
                return HttpResponse(json.dumps({"result": 6}))

            # 在所有满足条件的服务器中，选择虚拟机启动最少的服务器
            min_count = -1
            selected = None
            for server in re:
                vgt_count = len(Vgate.objects.filter(containerIP=server.hostname, state=1))
                vm_count = len(Vm.objects.filter(containerIP=server.hostname, state=1))
                if min_count < 0:
                    min_count = vgt_count + vm_count
                    selected = server
                else:
                    if min_count >= vgt_count + vm_count:
                        min_count = vgt_count + vm_count
                        selected = server

            ip = selected.hostname
        datas["containerIP"] = ip
        logger.info('server ' + ip + ' is selected to start topo.')
        data = post("http://" + ip + "/startBench/", datas)
        logger.info('topo start finished on server ' + ip)
        return HttpResponse(data)


def startBench(request):
	global groQueInfilTopo
	global container_ip
	global records
	container_ip = request.POST["containerIP"]
	result=0
	if request.method == 'POST':
			cuserid = request.POST['cuserid']
			curexp = int(request.POST['curexp'])
			expid = int(request.POST['expid'])
			courname = request.POST['courname']
			curvms = int(request.POST['curvms'])
			exp = Experiment.objects.get(id=curexp)
			topo = exp.topo

			#复制topo图到groQueInfilTopo变量
			groQueInfilTopo=exp.topo

			jsondata = topoToJson(topo)

			vms_msg={}
			return_vms_msg=[]
			host_id = 1
			host = Host.objects.get(id=host_id)
			try:
				conn = ConnServer(host)
				#while vmMgr.IsUsing:
				#	time.sleep(1)
				#vmMgr.IsUsing = True
				global IsStartingVm
				while IsStartingVm:
					# print "system is starting vms"
					time.sleep(3)
				IsStartingVm = True
				logger.info("IsStartingVm = True")
				logger.info('begin to start vms')
				result = controlRes(request,conn,cuserid,jsondata,curexp,courname)
				logger.info('vms start finish')
				logger.info('start to reset client.copytopo')
				#vmMgr.IsUsing = False
				IsStartingVm = False
				logger.info("IsStartingVm = False")
				if result ==1:
					vgates = VgateRes.objects.filter(userid=cuserid, resid=curexp,restype=0)
					groQueInfilTopo = topoToJson(groQueInfilTopo)
					
					for vgate in vgates:
						mac = vgate.macAddr#值是eth
						path = vgate.pathKey
						text = vgate.pathtext

						for key, value in groQueInfilTopo["paths"].items():
							if key==path:
								value['text']['text']=mac
								break


					for key, value in groQueInfilTopo["states"].items():
						value['attr']['x'] = int(value['attr']['x'])
						value['attr']['y'] = int(value['attr']['y'])
						value['attr']['width'] = int(value['attr']['width'])
						value['attr']['height'] = int(value['attr']['height'])


					for key, value in groQueInfilTopo["paths"].items():
						value['text']['textPos']['x'] = int(value['text']['textPos']['x'])
						value['text']['textPos']['y'] = int(value['text']['textPos']['y'])

					groQueInfilTopo = jsonToTopo(groQueInfilTopo)

					strinfo = re.compile('TO\w+')#没有eth的其他线上的文本清空
					groQueInfilTopo=strinfo.sub('',groQueInfilTopo)

					strinfo = re.compile('\*\*')#更换虚拟机的名称时候加了**，现在去掉这个**
					groQueInfilTopo=strinfo.sub('',groQueInfilTopo)

					client = Client.objects.get(studentid = cuserid)
					client.copytopo = groQueInfilTopo#显示启动后的拓扑图
					client.save()

				else:
					logger.info('Bench start failed, roll-back')
					global IsStartingVm
					IsStartingVm = False
					controlVm(request,cuserid,conn,"stop",courname)
					clearExamRes(curexp)
					add_record(request.POST["stuno"], operate=u'启动实验:\"'+exp.name+u'\"的控制台', re=0, type=1)

			except Exception, diag:
				IsStartingVm = False
				logger.error(str(diag))
				conn = None
	data={}
	data["result"] = result
	othermvs={}
	clientres = Res.objects.filter(userid=cuserid, resid=curexp).order_by('-id')
	if len(clientres) > 0:
		for res in clientres:
			if res.isconsole:
				vm = None
				if result == 1:
					vm = Vm.objects.get(name=res.rname)	
				if vm:
					data["clientid"]=vm.id
				else:
					data["clientid"]=0
			elif res.rtype=="imgls":
				vm = Vm.objects.get(name=res.rname)
				othermvs[res.rname]=vm.id

		re_id = add_record(request.POST["stuno"], operate=u'启动实验:\"'+exp.name+u'\"的控制台', re=1, type=1)
		records[request.POST["stuno"]] = re_id
		data["othermvs"]=othermvs

	# 实验启动成功
	if result == 1:
		vms_list = {
			"imgls": [],
			"imgvgtls": []
		}

		for res in clientres:
			if res.rtype == "imgls":
				vmid = Vm.objects.get(name=res.rname)
				vms_list["imgls"].append(vmid.id)
			elif res.rtype == "imgvgtls":
				vmid = Vgate.objects.get(name=res.rname)
				vms_list["imgvgtls"].append(vmid.id)

		exp_add_records(curexp, cuserid, vms_list)

	return HttpResponse(json.dumps(data))


# 记录实验启动时的日期，用于统计每周和每月的Top10实验
# 记录启动的虚拟机id，使用该虚拟机的学生id，使用的实验id，以及进行实验的时间
def exp_add_records(exp_id, stu_id, vms_list):
	now_time = time.strftime("%Y-%m-%d %H:%M:%S")
	now_year = int(time.strftime("%Y"))
	now_month = int(time.strftime("%m"))
	now_week = int(time.strftime("%W"))

	# Top10相关记录
	exp_record = ExpUseRecord(expid=exp_id, year=now_year, month=now_month, week=now_week)
	exp_record.save()

	# 虚拟机使用相关记录
	stu = Student.objects.get(id=stu_id)
	stu_class = stu.clasid
	stu_department = stu_class.departmentid
	exp_name = Experiment.objects.get(id=exp_id).name

	for vm in vms_list["imgls"]:
		vm_record = VmsUseRecord(vmid=vm, vmtype="imgls", deptname=stu_department.deptname, grade=stu_class.grade,
								claname=stu_class.claname, stuname=stu.stuname, expname=exp_name, starttime=now_time)
		vm_record.save()

	for vm in vms_list["imgvgtls"]:
		vm_record = VmsUseRecord(vmid=vm, vmtype="imgvgtls", deptname=stu_department.deptname, grade=stu_class.grade,
								claname=stu_class.claname, stuname=stu.stuname, expname=exp_name, starttime=now_time)
		vm_record.save()


def gettop10(request):
	now_year = int(time.strftime("%Y"))
	now_month = int(time.strftime("%m"))
	now_week = int(time.strftime("%W"))

	# 获取所有本月的实验记录
	month_records = ExpUseRecord.objects.filter(year=now_year, month=now_month)
	# 统计每个实验使用的次数
	exp_count_month = {}
	for record in month_records:
		# 首先检查该记录对应的实验是否存在，该实验如果不存在则删除该条记录
		try:
			exp = Experiment.objects.get(id=record.expid)
			if record.expid in exp_count_month:
				exp_count_month[record.expid] += 1
			else:
				exp_count_month[record.expid] = 1
		except Experiment.DoesNotExist:	
			record.delete()

	# 对实验次数进行排序
	exp_count_list = []
	for key, value in exp_count_month.items():
		exp_count_list.append([key, value])
	# 降序排列，取前10个数据
	res = sorted(exp_count_list, key=lambda x: x[1], reverse=True)
	month_res = []
	for r in res[0:10]:
		exp = Experiment.objects.get(id=r[0])
		p_name = "-----"
		if exp.parent_id != -1:
			p = exp.parent
			while p.parent_id != -1:
				p = p.parent
			p_name = p.name
		month_res.append([p_name, exp.name])

	# 获取本周所有的实验记录
	week_records = ExpUseRecord.objects.filter(year=now_year, week=now_week)
	# 统计每个实验使用的次数
	exp_count_week = {}
	for record in week_records:
		try:
			exp = Experiment.objects.get(id=record.expid)
			if record.expid in exp_count_week:
				exp_count_week[record.expid] += 1
			else:
				exp_count_week[record.expid] = 1
		except Experiment.DoesNotExist:
			record.delete()
			
	# 对实验次数进行排序
	exp_count_list = []
	for key, value in exp_count_week.items():
		exp_count_list.append([key, value])
	# 降序排列，取前10个数据
	res = sorted(exp_count_list, key=lambda x: x[1], reverse=True)
	week_res = []
	for r in res[0:10]:
		exp = Experiment.objects.get(id=r[0])
		p_name = "-----"
		if exp.parent_id != -1:
			p = exp.parent
			while p.parent_id != -1:
				p = p.parent
			p_name = p.name
		week_res.append([p_name, exp.name])

	return HttpResponse(json.dumps({"month": month_res, "week": week_res}))


def controlCheckState(conn):
	global container_ip
	vms = Vm.objects.filter(containerIP=container_ip).order_by('-id')
	for vm in vms:
		try:
			dom = conn.lookupVM(vm.name)
			if dom.info()[0] == 5 and vm.state==1:#关机；1开机；3暂停
				vm.state=0
				vm.save()
			elif dom.info()[0] == 1 and vm.state==0:#关机；1开机；3暂停
				dom.destroy()
		except Exception:
			logger.exception('check %s error' % (vm.name))

	vms = Vgate.objects.filter(containerIP=container_ip).order_by('-id')
	for vm in vms:
		try:
			dom = conn.lookupVM(vm.name)
			if dom.info()[0] == 5 and vm.state==1:#关机；1开机；3暂停
				vm.state=0
				vm.save()
			elif dom.info()[0] == 1 and vm.state==0:#关机；1开机；3暂停
				dom.destroy()
		except Exception:
			logger.exception('check %s error' % (vm.name))
			
	return 1
	
def controlChecklab(request):
	global container_ip
	container_ip = request.POST["containerIP"]
	clients=Client.objects.filter().order_by('-id')

	host_id = 1
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None

	for c in clients:
		lastlogtime = c.lasttime.strftime('%Y-%m-%d %H:%M:%S')
		nowtime = datetime.datetime.now()
		logtime = datetime.datetime.strptime(lastlogtime, '%Y-%m-%d %H:%M:%S')
		if (nowtime-logtime).seconds > 150:
			clientres = Res.objects.filter(userid=c.studentid,restype=0).order_by('id')

			# 如果实验c启动的资源不在当前的服务器上，那么就不进行处理
			flag = False  # 如果启动实验c的服务器与当前运行的服务器不同，则flag为True
			for cres in clientres:
				ip = ""
				if cres.rtype == "imgls":
					ip = Vm.objects.get(name=cres.rname).containerIP
				elif cres.rtype == "imgvgtls":
					ip = Vgate.objects.get(name=cres.rname).containerIP
				elif cres.rtype == "imgvshls":
					ip = Vswitch.objects.get(name=cres.rname).containerIP

				if ip != "" and ip != container_ip:
					flag = True
					break
			if flag:
				continue
			for cr in clientres:
				logger.info('clear res: ' + cr.rname)
				vm = ''
				if cr.rtype =="pgate" or cr.rtype =="pswitch" or cr.rtype =="pc":
					nn=cr.rname
					try:
						p = Device.objects.get(devname=nn)
						p.state = 0
						p.examuseNo = None
						p.usetype=None
						p.save()
					except Exception,diag:
						logger.error(str(diag))
						logger.error('controlChecklab:Device get failed')

				elif cr.rtype =="imgvshls":
					br = cr.rname
					try:
						vs = Vswitch.objects.get(name=br)
						vs.delete()

						cmddel = "/usr/local/bin/ovs-vsctl del-br " + br
						os.system(cmddel)
					except:
						logger.error('controlChecklab:imgvshls get failed')

					# cmdlist = 'ovs-vsctl list-ports br0'
					# status, output=commands.getstatusoutput(cmdlist)
					# outputlist=output.split('\n')
					# if 'patch-to-eth'+br in outputlist:
					# 	cmd = "ovs-vsctl del-port br0" +' patch-to-eth'+br
					# 	os.system(cmd)

				else:
					try:
						if cr.rtype == "imgls":
							vm = Vm.objects.get(name=cr.rname)
						else:
							vm = Vgate.objects.get(name=cr.rname)
						vm.usetype=None
						vm.useNo=None
						vm.state = 0
						vm.save()
					except:
						logger.error('controlChecklab:vm or vgate get failed')
					if conn:
						try:
							dom = conn.lookupVM(vm.name)
							if dom.info()[0] == 1:
								dom.destroy()
						except libvirtError , diag:
							logger.error('controlChecklab:' + str(diag))
						try:#删掉绑定的interface
							xml = dom.XMLDesc(0)
							tree = ET.fromstring(xml)
							interface1 = tree.find("devices").findall('interface')
							for i,interface in  enumerate(interface1):
								if interface.get('type') =="direct":
									if cr.rtype=="imgls":
										interface.find('source').set('dev','br2')
									else:#vgate
										if interface.find('source').get('dev') != str(i):
											interface.find('source').set('dev',str(i))
							xx =  ET.tostring(tree)
							xml = xx
							conn.defineXML(xml)
						except libvirtError , diag:
							logger.error('controlChecklab:restore interface failed' + str(diag))
				cr.delete()
	return HttpResponse(1)

def controlRes(request,conn,teacherid,topo,examID,courname):
	global vm_vgt#遍历中心端，以br为key
	global vm_ovs#发散端，以br为key
	global rectFlag
	global g_ethlist
	global br_MacAddr
	global br_Addr
	controlCheckState(conn)
	# controlChecklab(conn)
	vm_ovs={}
	vm_vgt={}
	rectFlag={}
	g_ethlist={}
	br_MacAddr={}
	br_Addr={}

	for key, value in topo["states"].items():
		addr = value["props"]["addr"]["value"]
		imgtype= value["props"]["type"]["value"]
		imgname = value["props"]["instance"]["value"]
		textname = value["props"]["text"]["value"]
		if imgtype == "imgvshls":
			rectFlag[key]='imgvshls'
			logger.info('startovs')
			result = startovs(conn,textname,topo,teacherid,examID,key,imgtype, imgname, addr,courname)
			logger.info('startovs end')
			if result !=1:
				return result
		elif imgtype == "pswitch":
			rectFlag[key]='pswitch'
			logger.info('startpswitch')
			result = startpswitch(conn,textname,topo,teacherid,examID,key,imgtype, imgname, addr,courname)
			logger.info('startpswitch end')
			if result !=1 and result !=None:
				return result
		elif imgtype=="imgvgtls":
			rectFlag[key]='imgvgtls'
			logger.info('startvgt')
			result = startvgt(conn,textname,topo,teacherid,examID,key,imgtype, imgname, addr,courname)
			logger.info('startvgt end')
			if result !=1:
				return result

		elif imgtype=="pgate":
			rectFlag[key]='pgate'
			logger.info('startpgate')
			result = startpgate(conn,textname,topo,teacherid,examID,key,imgtype, imgname, addr,courname)
			logger.info('startpgate end')
			if result !=1 and result !=None:
				return result


	logger.info('before starting all vms !')

	for key, value in topo["states"].items():
		addr = value["props"]["addr"]["value"]
		imgtype= value["props"]["type"]["value"]
		imgname = value["props"]["instance"]["value"]
		textname = value["props"]["text"]["value"]
		if imgtype != "imgvshls" and imgtype != "pswitch":
			result = startvms(conn,textname,topo,teacherid,examID,key,imgtype, imgname, addr,courname)
			if result !=1:
				return result
	logger.info('after starting all vms !')

	#根据br_MacAddr和br_Addr中的记录往VgateRes表里填写vgate的eth对应的path上字段
	for key in br_MacAddr:
		if br_MacAddr[key] in br_Addr:
			keymac=key.split(',')
			vr = VgateRes(vgateName=keymac[0],macAddr=keymac[1],pathKey=br_Addr[br_MacAddr[key]][0],pathtext=br_Addr[br_MacAddr[key]][1],userid=teacherid,restype=0,resid=examID)
			vr.save()

	logger.info('after saving  vgate internet access information!')

	return 1

def startovs(conn,textname,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr,courname):	
	global vm_ovs
	global br_Addr
	global container_ip

	if imgbrtype == "imgvshls":
		try:
			br = createbr()
			logger.info('create br: ' + br)
			cmd = "/usr/local/bin/ovs-vsctl add-br " + br
			os.system(cmd)
			logger.info('create ' + br + ' end')
			examres = Res(userid=teacherid,rectname=brkey,rname=br,insname=imgbrname,rtype=imgbrtype,resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
		except Exception,diag:
			logger.error('startovs:' + str(diag))
			# return 0
			return u'添加%s失败' % (br)
		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			recttotype = topo["states"][rectto]["props"]["type"]["value"]
			rectfromtype = topo["states"][rectfrom]["props"]["type"]["value"]

			pathtext = value["text"]["text"]


			if brkey == rectfrom:
				brname = createbr()
				cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
				os.system(cmd)
				examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
				examres.save()
				cmd1 = "/usr/local/bin/ovs-vsctl add-port "+br+" patch-to-"+brname
				os.system(cmd1)
				cmd4 = "/usr/local/bin/ovs-vsctl add-port "+brname+" patch-to-"+br+brname
				os.system(cmd4)
				cmd2 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+brname+" type=patch"
				os.system(cmd2)
				cmd3 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+brname+" options:peer=patch-to-"+br+brname
				os.system(cmd3)
				cmd5 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+br+brname+" type=patch"
				os.system(cmd5)
				cmd6 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+br+brname+" options:peer=patch-to-"+brname
				os.system(cmd6)

				vm_ovs[brname] = rectto

				#添加到绑定mac地址的全局变量
				if recttotype=="imgvgtls":
					br_Addr[brname]=[key,pathtext]

			elif brkey == rectto:
				brname = createbr()
				cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
				os.system(cmd)
				examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=br,rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
				examres.save()
				cmd7 = "/usr/local/bin/ovs-vsctl add-port "+br+" patch-to-"+brname
				os.system(cmd7)
				cmd10 = "/usr/local/bin/ovs-vsctl add-port "+brname+" patch-to-"+br+brname
				os.system(cmd10)
				cmd8 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+brname+" type=patch"
				os.system(cmd8)
				cmd9 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+brname+" options:peer=patch-to-"+br+brname
				os.system(cmd9)
				cmd11 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+br+brname+" type=patch"
				os.system(cmd11)
				cmd12 = "/usr/local/bin/ovs-vsctl set interface patch-to-"+br+brname+" options:peer=patch-to-"+brname
				os.system(cmd12)

				vm_ovs[brname] = rectfrom

				if rectfromtype=="imgvgtls":
					br_Addr[brname]=[key,pathtext]
		return 1

def startpswitch(conn,textname,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr,courname):	
	global vm_ovs
	global g_ethlist

	global rectFlag
	global br_Addr
	global container_ip
	ps = None

	if imgbrtype == "pswitch":
		try:
			ps = Device.objects.get(devname=imgbrname,devtype="pswitch",state=0)
			examres = Res(userid=teacherid,rectname=brkey,rname=imgbrname,insname=imgbrname,rtype="pswitch",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			ps.state = 1
			ps.examuseNo = courname
			ps.usetype=0
			ps.save()
			ethx = ps.ethx
			if ethx == None:
				return 
			g_ethlist[brkey] = ethx.split(',')
		except Exception,diag:
			logger.error('startpswitch:' + str(diag))
			return 3#物理资源不够

		
		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			pathtext = value["text"]["text"]

			if brkey == rectfrom:
				tecttotype=topo["states"][rectto]["props"]["type"]["value"]
				if tecttotype=="imgls"or tecttotype=="imgvgtls" :
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey] !=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
							vm_ovs[brname] = rectto
						except Exception:
							logger.error('startpswitch: 1get eth failed')
							# return 0
							return 'startpswitch: 1get eth failed'
						g_ethlist[brkey].pop(0)

						if tecttotype=="imgvgtls":
							br_Addr[brname]=[key,pathtext]

					else:
						return 5
				elif tecttotype=="pc" or tecttotype=="pgate" or (tecttotype=="pswitch"and rectto not in rectFlag):
					
					imgname = topo["states"][rectto]["props"]["instance"]["value"]
					device = Device.objects.get(devname=imgname)			
					ethx = device.ethx
					if not ethx == None:#eth为空时则说明没有添加到咱们平台上，直接使用网线连接
						if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
							brname = createbr()
							cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
							os.system(cmd)
							cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
							os.system(cmd1)
							try:
								examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
								vm_ovs[brname] =rectto
							except Exception:
								logger.error('startpswitch: 2get eth failed')
								# return 0
								return 'startpswitch: 2get eth failed'
							g_ethlist[brkey].pop(0)
						else:
							return 5
			if brkey == rectto:
				tectfromtype=topo["states"][rectfrom]["props"]["type"]["value"]
				if tectfromtype=="imgls"or tectfromtype=="imgvgtls" :
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
							vm_ovs[brname] = rectfrom
						except Exception:
							logger.error('startpswitch: 3get eth failed')
							# return 0
							return 'startpswitch: 3get eth failed'
						g_ethlist[brkey].pop(0)

						if tectfromtype=="imgvgtls":
							br_Addr[brname]=[key,pathtext]
					else:
						return 5
				elif tectfromtype=="pc" or tectfromtype=="pgate" or (tectfromtype=="pswitch"and rectfrom not in rectFlag):
					imgname = topo["states"][rectfrom]["props"]["instance"]["value"]
					device = Device.objects.get(devname=imgname)
					ethx = device.ethx
					if not ethx == None:#eth为空时则说明没有添加到咱们平台上，直接使用网线连接
						if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
							brname = createbr()
							cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
							os.system(cmd)
							cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
							os.system(cmd1)
							try:
								examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=braddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
								vm_ovs[brname] = rectfrom
							except Exception:
								logger.error('startpswitch: 4get eth failed')
								# return 0
								return 'startpswitch: 4get eth failed'
							g_ethlist[brkey].pop(0)
						else:
							return 5
		return 1

def startvgt(conn,textname,topo,teacherid,examID,vgtkey,imgvgttype, imgvtname, vgtaddr,courname):
	global vm_vgt
	global vm_ovs
	global rectFlag
	global container_ip
	if imgvgttype == 'imgvgtls':
		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			pathtext = value["text"]["text"]

			recttotype = topo["states"][rectto]["props"]["type"]["value"]
			rectfromtype = topo["states"][rectfrom]["props"]["type"]["value"]
			if vgtkey==rectfrom and  (recttotype== "imgls" or recttotype== "pc" or (recttotype== "imgvgtls" and rectto not in rectFlag) or recttotype== "pgate"):
				try:
					brname = createbr()
					cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
					os.system(cmd)
					examres = Res(userid=teacherid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=vgtaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()	
				except Exception,diag:
					logger.error(str(diag))
					# return 0
					return u'添加%s失败' % (brname)			
				vm_ovs[brname] = rectto
				if recttotype=="imgls" and int(topo["states"][rectto]["props"]["isconsole"]["value"]):#记录控制台
					vm_vgt[brname] = [vgtkey,1]
				else:
					vm_vgt[brname] = [vgtkey]

				br_Addr[brname]=[key,pathtext]

			if vgtkey==rectto and (rectfromtype== "imgls" or rectfromtype== "pc" or (rectfromtype== "imgvgtls" and rectfrom not in rectFlag) or rectfromtype== "pgate"):
				try:
					brname = createbr()
					cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
					os.system(cmd)
					examres = Res(userid=teacherid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=vgtaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()
				except Exception,diag:
					logger.error(str(diag))
					# return 0
					return u'添加%s失败' % (brname)
				vm_ovs[brname] = rectfrom
				if rectfromtype=="imgls" and int(topo["states"][rectfrom]["props"]["isconsole"]["value"]):#记录控制台
					vm_vgt[brname] = [vgtkey,1]
				else:
					vm_vgt[brname] = [vgtkey]

				# if rectfromtype=="imgvgtls":
				br_Addr[brname]=[key,pathtext]

	return 1

def startpgate(conn,textname,topo,teacherid,examID,gtkey,gttype, gtname, gtaddr,courname):
	global vm_vgt
	global vm_ovs
	global g_ethlist
	global rectFlag
	global container_ip
	pg = None
	if gttype == 'pgate':
		try:
			pg = Device.objects.get(devname=gtname,devtype="pgate",state=0)
			examres = Res(userid=teacherid,rectname=gtkey,rname=gtname,insname=gtname,rtype="pgate",resid=examID,coursename=courname,containerIP=container_ip,addr=gtaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pg.state = 1
			# expn = Experiment.objects.get(id=examID).name
			pg.examuseNo = courname
			pg.usetype=0
			pg.save()

			ethx= pg.ethx
			if ethx == None:
				return
			g_ethlist[gtkey] = ethx.split(',')
		except :
			logger.error('startpgate:get pgate Device failed')
			return 3#物理资源失败

		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			recttotype = topo["states"][rectto]["props"]["type"]["value"]
			rectfromtype = topo["states"][rectfrom]["props"]["type"]["value"]
			if gtkey==rectfrom:
				if recttotype== "imgls":
					if g_ethlist[gtkey]!=[''] and g_ethlist[gtkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[gtkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=gtaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
						except :
							logger.error('startpgate:1get pgate eth Device failed')
							# return 0
							return 'startpgate:1get pgate eth Device failed'

						g_ethlist[gtkey].pop(0)
						vm_ovs[brname] = rectto
					else:
						return 5
				elif  recttotype == "pc" or (recttotype== "pgate" and rectto not in rectFlag):
					imgname = topo["states"][rectto]["props"]["instance"]["value"]
					device = Device.objects.get(devname=imgname)			
					ethx = device.ethx
					if not ethx == None:#eth为空时则说明没有添加到咱们平台上，直接使用网线连接
						if g_ethlist[gtkey]!=[''] and g_ethlist[gtkey]!=[]:
							brname = createbr()
							cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
							os.system(cmd)
							cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[gtkey][0]
							os.system(cmd1)
							try:
								examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,coursename=courname,containerIP=container_ip,addr=gtaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
							except :
								logger.error('startpgate:2get pgate eth Device failed')
								# return 0
								return 'startpgate:2get pgate eth Device failed'

							g_ethlist[gtkey].pop(0)
							vm_ovs[brname] = rectto
						else:
							return 5

			elif gtkey==rectto:
				if rectfromtype== "imgls":
					if g_ethlist[gtkey]!=[''] and g_ethlist[gtkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[gtkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,coursename=courname,containerIP=container_ip,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
						except :
							logger.error('startpgate:3get pgate eth Device failed')
							# print "get eth failed"
							# return 0
							return 'startpgate:3get pgate eth Device failed'
						g_ethlist[gtkey].pop(0)
						vm_ovs[brname] = rectfrom
					else:
						return 5
				elif rectfromtype == "pc" or (rectfromtype== "pgate" and rectfrom not in rectFlag):
					imgname = topo["states"][rectfrom]["props"]["instance"]["value"]
					device = Device.objects.get(devname=imgname)			
					ethx = device.ethx
					if not ethx == None:#eth为空时则说明没有添加到咱们平台上，直接使用网线连接
						if g_ethlist[gtkey]!=[''] and g_ethlist[gtkey]!=[]:
							brname = createbr()
							cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
							os.system(cmd)
							cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[gtkey][0]
							os.system(cmd1)
							try:
								examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,coursename=courname,containerIP=container_ip,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
							except :
								logger.error('startpgate:4get pgate eth Device failed')
								# print "get eth failed"
								# return 0
								return 'startpgate:4get pgate eth Device failed'
							g_ethlist[gtkey].pop(0)
							vm_ovs[brname] = rectfrom
						else:
							return 5
	return 1

def startvms(conn,textname,topo,teacherid,examID,key,imgtype,imgname,vmaddr,courname):
	global vm_ovs
	global vm_vgt
	global g_ethlist
	global groQueInfilTopo
	global container_ip
	pc =None
	ethlist = None
	statetext=topo["states"][key]["vm"]
	if imgtype == "imgls":
		vmisconsole=int(topo["states"][key]["props"]["isconsole"]["value"])
		try:
			imgid = Img.objects.get(name=imgname).id
		except:
			logger.error('startvms:vmimg not exist')
			return 4
		vms = Vm.objects.filter(state=0, imgtype=imgid, containerIP=container_ip).order_by('id')
		
		if  vms:
			if conn:
				if len(vms) > 0:
					vmname = vms[0].name
					logger.info('start vm: ' + vmname)
					try:
						dom = conn.lookupVM(vmname)
						vm_br(conn,dom,imgtype,vmname,vmaddr,key)
						vmmac1 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[1]/mac/@address")
						vmmac2 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[2]/mac/@address")
						if not vmmac1:
							vmmac1=""
						if not vmmac2:
							vmmac2=""
						# print "dom :",dom
						dom.create()

						time.sleep(3)
						#vmMgr.RequestList.put(dom)

						vm = Vm.objects.get(name=vms[0].name)
						examres = Res(userid=teacherid,rectname=textname,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,coursename=courname,containerIP=container_ip,mac1=vmmac1,mac2=vmmac2,addr=vmaddr,restype=0,isconsole=vmisconsole,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
						examres.save()
						
						strinfo = re.compile('\''+statetext+'\'')
						groQueInfilTopo=strinfo.sub('\''+vmname+'**\'',groQueInfilTopo)
						
						vm.state=1#启动
						vm.usetype=0
						vm.useNo=courname
						vm.save()
					except Exception:
						# logger.error('startvms:vm start failed,'+str(diag))
						logger.exception('startvms:%s start failed' % (vmname))
						# return 0
						return u'启动%s失败' % (vmname)
		#资源不够
		else:
			return 2

	elif imgtype=="pc":
		try:
			pc = Device.objects.get(devname=imgname,devtype="pc",state=0)			
			ethx = pc.ethx
			if ethx == None:
				ethx=''
			ethlist = ethx.split(',')
		except :
			logger.error('startvms:get pc Device failed')
			return 3#物力资源不够
		
		if ethlist!=['']:
			examres = Res(userid=teacherid,rectname=key,rname=imgname,insname=imgname,rtype="pc",resid=examID,coursename=courname,containerIP=container_ip,addr=vmaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pc.state = 1
			# expn = Experiment.objects.get(id=examID).name
			pc.examuseNo = courname
			pc.usetype=0
			pc.save()
		
			for brname in vm_ovs:
				if key == vm_ovs[brname]:
					if ethlist!=[''] and ethlist!=[]:
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+ethlist[0]
						os.system(cmd1)
						ethlist.pop(0)
						br_Addr[brname]=vmaddr

					else:
						return 5
			
	elif imgtype=="imgvgtls":#防火墙是虚拟墙
		try:
			imgvgtid = ImgVgt.objects.get(name=imgname).id
		except:
			logger.error('startvms:vgtimg not exist')
			return 4
		vms = Vgate.objects.filter(state=0, imgtype=imgvgtid, containerIP=container_ip).order_by('-id')
		if  vms:
			if conn:
				try:
					vmname = vms[0].name
					logger.info('start vgt: ' + vmname)
					dom = conn.lookupVM(vmname)
					vm_br(conn,dom,imgtype,vmname,vmaddr,key)

				except libvirtError ,diag:
					logger.error('startvms:'+str(diag))
					# return 0
					return u'启动%s失败' % (vmname)
				try:
					vmmac1 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[1]/mac/@address")
					vmmac2 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[2]/mac/@address")
					if not vmmac1:
						vmmac1=""
					if not vmmac2:
						vmmac2=""

					dom.create()
					time.sleep(3)
					#vmMgr.RequestList.put(dom)

					vm = Vgate.objects.get(name=vms[0].name)
					examres = Res(userid=teacherid,rectname=key,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,coursename=courname,containerIP=container_ip,mac1=vmmac1,mac2=vmmac2,addr=vmaddr,restype=0,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()
					strinfo = re.compile('\''+statetext+'\'')
					groQueInfilTopo=strinfo.sub('\''+vmname+'**\'',groQueInfilTopo)

					vm.state=1
					vm.usetype=0
					vm.useNo=courname
					vm.save()
				except libvirtError ,diag:
					logger.error('startvms:vgate start failed,'+str(diag))
					# return 0
					return u'启动%s失败' % (vmname)
					#pass
		else:
			return 2#资源不足

	elif imgtype=="pgate":#防火墙是物理墙	
		for brname in vm_ovs:
			if key == vm_ovs[brname]:
				if g_ethlist[key]:
					cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[key][0]
					os.system(cmd1)
					g_ethlist[key].pop(0)
				else:
					return 5#网卡不足	
	elif imgtype=="pswitch":#物理交换机被连接在虚拟交换机上了，只做了终端，所以只存在vm_ovs里面	
		for brname in vm_ovs:
			if key == vm_ovs[brname]:
				if g_ethlist[key]:
					cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[key][0]
					os.system(cmd1)
					g_ethlist[key].pop(0)
				else:
					return 5#网卡不足	
	return 1

def vm_br(conn,dom,imgtype,vmname,addr,key):
	global vm_ovs
	global vm_vgt
	global br_MacAddr
	global br_Addr
	frebr=['0','1','2','3','4',]
	if imgtype=="imgvgtls":
		for brname in vm_vgt:#第一次遍历用掉vgate的eth0,绑定控制台
			if len(vm_vgt[brname])==2:#如果控制台连接vgate,它的值为长度为2的数组。
				if key == vm_vgt[brname][0]:
					xml=dom.XMLDesc(0)
					tree = ET.fromstring(xml)
					interface = tree.find("devices").findall("interface")[0]
					devnum = interface.find('source').get('dev')
					interface.find('source').set('dev',brname)
					br_MacAddr[vmname+','+'eth'+devnum] = brname
					xx =  ET.tostring(tree)
					xml = xx
					conn.defineXML(xml)
					break
		for brname in vm_vgt:#正常遍历非控制台的vgate和vm
			if len(vm_vgt[brname])==1 and key == vm_vgt[brname][0]:
				try:
					xml=dom.XMLDesc(0)
					tree = ET.fromstring(xml)
					interface1 = tree.find("devices").findall("interface")
					for interface in interface1:
						devnum = interface.find('source').get('dev')
						if interface.get('type') =="direct" and  devnum in frebr:
							interface.find('source').set('dev',brname)
							# macaddr=interface.find('mac').get('address')
							br_MacAddr[vmname+','+'eth'+devnum] = brname
							break
					xx =  ET.tostring(tree)
					xml = xx
					conn.defineXML(xml)
				except libvirtError ,diag:
					logger.error('vm_br:2xml  failed,'+str(diag))
					return 0
	for brname in vm_ovs:
		if key==vm_ovs[brname]:
			try:
				xml=dom.XMLDesc(0)
				tree = ET.fromstring(xml)
				interface1 = tree.find("devices").findall("interface")
				if imgtype=="imgls":
					for interface in interface1:
						if interface.get('type') =="direct":
							interface.find('source').set('dev',brname)					
				else:
					for interface in interface1:
						devnum = interface.find('source').get('dev')
						if interface.get('type') =="direct" and  devnum in frebr:
							interface.find('source').set('dev',brname)
							# macaddr=interface.find('mac').get('address')
							br_MacAddr[vmname+','+'eth'+devnum] = brname
							break
					# devices = tree.find("devices")
					# num=len(devices.findall("interface"))+1

					# elem = ET.Element("interface", {'type': 'direct', })
					# elem1 = ET.Element("source", {'dev': brname, 'mode':'bridge',})
					# elem.append(elem1)
					# devices.append(elem)

				xx =  ET.tostring(tree)
				xml = xx
				conn.defineXML(xml)
				# if imgtype=="imgvgtls":
				# 	macaddr=get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[%s]/mac/@address" % 1)
				# 	br_MacAddr[vmname+','+macaddr] = brname
			except libvirtError ,diag:
				logger.error('vm_br:1xml  failed,'+str(diag))
				return 0
	

def clearExamRes(examID):
	res = Res.objects.filter(Q(resid=examID) & Q(restype = 0))
	for r in res:
		r.delete()

def checkBrs():
	"""服务器重启后，将所有vm的br改为br2，所有vgate的br改为0,1,2,3,4"""
	vms = Vm.objects.all()
	vgts = Vgate.objects.all()

	try:
		host = Host.objects.get(id=1)
		conn = ConnServer(host)

		for vm in vms:
			try:
				dom = conn.lookupVM(vm.name)
				xml = dom.XMLDesc(0)
				tree = ET.fromstring(xml)
				interface1 = tree.find("devices").findall('interface')
				for i, interface in  enumerate(interface1):
					if interface.get('type') == "direct":
						interface.find('source').set('dev','br2')
				xml = ET.tostring(tree)
				os.system('virsh undefine %s --managed-save' % (vm.name))
				conn.defineXML(xml)
			except Exception:
				logger.exception('check brs error: ' + vm.name)

		for vgt in vgts:
			try:
				dom = conn.lookupVM(vgt.name)
				xml = dom.XMLDesc(0)
				tree = ET.fromstring(xml)
				interface1 = tree.find("devices").findall('interface')
				for i, interface in  enumerate(interface1):  # i是索引
					if interface.get('type') == "direct":
						if interface.find('source').get('dev') != str(i):
							interface.find('source').set('dev',str(i))
				xml = ET.tostring(tree)
				os.system('virsh undefine %s --managed-save' % (vgt.name))
				conn.defineXML(xml)

				#删除vgate记录的mac地址
				vr = VgateRes.objects.filter(vgateName=vgt.name)
				for v in vr:
					v.delete()
			except Exception:
				logger.exception('check brs error: ' + vgt.name)

	except Exception:
		logger.exception('check brs error!')


#回收资源
def controlVm(request,examid,conn,sptype,courname):
	resvms = Res.objects.filter(userid=examid, restype=0)  #restype字段的意思是：0代表实训；1代表竞赛；2代表攻防
	for resvm in resvms:
		if sptype=="stop":
			if resvm.rtype=="imgvshls" :
				if conn :
					br = resvm.rname
					try:
						cmddel = "/usr/local/bin/ovs-vsctl del-br " + br
						os.system(cmddel)
						vm=Vswitch.objects.get(name=br)
						vm.delete()
					except:
						logger.error("Vswitch or cmddel failed")
						return 0
			elif resvm.rtype=="pswitch" :
				pswitch = Device.objects.filter(devtype="pswitch",examuseNo=courname,usetype=0)
				for ps in pswitch:
					ps.examuseNo = None
					ps.usetype = None
					ps.state = 0
					ps.save()
			elif resvm.rtype=="pc" :
				pcs = Device.objects.filter(devtype="pc",examuseNo=courname,usetype=0)
				for pc in pcs:
					pc.state = 0
					pc.examuseNo = None
					pc.usetype = None
					pc.save()
			elif resvm.rtype=="pgate":
				pgate = Device.objects.filter(devtype="pgate",examuseNo=courname,usetype=0)
				for pg in pgate:
					pg.examuseNo = None
					pg.usetype = None
					pg.state = 0
					pg.save()
		vmgt=None
		if resvm.rtype=="imgls":
			vmgt = Vm.objects.get(name=resvm.rname)
		elif resvm.rtype=="imgvgtls":
			vmgt=Vgate.objects.get(name=resvm.rname)
		if conn and vmgt:
			dom = conn.lookupVM(vmgt.name)
			if sptype == "stop":
				try:
					dom.destroy()
				except:
					pass
				vmgt.usetype=None
				vmgt.useNo=None
				vmgt.state=0#停止
				try:
					xml = dom.XMLDesc(0)
					tree = ET.fromstring(xml)
					interface1 = tree.find("devices").findall('interface')
					for i,interface in  enumerate(interface1):#i是索引
						if interface.get('type') =="direct":
							if resvm.rtype=="imgls":
								interface.find('source').set('dev','br2')
							else:#vgate
								if interface.find('source').get('dev') != str(i):
									interface.find('source').set('dev',str(i))
								# tree.find("devices").remove(interface)
					xx =  ET.tostring(tree)
					xml = xx
					conn.defineXML(xml)

					if resvm.rtype=="imgvgtls":#删除vgate记录的mac地址
						vr=VgateRes.objects.filter(vgateName=vmgt.name)
						for v in vr:
							v.delete()

				except Exception ,diag:
					logger.error('controlVm:'+str(diag))

			elif sptype =="resume":
				dom.resume()
				vmgt.state = 1#启动
			else:#sptype =="suspend"
				dom.suspend()
				vmgt.state=2#暂停，Vm数据表使用的是bool类型？？？？？？
			vmgt.save()

		resvm.delete()
	conn.close()
	return 1


def stopVM(request):
    if request.method == 'POST':
        if not 'cusername' in request.session:
            return HttpResponseRedirect('/client/')
        cuserid = request.session['cuserid']
        curexp = int(request.POST['curexp'])
        expid = int(request.POST['expid'])
        courname = request.POST['courname']
        curvms = int(request.POST['curvms'])
        stuno = request.session["stuno"]
        datas = {'cuserid': cuserid, 'curexp': curexp, 'expid': expid, 'courname': courname, 'curvms': curvms, 'stuno': stuno}
        # 通过实验名称，找到使用的虚拟设备，获取虚拟设备所在的宿主机ip，然后将请求发送给宿主机，关闭虚拟机
        res = Res.objects.filter(userid=cuserid, resid=curexp, rtype="imgls")
        if len(res) > 0:
            ip = Vm.objects.get(name=res[0].rname).containerIP
        else:
            res = Res.objects.filter(userid=cuserid, resid=curexp, rtype="imgvgtls")
            if len(res) > 0:
                ip = Vgate.objects.get(name=res[0].rname).containerIP
            else:
                res = Res.objects.filter(userid=cuserid, resid=curexp, rtype="imgvshls")
                ip = Vswitch.objects.get(name=res[0].rname).containerIP
        data = post("http://" + ip + "/stopBench/", datas)
        return HttpResponse(data)


def stopBench(request):
	global groQueInfilTopo
	global records
	result=0
	cuserid = request.POST['cuserid']
	c = Client.objects.get(studentid=cuserid)
	c.copytopo = None
	c.save()
	if request.method == 'POST':
			curexp = int(request.POST['curexp'])
			expid = int(request.POST['expid'])
			courname = request.POST['courname']
			curvms = int(request.POST['curvms'])

			exp = Experiment.objects.get(id=curexp)

			host_id = 1
			host = Host.objects.get(id=host_id)
			try:
				conn = ConnServer(host)
				result = controlVm(request,cuserid,conn,"stop",courname)
				
			except libvirtError ,diag:
				add_record(request.POST["stuno"], operate=u'关闭实验:\"'+exp.name+u'\"的控制台', re=0, type=1)
				logger.error('stopBench:'+str(diag))
				conn = None
	data={}
	data["clientid"]=0

	try:
		rec = Records.objects.get(id=records[request.POST["stuno"]])
		rec.save()
		del records[request.POST["stuno"]]
	except Exception:
		add_record(request.POST["stuno"], operate=u'关闭实验:\"'+exp.name+u'\"的控制台', re=1, type=1)

	return HttpResponse(json.dumps(data))

def createbr():
	global container_ip
	brname =''
	ovs = ImgVsh.objects.get(name='OVS')
	brs = Vswitch.objects.order_by('id')
	count = len(brs) + 1 + 100
	index = 100
	ip = container_ip
	while index < count:
		brname = 'br' + str(index)
		vm = Vswitch.objects.filter(name=brname)
		if len(vm) > 0:
			pass
		else:
			vm = Vswitch(
					name=brname, 
					mgrip='', 
					imgtype_id=ovs.id, 
					mgrport=9000, 
					state=0,
					remark='',
					containerIP=ip)
			vm.save()
			break
		index = index + 1
	return brname

def vmHost(request, ip, mac2):
	data = ''
	try:
		clientres = Res.objects.filter(mac2__iexact=mac2)
		if clientres.count()<=0:
			clientres = Res.objects.filter(mac1__iexact=mac2)
		data = '{"Ip": "%s", "mac2":"%s"}' %(clientres[0].addr, mac2)
	except:
		data = '{"Ip":"192.168.1.25", "mac2":"%s"}' %mac2
	params = json.loads(data)
	return HttpResponse(json.dumps(params))

def vgateSet(request, json):
	params = ''
	return HttpResponse(json.dumps(params))

def configvm():
	host_id = 1
	vid = int(vid)
	vm = Vm.objects.get(id=vid) 
	vname = vm.name 
	errors = []
	messages = []
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None
	if not conn:
		errors.append(e.message)
	else:
		dom = conn.lookupVM(vname)
		try:
			dom.create()
			time.sleep(3)
			vm.state = 1
			vm.save()
		except libvirtError as msg_error:
			errors.append(msg_error.message)
def submitflags(request):
	iscorrect = False
	temp =""
	data={}
	data['issubmit'] = 'false'

	# print request.session["exam_id"]
	exm =Examinations.objects.get(id = request.session["exam_id"])
	if request.method=="POST" and exm.examStatus == 2:
		try:
			con =  json.loads(request.POST["flaghidden"])
		except:
			# print "this is not flaghidden"
			pass
		gopid =ExamGroup.objects.filter(examID_id = request.session["exam_id"])
		gpid = GroupMembers.objects.filter(studentid_id = request.session["cuserid"])
		for gp in gpid:
			for gop in gopid: 	
				if gp.groupid_id == gop.groupID_id:
					temp = gop.groupID_id

		#判断是否已经提交过基础题			
		ans = AnswerInfo.objects.filter(groupid_id=temp,examid=request.session["exam_id"],anstype=1)
		for an in ans:
			if an.queid.qtype=='1':
				data['issubmit'] = 'true'
				return HttpResponse(json.dumps(data))

		for key,value in con.items():
			opp=""
			qtinfo = Choose.objects.get(queid_id=key)#选择题题目
			options = Option.objects.order_by('id').filter(choid_id=qtinfo.id)
			for op in options:
				if op.isresult == '1':
					opp+=op.oid
			if opp==value:
				iscorrect = True
			AnswerInfo(groupid_id=temp,examid=request.session["exam_id"],keyid=1,is_correct= iscorrect,extime = datetime.datetime.now(),queid_id=key,answer=value).save()
		data["istart"] = "true"
	else:#竞赛已经关闭
		data["istart"] = "false"
	return HttpResponse(json.dumps(data))
#********5555555555555个选择题
# def submitexamque(request):
# 	iscorrect = False
# 	temp =""
# 	flag = 0
# 	# print request.session["exam_id"]
# 	if request.method=="POST":
		
# 		try:
# 			con = json.loads(request.POST["skillhidden"])
# 		except:
# 			# print "this is not skillhidden"
# 			pass
# 		try:
# 			con = json.loads(request.POST["totalhidden"])
# 		except:
# 			# print "this is not totalhidden"
# 			pass

# 		gopid =ExamGroup.objects.filter(examID_id = request.session["exam_id"])
# 		exm =Examinations.objects.get(id = request.session["exam_id"])
# 		gpid = GroupMembers.objects.filter(studentid_id = request.session["cuserid"])
# 		for gp in gpid:
# 			for gop in gopid: 	
# 				if gp.groupid_id == gop.groupID_id:
# 					temp = gop.groupID_id
# 		questionsid = con["qid"] / 10
# 		keyid = con["qid"] % 10

# 		que = PaperQuestion.objects.get(id=questionsid)
# 		qtype = Question.objects.get(id=que.questionid_id)
# 		opp=""

# 		if qtype.qtype == '2':
# 			qtinfo = Skill.objects.get(queid_id=que.questionid_id)
# 			if qtinfo.result == con["ans"]:
# 				iscorrect = True
# 				flag = 2

# 		if qtype.qtype == '3':		
# 			qtinfo = Infiltration.objects.get(queid_id=que.questionid_id)
# 			result = qtinfo.result.split(",")
# 			if result[keyid-1] == con["ans"]:
# 				iscorrect = True
# 				flag=3
# 		ansinfo = AnswerInfo(groupid_id = temp,examid = con["examid"],keyid=keyid,is_correct= iscorrect,extime = datetime.datetime.now(),queid_id=que.questionid_id,answer=con["ans"])
		
# 		if exm.examStatus != 2:
# 			con["istart"] = "false"
# 		else:
# 			if flag == 1:
# 				ansinfo.save()
# 			if flag == 2:
# 				con["istart"] = "skilltrue"
# 				haveans=AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,is_correct= iscorrect,queid_id=que.questionid_id)
# 				if  haveans.count()>0:
# 					con["istart"] = "haveskillans"
# 				else:
# 					ansinfo.save()
# 			if flag == 3:
# 				con["istart"] = "totaltrue"
# 				haveans=AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,is_correct= iscorrect,queid_id=que.questionid_id)
# 				if  haveans.count()>0:
# 					con["istart"] = "havetotalans"
# 				else:
# 					ansinfo.save()

# 	return HttpResponse(json.dumps(con))
def submitexamque(request):
	iscorrect = False
	temp =""
	flag = 0
	if request.method=="POST":
		
		try:
			con = json.loads(request.POST["shidden"])
		except:
			pass
		
		gopid =ExamGroup.objects.filter(examID_id = con["examid"])
		exm =Examinations.objects.get(id = con["examid"])

		gpid = GroupMembers.objects.filter(studentid_id = request.session["cuserid"])
		for gp in gpid:
			for gop in gopid: 	
				if gp.groupid_id == gop.groupID_id:
					temp = gop.groupID_id
		
		questionsid = con["qid"] / 10
		keyid = con["qid"] % 10
		
		que = PaperQuestion.objects.get(id=questionsid)
		qtype = Question.objects.get(id=que.questionid_id)
		opp=""
		if qtype.qtype == '1':
			if AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,queid_id=que.questionid_id):
				flag = -1
			else:
				flag = 1
				qtinfo = Choose.objects.get(queid_id=que.questionid_id)#选择题题目
				options = Option.objects.order_by('id').filter(choid_id=qtinfo.id)
				for op in options:
					if op.isresult == '1':
						opp+=op.oid
				if opp==con["ans"]:
					iscorrect = True
							
		if qtype.qtype == '4':		
			iscorrect = True
			if AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,queid_id=que.questionid_id):
				flag = -1
			else:
				flag = 4
			

		if qtype.qtype == '2':
			qtinfo = Skill.objects.get(queid_id=que.questionid_id)
			if qtinfo.result == con["ans"]:
				iscorrect = True
				#查看之前是否已经答过该题目
				if AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,queid_id=que.questionid_id):
					flag = -1
				else:
					flag = 2

		if qtype.qtype == '3':		
			qtinfo = Infiltration.objects.get(queid_id=que.questionid_id)
			result = qtinfo.result.split(",")
			if result[keyid-1] == con["ans"]:
				iscorrect = True
				#判断之前是否已经答过该题目
				if AnswerInfo.objects.filter(groupid_id = temp,examid = con["examid"],keyid=keyid,queid_id=que.questionid_id):
					flag = -1
				else:
					flag = 3
				
		print "-----------------"
		print con["examid"]
		print "groupid     ",temp
		print que.questionid_id
		print keyid

		ansinfo = AnswerInfo(groupid_id = temp,examid = con["examid"],keyid=keyid,is_correct= iscorrect,extime = datetime.datetime.now(),queid_id=que.questionid_id,answer=con["ans"])
		print "dddddddddddddddddddddddddddddd"
		data={}
		data["flag"] = flag
		data["istart"] = "false"
		data['issave'] = 'false'
		if exm.examStatus != 2:
			data["istart"] = "false"
		else:
			data["istart"] = "true"
			if flag != -1 and flag != 0:
				data['issave'] = 'true'
				#添加不让重复答题的功能
				ansinfo.save()
			else:
				data['issave'] = 'false'
		print json.dumps(data)
	return HttpResponse(json.dumps(data))
def submitans(request):
	iscorrect = False
	global grid
	if request.method=="POST":
		try:
			con = json.loads(request.POST["totalhidden"])
		except:
			# print "this is error!"
			pass
		#gopid =AtkdfsGroup.objects.filter(id = request.session['hack_id'])
		atkdfs =Atkdfs.objects.get(id = request.session['hack_id'])
		groupids = AtkdfsGroup.objects.filter(atkdfsID_id=request.session['hack_id'])
		groupers = GroupMembers.objects.filter(studentid_id=request.session['cuserid'])
	    #获取唯一的参加对抗的团队ID
		for gr in groupids:
			for gs in groupers:
				if gr.groupID_id == gs.groupid_id:
					gro_id =  gr.groupID_id
					g_name =Group.objects.get(id=gro_id)
					grid = gro_id

		#取题目id 与key对应的对比答案
		groups = AtkdfsGroup.objects.filter(atkdfsID_id=request.session['hack_id'])
		if len(groups) > 0:
			for i in groups:
				if int(i.quesID_id) == int(con["questid"]):
					gpname = Group.objects.get(id=i.groupID_id)
					gp_name = gpname.id
					quest = Infiltration.objects.get(queid_id=i.quesID_id)
					#答案切割成各个key
					arrary = quest.result.split(",")
					#传下来的标题号处理成索引
					string = con["keyid"]
					if string[4] == '0':
						string = string[5:]
					else:
						string = string[4:]
					con["keyid"] =string

					#判断提交的key是否正确
					if arrary[int(string) -1] == con["ans"]:
						iscorrect = True

					ansinfo = AnswerInfo(groupid_id = grid,examid = request.session['hack_id'],is_correct= iscorrect,extime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),queid_id=con["questid"],keyid=int(string),answer=con["ans"],anstype=2)
					if atkdfs.atkdfsStatus != 2:
						con["istart"] = "false"
					else:
						con["istart"] = "true"
						if iscorrect == True:
							con["istart"] = "right"
							aninfo_result = AnswerInfo.objects.filter(anstype=2,answer=con["ans"],queid_id = con["questid"])
							#其他团队提交过就不让提交
							if aninfo_result:
								pass
							else:
								con["istart"] = "left"
								ansinfo.save()
	return HttpResponse(json.dumps(con))
	
def GetSETime(request):
	if not 'cusername' in request.session:
			return HttpResponseRedirect('/Login/')
	courname = request.POST['courname']
	courses = Course.objects.filter(cname=courname)
	data={}
	if(courses.count() > 0):
		startTime = courses[0].begintime
		endTime = courses[0].endtime
		data["startTime"] = startTime.strftime("%Y-%m-%d %H:%M")
		data["endTime"] = endTime.strftime("%Y-%m-%d %H:%M")
	return HttpResponse(json.dumps(data))

# def getVMName(request):
# 	if request.method == "POST":
# 		expid = request.POST["expid"]
# 		cuserid = request.session['cuserid']
# 		curname = request.POST['curname']
# 		clientres = Res.objects.get(userid=cuserid, resid=expid, rectname=curname)
# 		return HttpResponse(json.dumps(clientres.rname))

def getVMId(request):
	if request.method == "POST":
		if request.POST["type"] == "imgls":
			vm = Vm.objects.get(name=request.POST["name"])
		elif request.POST["type"] == "imgvgtls":
			vm = Vgate.objects.get(name=request.POST["name"])

		ip = vm.containerIP
		return HttpResponse(json.dumps(str(vm.id) + ":" + ip))

def expIsStart(request):
	if request.method == "POST":
		expid = request.POST["expid"]
		cuserid = request.session['cuserid']
		clientres = Res.objects.filter(userid=cuserid, resid=expid,isconsole=1)
		return HttpResponse(json.dumps(len(clientres)))

def getNewTopo(request):
	if request.method == "POST":
		cuserid = request.session['cuserid']
		topo = Client.objects.get(studentid=cuserid)
		return HttpResponse(json.dumps(topo.copytopo))


def getOldTopo(request):
	if request.method == "POST":
		expid = request.POST['expid']
		topo = Experiment.objects.get(id=expid)
		return HttpResponse(json.dumps(topo.topo))
#删除课程、大纲、学员会用此装饰器，回收相关的资源
def decorator(deltype):
	def indecorator(f):
		def wrapper(*args, **kwds):
			coursename = None
			expidlist = []
			exp_course_names = []
			stuid = 0
			datas = {}
			result = None
			if deltype=='course':
				courseid = int(args[0].POST['Info'])
				coursename = Course.objects.get(id=courseid).cname
			elif deltype =='outline':
				outlineid = int(args[1])
				ore = Outlinerelation.objects.filter(outlineid_id=outlineid)
				exp_courses = Course.objects.filter(outlineid_id=outlineid)
				for o in ore:
					if o.expid:
						expidlist.append(o.expid.exp_id)
				for c in exp_courses:
					exp_course_names.append(c.cname)
			elif deltype == 'stu':
				stuid = int(args[1])

			datas['course'] = coursename
			datas['outline'] = json.dumps(expidlist)
			datas['exp_course_name'] = json.dumps(exp_course_names)
			datas['stu'] = stuid

			hosts = Host.objects.order_by('id')[1:]
			for host in hosts:
				datas['ip'] = host.hostname
				post("http://" + host.hostname + "/tools/clearRes/", datas)
				
			try:
				# pass
				result = f(*args, **kwds)
			except Exception,diag:
				print str(diag)
			return result
		return wrapper
	return indecorator

def clearRes(request):
	crs = Res.objects.filter(restype=0,containerIP=request.POST['ip'])
	cn = request.POST['course']
	rid = json.loads(request.POST['outline'])
	exp_cnames = json.loads(request.POST['exp_course_name'])
	uid = request.POST['stu']
	host_id = 1
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None

	for cr in crs:
		if (cr.coursename == cn) or (cr.resid in rid and cr.coursename in exp_cnames) or (int(cr.userid) == int(uid)):
			vm = ''
			if cr.rtype =="pgate" or cr.rtype =="pswitch" or cr.rtype =="pc":
				nn=cr.rname
				try:
					p = Device.objects.get(devname=nn)
					p.state = 0
					p.examuseNo = None
					p.usetype=None
					p.save()
				except Exception,diag:
					logger.error(str(diag))
					logger.error('controlChecklab:Device get failed')

			elif cr.rtype =="imgvshls":
				br = cr.rname
				try:
					vs = Vswitch.objects.get(name=br)
					vs.delete()

					cmddel = "/usr/local/bin/ovs-vsctl del-br " + br
					os.system(cmddel)
				except:
					logger.error('controlChecklab:imgvshls get failed')
			else:
				try:
					if cr.rtype == "imgls":
						vm = Vm.objects.get(name=cr.rname)
					else:
						vm = Vgate.objects.get(name=cr.rname)
					vm.usetype=None
					vm.useNo=None
					vm.state = 0
					vm.save()
				except:
					logger.error('controlChecklab:vm or vgate get failed')
				if conn:
					try:
						dom = conn.lookupVM(vm.name)
						if dom.info()[0] == 1:
							dom.destroy()
					except libvirtError , diag:
						logger.error('controlChecklab:' + str(diag))
					try:#删掉绑定的interface
						xml = dom.XMLDesc(0)
						tree = ET.fromstring(xml)
						interface1 = tree.find("devices").findall('interface')
						for i,interface in  enumerate(interface1):
							if interface.get('type') =="direct":
								if cr.rtype=="imgls":
									interface.find('source').set('dev','br2')
								else:#vgate
									if interface.find('source').get('dev') != str(i):
										interface.find('source').set('dev',str(i))
						xx =  ET.tostring(tree)
						xml = xx
						conn.defineXML(xml)
					except libvirtError , diag:
						logger.error('controlChecklab:restore interface failed' + str(diag))
			cr.delete()
	return HttpResponse(1)

