#-*- coding: utf-8 -*- 
'''
1. 添加攻防：首先调用getQuestionNum方法，判断题目数量与团队数量的关系，要求题目数大于等于团队数，调用
atkdfsSave方法，根据前端提交的数据，在Atkdfs表中添加一条数据，并根据选择的教练和参加的团队，分别在
AtkdfsTeacher和AtkdfsGroup中添加数据；

2. 编辑攻防：首先调用atkdfsEdit方法，获取选中攻防的所有信息，用于填充表单，在用户点击保存后，调用
atkdfsUpdate方法，修改数据库中保存的数据；

3. 启动攻防：调用atkdfsControl方法，首先获取攻防所使用的题目以及团队数量，为每个团队随机分配一个
题目，然后调用ftTopos方法，先调用controlChecklab方法清除所有服务器上启动但未使用的虚拟机，找出启动虚
拟机最少且能够启动所有拓扑图的服务器，并调用该服务器上的controlRes方法，将所有的拓扑图分配给那台服务
器。controlRes方法为拓扑图中的每个设备都分配并启动一个虚拟机，并使用openvswitch创建虚拟交换机，将虚拟
机连接到虚拟交换机之上，实现虚拟机之间的通信；

4. 暂停攻防：调用atkdfsControl方法，获取攻防id，调用gbTopos方法，遍历所有服务器，并调用每台服务器上的
controlVm方法，该方法只处理与自己相关的所有虚拟机，这里会将与选中攻防相关的所有虚拟机给暂停掉，最后修
改完成后，在atkdfsControl方法中，修改数据库中该攻防的状态；

5. 停止攻防：依然调用atkdfsControl方法，获取攻防id，调用gbTopos方法，遍历所有服务器，并调用controlVm
方法，将本机上与选中攻防相关的虚拟机全部关闭，并删除为其创建的openvswitch虚拟交换机，最后回到
atkdfsControl方法中，修改数据库中该攻防的状态；

6. 恢复攻防：暂停攻防后，可以再次点击启动按键恢复攻防，首先调用atkdfsControl方法，获取攻防id，然后调用
gbTopos方法，遍历调用所有服务器上的controlVm方法，将所有与选中攻防相关的虚拟机，恢复至启动状态，最后
回到atkdfsControl方法中，修改数据库中该攻防的状态；

7. 攻防详情：调用atkdfsDisplay方法，从数据库中获取与攻防相关的所有数据，并返回给前端页面；

8. 统计归档并导出：停止攻防后，需要将本次攻防的数据导出并保存为excel文件，调用atkdfsCur方法，将攻防信息
以及各个团队的答题、得分与排名情况导出，并保存为excel文件，存放在服务器上；

9. 历史存档记录：调用atkdfsHistoryCur方法，根据攻防id，获取存放在服务器上的所有历史归档excel文件，并返回
给前端页面，以供下载；

10. 攻防展现界面：调用atkdfsshow模块下的views.py文件中的showstate方法，返回攻防展现html界面；

11. 删除攻防：首先调用delHistoryCur方法，删除与选中攻防有关的所有归档excel文件，然后调用atkdfsDelete方法，
从数据库中删除与该攻防有关的所有数据。
'''

from django.shortcuts import render_to_response
from students.models import Student
from groups.models import *
from teachers.models import Teacher
from questions.models import *
import random
import re
from papers.models import *
from sysmgr.models import *
from vms.models import *
from vgates.models import *
from vswitches.models import *
from client.models import *
from devices.models import Device
from tsssite.server import *
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT,HERE
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.models import Q
import json
import datetime
import time
from xml.etree import cElementTree as ET
from  xml.dom import minidom
from xlwt import *
import xlwt
import logging
import sys, os, libvirt, subprocess,commands
from libvirt import libvirtError
from atkdfs.models import *
from collections import OrderedDict
import urllib
import urllib2
import sys

logger = logging.getLogger('mysite.log')
reload(sys)
sys.setdefaultencoding('utf8')
vm_ovs ={}
vm_vgt = {}
g_ethlist = {}
rectFlag = {}
br_MacAddr={}#vgate的mac地址
br_Addr={}#ovs和终端的ip
groQueInfilTopo=None
container_ip = ""

# 默认页面显示信息
def atkdfsManage(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	errors=[]
	examSelect = ''
	currenttea = Teacher.objects.get(id=request.session['userid'])
	if currenttea.roletype == 0:#教练员
		atkteas = AtkdfsTeacher.objects.filter(teaID_id=currenttea.id)
		atkteaids=[]
		for atktea in atkteas:
			atkteaids.append(int(atktea.atkdfsID_id))
		exams = Atkdfs.objects.filter(id__in=atkteaids)
		# exams = Atkdfs.objects.filter(atkdfsCreatorID_id=request.session['userid']).order_by('-id')
	else:
		exams = Atkdfs.objects.order_by('-id')

	if 'textFilter' in request.GET and request.GET['textFilter']:
		examFilter = request.GET.get('textFilter', '')
		exams = exams.filter(Q(atkdfsNo__icontains=examFilter)|Q(atkdfsName__icontains=examFilter))
		examSelect = examFilter
		request.session['examSelect'] = examSelect

	if 'examinationSelect' in request.GET:
		exams = Atkdfs.objects.order_by('-id')
		examFilter = request.GET.get('examinationSelect', '')
		exams = exams.filter(Q(atkdfsNo__icontains=examFilter)|Q(atkdfsName__icontains=examFilter))
		examSelect = examFilter
		request.session['examSelect'] = examSelect
	
	if examSelect in request.session:
		examSelect = request.session['examSelect']
		

	after_range_num = 2
	befor_range_num = 3
	try:
		page = int(request.GET.get("page", 1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1

	paginator = Paginator(exams, 10)

	try:
		examList = paginator.page(page)
	except(EmptyPage, InvalidPage, PageNotAnInteger):
		examList = paginator.page(paginator.num_pages)
	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:page+befor_range_num]
	return render_to_response('templates/atkdfs.html',
							{'examSelect':examSelect,
							'examList':examList,
							'exams':exams,
							'page_range':page_range,
							'nu':exams.count(),
							},
							context_instance=RequestContext(request))

#****返回攻防对抗中的试卷，组队，教练信息****
def atkdfsAddGetInfo(request):
	data = {}
	papers = examGetPapers('')#这两个方法与竞赛中的完全一样
	groups = examGetGroups('')
	teachers = examGetTeachers('')
	data["papers"] = papers
	data["groups"] = groups
	data["teachers"] = teachers
	return HttpResponse(json.dumps(data))

#获取攻防对抗中的试卷信息
def examGetPapers(filterStr): 
	papers = Paper.objects.order_by('-id')
	paps = []
	if filterStr:
		papers = papers.filter(Q(papid__icontains=filterStr)|Q(papname__icontains=filterStr))
	
	for p in papers:
		is_have=0
		pqs = p.paperquestion_set.all()
		for pq in pqs:
			if pq.questionid.qtype !='3':
				is_have=1
				break
		if is_have==0:
			paps.append(p)
	papers = []

	for item in paps:
		pap = {}
		pap["id"] = item.id
		pap["papid"] = item.papid
		pap["papname"] = item.papname
		pap["creator"] = item.creatorid.teaname
		pap["score"] = item.score
		pap["frequency"] = item.frequency 
		pap["edittime"] = item.edittime.strftime("%Y-%m-%d %H:%M")
		papers.append(pap)
	return papers

#获取攻防对抗中的团队信息
def examGetGroups(filterStr):
	gros = Group.objects.order_by('-id')

	if filterStr:
		gros = gros.filter(Q(id=filterStr))

	groups = []
	for item in gros:
		cap=''
		gro = {}
		gromebs = []
		gronums=[]
		gronum_name=[]#归档使用
		gro["id"]=item.id
		gro["gname"] = item.gname
		gm=GroupMembers.objects.filter(groupid_id=item.id)
		for g in gm:
			gromeb=g.studentid.stuname
			gronum=g.studentid.stuno
			gronumname=gromeb+'('+gronum+')'
			gromebs.append(gromeb)
			gronums.append(gronum)

			gronum_name.append(gronumname)#归档使用

			if g.iscaptain == True:
				cap=gromeb
		if cap:
			gro["captain"] = cap
		else:
			gro["captain"] = '--'
		gro["gromebs"]=gromebs
		gro["gronums"]=gronums
		gro["gronum_name"]=gronum_name#归档使用

		groups.append(gro)
	return groups

#获取攻防对抗中的教练信息
def examGetTeachers(filterStr): 
	teas = Teacher.objects.filter(needaudit=0)

	if filterStr:
		teas = teas.filter(Q(account__icontains=filterStr)|Q(teaname__icontains=filterStr))

	teachers = []

	for item in teas:
		tea = {}
		tea["id"] = item.id
		tea["teaname"] = item.teaname
		tea["account"] = item.account
		tea["roletype"] = item.roletype
		tea["sex"] = item.sex
		tea["email"] = item.email
		tea["mobile"] = item.mobile
		teachers.append(tea)
	return teachers

#!!!!检测已有信息!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#检查对抗编号重复性
def atkdfsCheckexamno(request):
	global logger
	exams = Atkdfs.objects.order_by("-id")
	judgeexamno = 0
	if request.method == 'POST':
		try:
			strExamInfo = request.POST['Info']
		except ValueError:
			logger.error("examination")
			raise Http404()
		for exam in exams:
			if strExamInfo == exam.atkdfsNo:
				judgeexamno = 1
				break
		data={}
		data["judgeexamno"] = judgeexamno
		return HttpResponse(json.dumps(data))

# 检查题目与团队数目匹配
def getQuestionNum(request): 
	global logger
	if request.method == 'POST':
		try:
			paperID = int(request.POST['Info'])
		except ValueError:
			logger.error("examDelete: get examination ID error")
			raise Http404
		ques = PaperQuestion.objects.filter(paperid=paperID)
		data={}
		data["quesNum"] = ques.count()
		return HttpResponse(json.dumps(data))

# 创建攻防对抗保存操作
def atkdfsSave(request): 
	global logger
	if request.method == 'POST':
		try:
			strHackInfo = request.POST['Info']
		except ValueError:
			logger.error("hackSave: get atkdfs information error")
			raise Http404

	jsonHackInfo = json.loads(strHackInfo)
	start = datetime.datetime.strptime(jsonHackInfo["startTime"],"%Y-%m-%d %H:%M") 
	end=datetime.datetime.strptime(jsonHackInfo["endTime"],"%Y-%m-%d %H:%M") 
	hack = Atkdfs(atkdfsNo=jsonHackInfo['no'],
						atkdfsName=jsonHackInfo['name'],
						atkdfsDescription=jsonHackInfo['description'],
						atkdfsStartTime=start,
						atkdfsEndTime=end,
						atkdfsCreatorID_id=int(request.session['userid']),
						atkdfsCreateTime=datetime.datetime.now(),
						atkdfsEditTime=datetime.datetime.now(),
						atkdfsStatus=0,#default
						atkdfsPaperID_id=int(jsonHackInfo['paperID']))
	hack.save()
	hackID = hack.id
	
	if jsonHackInfo["studentIDs"][0]:#添加了空团队
		addAtkdfsGroup(hackID, jsonHackInfo["studentIDs"])

	addAtkdfsTeacher(hackID, jsonHackInfo["teacherIDs"])
	addPaperFrequency(int(jsonHackInfo['paperID']))

	return HttpResponseRedirect("/atkdfs/")

#向攻防团队中添加学生信息
def addAtkdfsGroup(hackID, studentIDs): 
	if studentIDs:
		for item in studentIDs:
			hackStu = AtkdfsGroup(atkdfsID_id=hackID, groupID_id=int(item))
			hackStu.save() 

#向攻防中添加教练信息
def addAtkdfsTeacher(hackID, teacherIDs): 
	for item in teacherIDs:
		hackTea = AtkdfsTeacher(atkdfsID_id=hackID, teaID_id=int(item))
		hackTea.save()

#向攻防中添加试卷信息
def addPaperFrequency(paperID): 
	papid = int(paperID)
	paper = Paper.objects.get(id=papid)
	paper.frequency += 1;
	paper.save()
	return paper.frequency

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# 编辑攻防对抗

# 获取编辑页面显示信息
def atkdfsEdit(request): 
	global logger
	data = {}
	try:
		if request.method == 'POST':
			examid = int(request.POST['Info'])
			examination = Atkdfs.objects.get(id=examid)
			examTea = AtkdfsTeacher.objects.filter(atkdfsID_id=examid).order_by('id')
			examGro = AtkdfsGroup.objects.filter(atkdfsID_id=examid)
			exam={}
			exam['examID'] = examination.id
			exam['examNo'] = examination.atkdfsNo
			exam['examName'] = examination.atkdfsName
			exam['examDescription'] = examination.atkdfsDescription
			exam['examStartTime'] = examination.atkdfsStartTime.strftime("%Y-%m-%d %H:%M")
			exam['examEndTime'] = examination.atkdfsEndTime.strftime("%Y-%m-%d %H:%M")
			exam['examPaperID'] = examination.atkdfsPaperID.id

			teas = []
			for item in examTea:
				teas.append(item.teaID.id)

			gros = []
			for item in examGro:
				gros.append(item.groupID.id)
			exam['examTea'] = teas
			exam['examGro'] = gros

			papers = examGetPapers('')
			groups = examGetGroups('')
			teachers = examGetTeachers('')
			data["papers"] = papers
			data["groups"] = groups
			data["teachers"] = teachers
			data['exam'] = exam

			data['status'] = examination.atkdfsStatus
	except:
		logger.error("examEdit:get atkdfs ID error")
		data["result"] = 1
	else:
		data["result"] = 0
	finally:
		return HttpResponse(json.dumps(data))

# 更新攻防对抗基本信息
def atkdfsUpdate(request): 
	global logger
	if request.method == 'POST':
		try:
			examInfo =  request.POST['Info']	

		except ValueError:
			logger.error('examUpdate get examination information failed')
			raise Http404

	jsonexamInfo = json.loads(examInfo)

	examID = int(jsonexamInfo["id"])

	exam = Atkdfs.objects.get(id=examID)

	if int(jsonexamInfo["paperID"]) != exam.atkdfsPaperID.id:
		subPaperFrequency(exam.atkdfsPaperID.id)
		exam.atkdfsPaperID_id = int(jsonexamInfo["paperID"])
		addPaperFrequency(int(jsonexamInfo["paperID"]))

	start = datetime.datetime.strptime(jsonexamInfo["startTime"],"%Y-%m-%d %H:%M") 
	end=datetime.datetime.strptime(jsonexamInfo["endTime"],"%Y-%m-%d %H:%M") 

	exam.atkdfsNo = jsonexamInfo["no"]
	exam.atkdfsName = jsonexamInfo["name"]
	exam.atkdfsStartTime = start
	exam.atkdfsEndTime = end
	exam.atkdfsDescription = jsonexamInfo["description"]
	# exam.examCreateTime=datetime.datetime.now()
	exam.atkdfsEditTime=datetime.datetime.now()
	exam.save()
	#删除原来的团队与教练重新添加
	clearAtkdfsGroup(examID)
	clearAtkdfsTeacher(examID)
	addAtkdfsGroup(examID, jsonexamInfo["studentIDs"])
	addAtkdfsTeacher(examID, jsonexamInfo["teacherIDs"])
	return HttpResponseRedirect("/atkdfs/")

# 更改试卷使用次数，用于判断试卷是否被使用
def subPaperFrequency(paperID): 
	papid = int(paperID)
	paper = Paper.objects.get(id=papid)
	paper.frequency -= 1;
	if paper.frequency < 0:
		paper.frequency = 0
	paper.save()
	return paper.frequency

# 删除攻防中团队信息
def clearAtkdfsGroup(examID): 
	ExamGro = AtkdfsGroup.objects.filter(atkdfsID_id = int(examID))
	for item in ExamGro:
		item.delete()

# 删除攻防中教练信息
def clearAtkdfsTeacher(examID): 
	ExamTea = AtkdfsTeacher.objects.filter(atkdfsID_id = int(examID))
	for item in ExamTea:
		item.delete()

# 删除攻防对抗
def atkdfsDelete(request):
	global logger
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examDelete: get atkdfs ID error")
			raise Http404

	clearAtkdfsGroup(examid)
	clearAtkdfsTeacher(examid)

	exam = Atkdfs.objects.get(id=examid)
	
	exam.delete()
	subPaperFrequency(exam.atkdfsPaperID.id)
	return HttpResponseRedirect("/atkdfs/")

# 详情信息展示
def atkdfsDisplay(request):
	global logger
	if request.method == 'POST':
		try:
			examID = request.POST['Info']
			exam = Atkdfs.objects.get(id=examID)
			gros = AtkdfsGroup.objects.filter(atkdfsID=examID).order_by('-id')
			teas = AtkdfsTeacher.objects.filter(atkdfsID=examID).order_by('-id')
		except:
			logger.error('examDisplay:get examID failed')
			raise Http404

	data = {}
	data["examID"] = exam.id
	data["examNo"] = exam.atkdfsNo
	data["examName"] = exam.atkdfsName
	data["examDescription"] = exam.atkdfsDescription
	data["examCreator"] = exam.atkdfsCreatorID.teaname
	data["examPaper"] = exam.atkdfsPaperID.papname
	data["examStartTime"] = exam.atkdfsStartTime.strftime("%Y-%m-%d %H:%M")
	data["examEndTime"] = exam.atkdfsEndTime.strftime("%Y-%m-%d %H:%M")
	data["examEditTime"] = exam.atkdfsEditTime.strftime("%Y-%m-%d %H:%M")
	data["examCreateTime"] = exam.atkdfsCreateTime.strftime("%Y-%m-%d %H:%M")
	data["examStatus"] = exam.atkdfsStatus
	groups = []
	for item in gros:
		gro = {}
		cap=''
		gromebs = []
		gro["id"]=item.groupID.id
		gro["gname"] = item.groupID.gname

		gm=GroupMembers.objects.filter(groupid_id=item.groupID.id)
		for g in gm:
			gromeb=g.studentid.stuname
			gromebs.append(gromeb)
			if g.iscaptain == True:
				cap=gromeb
		if cap:
			gro["captain"] = cap
		else:
			gro["captain"] = '--'
		gro["captain"] = cap
		gro["gromebs"]=gromebs
		groups.append(gro)
	data["groups"] = groups
	teachers = []
	for item in teas:
		teachers.append(item.teaID.teaname)
	data["teachers"] = teachers

	return HttpResponse(json.dumps(data))

# 启动攻防对抗操作

#向Vswitch中添加br信息
def createbr():  
	global container_ip
	brname =''
	ovs = ImgVsh.objects.get(name='OVS')
	brs = Vswitch.objects.order_by('id')
	count = len(brs) + 1 + 100
	index = 100
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
					containerIP=container_ip)
			vm.save()
			break
		index = index + 1
	return brname

#检查当前所有虚拟机状态
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
		except libvirtError ,diag:
			logger.error(str(diag))
	vms = Vgate.objects.filter(containerIP=container_ip).order_by('-id')
	for vm in vms:
		try:
			dom = conn.lookupVM(vm.name)
			if dom.info()[0] == 5 and vm.state==1:#关机；1开机；3暂停
				vm.state=0
				vm.save()
			elif dom.info()[0] == 1 and vm.state==0:#关机；1开机；3暂停
				dom.destroy()
		except libvirtError ,diag:
			logger.error(str(diag))
	return 1

#首先清除空闲的实验环境
def controlChecklab(request): 
	global container_ip
	container_ip = request.POST["containerIP"]
	# clients=Client.objects.filter().order_by('-id')
	clients=Client.objects.order_by('-id')
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
		logger.info('clear client id=' + str(c.id) + ' time=' + str((nowtime-logtime).seconds))
		if (nowtime-logtime).seconds > 150:
			clientres = Res.objects.filter(userid=c.studentid,restype=0).order_by('id')

			# 如果实验c启动的资源不在当前的服务器上，那么就不进行处理
			if len(clientres) > 0 and clientres[0].containerIP != container_ip:
				continue

			for cr in clientres:
				logger.info('client id=' + str(c.id) + ', start clear: ' + cr.rname)
				vm = ''
				if cr.rtype =="pgate" or cr.rtype =="pswitch" or cr.rtype =="pc":
					nn=cr.rname
					try:
						ps = Device.objects.filter(devname=nn)
						for p in ps:
							p.examuseNo = None
							p.usetype=None
							p.state = 0
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
						if vm.state:
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
				logger.info('client id=' + str(c.id) + ', end clear: ' + cr.rname)
	return HttpResponse(1)

#筛选渗透题型才能被攻防对抗使用
def controlGetQuesID(request,paperID): 
	questionInfiltraIDs = []
	if paperID:
		paperquestions = PaperQuestion.objects.filter(paperid=paperID)
	for item in paperquestions:
		queid = item.questionid.id
		que = Question.objects.get(id = queid)
		if que.qtype == '3':
			questionInfiltraIDs.append(queid)
	return questionInfiltraIDs

#拓扑图转为Json
def topoToJson(topo): 
	if topo:
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
		try:
			jsontopo = json.loads(topo)
		except :
			# print "get topo failed"
			pass
		return jsontopo

#Json转为拓扑图
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
	return topo

#服务器之间通信使用
def post(url, data): 
	try:
		req = urllib2.Request(url)
		data = urllib.urlencode(data)
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
		response = opener.open(req, data)
		return response.read()
	except Exception, e:
		return None

#分配拓扑图到多台服务器上启动
def fpTopos(teacherid,topos,examID): 
	# 获取所有服务器上虚拟终端和安全设备的数量（启动数量和未使用数量）
	infos = {}
	servers = Host.objects.order_by('id')[1:]

	# 首先清除空闲的实验环境controlChecklab
	for server in servers:
		logger.info('atkdfs start to clear lab: ' + server.hostname)
		post("http://" + server.hostname + "/atkdfs/controlChecklab/", {"containerIP": server.hostname})

	for server in servers:
		infos[server.hostname] = {}
		infos[server.hostname]["used"] = 0
		infos[server.hostname]["imgs"] = {}
		# infos[server.hostname]["topos"] = {}

		imgls = Img.objects.all()
		for img in imgls:
			vms = Vm.objects.filter(imgtype_id=img.id, containerIP=server.hostname)
			startedVms = vms.filter(state=1)
			infos[server.hostname]["used"] += len(startedVms)
			infos[server.hostname]["imgs"]["imgls_" + img.name] = len(vms) - len(startedVms)

		imgvgtls = ImgVgt.objects.all()
		for imgvgt in imgvgtls:
			vgts = Vgate.objects.filter(imgtype_id=imgvgt.id, containerIP=server.hostname)
			startedVgts = vgts.filter(state=1)
			infos[server.hostname]["used"] += len(startedVgts)
			infos[server.hostname]["imgs"]["imgvgtls_" + imgvgt.name] = len(vgts) - len(startedVgts)

	img_counts = {}  # 记录每种虚拟终端的数量，名字是固定的imgls,imgvgtls
	hasPhysics = False  # topo中存在物理设备时，为True。否则为False
	for groid in topos:
		if topos[groid]:
			for k, v in topos[groid]["states"].items():
				t = v["props"]["type"]["value"]
				if t == "imgls" or t == "imgvgtls":
					ins = v["props"]["instance"]["value"]
					key = t + "_" + ins
					if key not in img_counts:
						img_counts[key] = 1
					else:
						img_counts[key] += 1
				elif (not hasPhysics) and (t == "pgate" or t == "pswitch" or t == "pc"):
					hasPhysics = True

	# 找出能够启动拓扑图
	passer = []
	for k, v in infos.items():
		flag = True
		imgs = v["imgs"]
		for i, c in img_counts.items():
			if imgs[i] < c:
				flag = False
				break
		if flag:
			passer.append(k)

	# 如果存在物理设备，默认使用主服务器
	main_server = Host.objects.get(id=2).hostname
	if hasPhysics and (main_server in passer):
		passer = [main_server]
	elif hasPhysics:
		return 2

	if not len(passer):
		return 2

	# 在passer中找到启动虚拟机数量最少的服务器
	min_count = -1
	host_ip = ""
	for p in passer:
		if min_count == -1:
			min_count = infos[p]["used"]
			host_ip = p
		elif min_count > infos[p]["used"]:
			min_count = infos[p]["used"]
			host_ip = p

	datas = {"teacherid": teacherid, "grotopos": json.dumps(topos), "examID": examID, "containerIP": host_ip}
	re = post("http://" + host_ip + "/atkdfs/controlRes/", datas)
	return int(re)

# 关闭或停止所有的拓扑图
def gbTopos(examid, sptype):
	servers = Host.objects.order_by('id')[1:]
	re = 0
	for server in servers:
		ip = server.hostname
		re = post("http://" + ip + "/atkdfs/controlVm/", {"examid": examid, "sptype": sptype, "host_ip": ip})
		if int(re) != 1:
			break
	return int(re)

# 响应ajax攻防对抗控制
def atkdfsControl(request):
	if not 'userid' in request.session:
		return HttpResponseRedirect('/Login/')	
	global logger
	result = 0

	teacherid = request.session["userid"]
	if request.method == 'POST':
		try:
			examID = int(request.POST["eid"])  #获取攻防ID
		except ValueError:
			logger.error('examStart get examination information failed')
			raise Http404

		data = {}
		if "start" == request.POST["btnname"]:  #按照按钮名称操作
			# import pdb
			# pdb.set_trace()
			paperID = Atkdfs.objects.get(id=examID).atkdfsPaperID.id #由攻防的ID获取试卷
			
			questionInfiltraIDs = controlGetQuesID(request,paperID) #由试卷的ID获取题目

			ags = AtkdfsGroup.objects.filter(atkdfsID_id=examID) #由攻防ID获取攻防团队
			if len(questionInfiltraIDs) < len(ags):
				return HttpResponse(json.dumps({"result": u'团队数量不能大于题目数量'}))
			#由攻防的ID和所有题目的ID给团队随机分配题目,并得到分配出的题目的topo;topos是字典，以团队ID为key，topo为值
			grotopos=controlQuesToGroup(examID,questionInfiltraIDs)
			#print grotopos
			#由img的ID启动可以使用的虚拟机
			# result = controlRes(request,conn,teacherid,grotopos,examID)
			result = fpTopos(teacherid,grotopos,examID)
			if result ==1:
				atkdfs = Atkdfs.objects.get(id=examID)
				atkdfs.atkdfsStatus = 2#启动
				atkdfs.atkdfsEditTime=datetime.datetime.now()
				atkdfs.save()
			else:
				# controlVm(request,examID,conn,"stop")
				gbTopos(examID, "stop")
				clearExamRes(examID)
		elif "pause" == request.POST["btnname"]:
			# result = controlVm(request,examID,conn,"suspend")
			result = gbTopos(examID, "suspend")
			if result:
				exam = Atkdfs.objects.get(id=examID)
				exam.atkdfsStatus = 1#暂停
				exam.atkdfsEditTime=datetime.datetime.now()
				exam.save()
		elif "resume" == request.POST["btnname"]:
			# result = controlVm(request,examID,conn,"resume")
			result = gbTopos(examID, "resume")
			if result:
				exam = Atkdfs.objects.get(id=examID)
				exam.atkdfsStatus = 2#暂停
				exam.atkdfsEditTime=datetime.datetime.now()
				exam.save()
		elif "stop" == request.POST["btnname"]:
			# result = controlVm(request,examID,conn,"stop")
			result = gbTopos(examID, "stop")
			if result:
				exam = Atkdfs.objects.get(id=examID)
				exam.atkdfsStatus = 3#已完成
				exam.atkdfsEditTime=datetime.datetime.now()
				exam.save()
		data["result"] = result
		return HttpResponse(json.dumps(data))

# 将攻防对抗中的题目分配改团队
def controlQuesToGroup(examID,questionInfiltraIDs):
	grotopos = {}	
	ags = AtkdfsGroup.objects.filter(atkdfsID_id=examID)
	for ag in ags:
		qid=random.choice(questionInfiltraIDs)
		ag.quesID=Question.objects.get(id=qid)
		topo = Infiltration.objects.get(queid=qid).topo
		ag.copytopo=topo
		ag.save()		

		jsontopo = topoToJson(topo)
		grotopos[ag.groupID_id]=jsontopo
		questionInfiltraIDs.remove(qid)#不同的团队不能使用相同的题目
	return grotopos

# 攻防对抗控制
def controlRes(request):
	global vm_vgt#遍历中心端，以br为key
	global vm_ovs#发散端，以br为key
	global rectFlag
	global g_ethlist
	global br_MacAddr
	global br_Addr
	global groQueInfilTopo
	global container_ip

	host_id = 1
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None

	teacherid = request.POST["teacherid"]  #获取教练ID信息
	grotopos = json.loads(request.POST["grotopos"]) #转码拓扑数据
	examID = request.POST["examID"]  #获取实验ID
	container_ip = request.POST["containerIP"]		

	controlCheckState(conn)
	# controlChecklab(conn)

	for groid in grotopos:
		vm_ovs={}
		vm_vgt={}
		rectFlag={}
		g_ethlist={}
		br_MacAddr={}
		br_Addr={}
		groQueInfilTopo=None

		topo=grotopos[groid]
		
		atkgro=AtkdfsGroup.objects.get(atkdfsID_id=examID,groupID_id=groid)
		groQueInfilTopo=atkgro.copytopo


		if topo!=None:
			for key, value in topo["states"].items():
				addr = value["props"]["addr"]["value"]
				imgtype= value["props"]["type"]["value"]
				imgname = value["props"]["instance"]["value"]
				if imgtype == "imgvshls":
					rectFlag[key]='imgvshls'
					
					result = startovs(conn,groid,topo,teacherid,examID,key,imgtype, imgname, addr)			
					if result !=1:
						return HttpResponse(result)

				elif imgtype == "pswitch":
					rectFlag[key]='pswitch'
					result = startpswitch(conn,groid,topo,teacherid,examID,key,imgtype, imgname, addr)
					if result !=1 and result !=None:
						return HttpResponse(result)

				elif imgtype=="imgvgtls":
					rectFlag[key]='imgvgtls'
					result = startvgt(conn,groid,topo,teacherid,examID,key,imgtype, imgname, addr)
					if result !=1:
						return HttpResponse(result)

				elif imgtype=="pgate":
					rectFlag[key]='pgate'
					result = startpgate(conn,groid,topo,teacherid,examID,key,imgtype, imgname, addr)
					if result !=1 and result !=None:
						return HttpResponse(result)
			logger.info('before starting all vms !')


			for key, value in topo["states"].items():
				addr = value["props"]["addr"]["value"]
				imgtype= value["props"]["type"]["value"]
				imgname = value["props"]["instance"]["value"]

				if imgtype != "imgvshls":#只有虚拟交换机不会作为终端
					result = startvm(conn,groid,topo,teacherid,examID,key,imgtype, imgname, addr)
					if result !=1:
						return HttpResponse(result)

			logger.info('after starting all vms !')
			
			for key in br_MacAddr:
				if br_MacAddr[key] in br_Addr:
					keymac=key.split(',')
					vr = VgateRes(vgateName=keymac[0],macAddr=keymac[1],pathKey=br_Addr[br_MacAddr[key]][0],pathtext=br_Addr[br_MacAddr[key]][1],userid=teacherid,restype=2,resid=examID)
					vr.save()
			logger.info('after saving  vgate internet access information!')

			vgates = VgateRes.objects.filter(userid=teacherid, resid=examID,restype=2)
			groQueInfilTopo = topoToJson(groQueInfilTopo)
			
			for vgate in vgates:
				mac = vgate.macAddr
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
					
			strinfo = re.compile('\*\*')
			groQueInfilTopo=strinfo.sub('',groQueInfilTopo)

			atkgro.copytopo = groQueInfilTopo
			atkgro.save()
	# 修改res里面多个控制台IP冲突的问题
	logger.info('start to resSetIP')
	resSetIP(examID)
	return HttpResponse(1)


def resSetIP(examID):
	res = Res.objects.filter(resid=examID,restype=2)
	alladdr = list(res.values("addr"))
	stuconaddr = res.exclude(Q(usebystu=None)).filter(Q(isconsole=0))
	for stuaddr in stuconaddr:
		tempaddr = stuaddr.addr.split('.')
		while True:
			tempaddr[-1] = unicode(random.randint(2,253))
			newaddr = '.'.join(tempaddr)

			temp = {'addr':newaddr}
			if temp not in alladdr :
				alladdr.append(temp)
				stuaddr.addr = newaddr
				stuaddr.save()
				break

def startovs(conn,groid,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr):	
	global vm_ovs
	global br_MacAddr
	global br_Addr
	if imgbrtype == "imgvshls":
		try:
			br = createbr()
			cmd = "/usr/local/bin/ovs-vsctl add-br " + br
			os.system(cmd)
			examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=br,insname=imgbrname,rtype=imgbrtype,resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
		except Exception,diag:
			logger.error('startovs:' + str(diag))
			return 0
		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			recttotype = topo["states"][rectto]["props"]["type"]["value"]
			rectfromtype = topo["states"][rectfrom]["props"]["type"]["value"]

			pathtext = value["text"]["text"]

			if brkey == rectfrom:#虚拟交换机可以连接除了虚拟交换机的所有类型
				brname = createbr()
				cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
				os.system(cmd)
				examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
				examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname=br,rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
def startvgt(conn,groid,topo,teacherid,examID,vgtkey,imgvgttype, imgvtname, vgtaddr):
	global vm_vgt
	global vm_ovs
	global rectFlag

	if imgvgttype == 'imgvgtls':
		for key, value in topo["paths"].items():
			rectfrom= value["from"]
			rectto = value["to"]
			pathtext = value["text"]["text"]

			recttotype = topo["states"][rectto]["props"]["type"]["value"]
			rectfromtype = topo["states"][rectfrom]["props"]["type"]["value"]
			
			if vgtkey==rectfrom and  (recttotype== "imgls" or recttotype== "pc" or (recttotype== "imgvgtls" and rectto not in rectFlag) or recttotype== "pgate" ):
				try:
					brname = createbr()
					cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
					os.system(cmd)
					examres = Res(userid=teacherid,usebygroup_id=groid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=vgtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()	
				except Exception,diag:
					logger.error(str(diag))
					return 0			
				vm_ovs[brname] = rectto
				if recttotype=="imgls" and int(topo["states"][rectto]["props"]["isconsole"]["value"]):#记录控制台
					vm_vgt[brname] = [vgtkey,1]
				else:
					vm_vgt[brname] = [vgtkey]
				br_Addr[brname]=[key,pathtext]

			elif vgtkey==rectto and ( rectfromtype== "imgls" or rectfromtype== "pc" or (rectfromtype== "imgvgtls" and rectfrom not in rectFlag) or rectfromtype== "pgate"):
				try:
					brname = createbr()
					cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
					os.system(cmd)
					examres = Res(userid=teacherid,usebygroup_id=groid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=vgtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()
				except Exception,diag:
					logger.error(str(diag))
					return 0	
				vm_ovs[brname] = rectfrom
				if rectfromtype=="imgls" and int(topo["states"][rectfrom]["props"]["isconsole"]["value"]):#记录控制台
					vm_vgt[brname] = [vgtkey,1]
				else:
					vm_vgt[brname] = [vgtkey]

				br_Addr[brname]=[key,pathtext]

	return 1
def startpswitch(conn,groid,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr):	
	global vm_ovs
	global g_ethlist
	global rectFlag
	global br_Addr

	ps = None
	if imgbrtype == "pswitch":
		try:
			ps = Device.objects.get(devname=imgbrname,devtype="pswitch",state=0)
			examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=imgbrname,insname=imgbrname,rtype="pswitch",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			ps.state = 1
			ps.examuseNo = Atkdfs.objects.get(id=examID).atkdfsNo
			ps.usetype=2
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
				if tecttotype=="imgls" or tecttotype=="imgvgtls":
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
							vm_ovs[brname] = rectto
						except Exception:
							logger.error('startpswitch: 1get eth failed')
							return 0
						g_ethlist[brkey].pop(0)
						if tecttotype=="imgvgtls":
							br_Addr[brname]=braddr
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
								examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
								vm_ovs[brname] =rectto
							except Exception:
								logger.error('startpswitch: 2get eth failed')
								return 0
							g_ethlist[brkey].pop(0)
						else:
							return 5

			elif brkey == rectto:
				tectfromtype=topo["states"][rectfrom]["props"]["type"]["value"]
				if tectfromtype=="imgls"or tectfromtype=="imgvgtls":
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()

							vm_ovs[brname] = rectfrom

						except Exception:
							logger.error('startpswitch: 3get eth failed')
							return 0
						g_ethlist[brkey].pop(0)
						if tectfromtype=="imgvgtls":
							br_Addr[brname]=braddr
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
								examres = Res(userid=teacherid,usebygroup_id=groid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
								vm_ovs[brname] = rectfrom

							except Exception:
								logger.error('startpswitch: 4get eth failed')
								return 0
							g_ethlist[brkey].pop(0)
						else:
							return 5

			
		return 1
def startpgate(conn,groid,topo,teacherid,examID,gtkey,gttype, gtname, gtaddr):
	global vm_vgt
	global vm_ovs
	global g_ethlist
	global rectFlag

	pg = None
	if gttype == 'pgate':
		try:
			pg = Device.objects.get(devname=gtname,devtype="pgate",state=0)
			examres = Res(userid=teacherid,usebygroup_id=groid,rectname=gtkey,rname=gtname,insname=gtname,rtype="pgate",resid=examID,addr=gtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pg.state = 1
			pg.examuseNo = Atkdfs.objects.get(id=examID).atkdfsNo
			pg.usetype=2
			pg.save()

			ethx= pg.ethx
			if ethx == None:
				# ethx=''
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
							examres = Res(userid=teacherid,usebygroup_id=groid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
						except :
							logger.error('startpgate:1get pgate eth Device failed')
							return 0

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
								examres = Res(userid=teacherid,usebygroup_id=groid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
							except :
								logger.error('startpgate:2get pgate eth Device failed')
								return 0

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
							examres = Res(userid=teacherid,usebygroup_id=groid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
						except :
							logger.error('startpgate:3get pgate eth Device failed')
							return 0
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
								examres = Res(userid=teacherid,usebygroup_id=groid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
							except :
								logger.error('startpgate:4get pgate eth Device failed')
								return 0
							g_ethlist[gtkey].pop(0)
							vm_ovs[brname] = rectfrom
						else:
							return 5
	return 1
def vm_br(conn,examID,groid,teacherid,dom,key,imgtype,vmname,addr,vmisconsole):
	global vm_ovs
	global vm_vgt
	global br_MacAddr
	global br_Addr
	frebr=['0','1','2','3','4',]	
	if imgtype=="imgvgtls":
		for brname in vm_vgt:
			if len(vm_vgt[brname])==2:
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
		for brname in vm_vgt:#只可能是vgate做中心遍历的时候添加进去
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

					# macaddr=get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[%s]/mac/@address" % num)
					# br_MacAddr[vmname+','+macaddr]=brname
				except libvirtError ,diag:
					logger.error('vm_br:2xml  failed,'+str(diag))
					return 0
	for brname in vm_ovs:
		if key == vm_ovs[brname]:
			if vmisconsole:#imgls的控制台的br才会执行
				cmdlist = '/usr/local/bin/ovs-vsctl list-br'
				status, output=commands.getstatusoutput(cmdlist)
				outputlist=output.split('\n')
				# br1_作用：因为攻防为完全独立环境，需要两个团队的拓扑能够通信才能实现攻击，用此br连接所有控制台电脑，实现控制台之间的通信
				if 'br1_'+str(examID) not in outputlist:
					cmd = "/usr/local/bin/ovs-vsctl add-br br1_"+str(examID)
					os.system(cmd)
				try:
					cmd7 = "/usr/local/bin/ovs-vsctl add-port br1_"+str(examID)+" patch-to-eth"+brname
					os.system(cmd7)
					cmd10 = "/usr/local/bin/ovs-vsctl add-port "+brname+" patch-to-br1eth"+brname
					os.system(cmd10)
					cmd8 = "/usr/local/bin/ovs-vsctl set interface patch-to-br1eth"+brname+" type=patch"
					os.system(cmd8)
					cmd9 = "/usr/local/bin/ovs-vsctl set interface patch-to-eth"+brname+" options:peer=patch-to-br1eth"+brname
					os.system(cmd9)
					cmd11 = "/usr/local/bin/ovs-vsctl set interface patch-to-eth"+brname+" type=patch"
					os.system(cmd11)
					cmd12 = "/usr/local/bin/ovs-vsctl set interface patch-to-br1eth"+brname+" options:peer=patch-to-eth"+brname
					os.system(cmd12)

					newbr="br1_"+str(examID)
					examres = Res(userid=teacherid,usebygroup_id=groid,rectname="rect3",rname=newbr,insname="OVS",rtype="imgvshls",resid=examID,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()
					ovs = ImgVsh.objects.get(name='OVS')
					vm = Vswitch(name=newbr,mgrip='',imgtype_id=ovs.id,mgrport=9000,state=0,remark='',containerIP=container_ip)
					vm.save()
				except:
					logger.error("console_br1 failed") 
					return 6
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
				xx =  ET.tostring(tree)
				xml = xx
				conn.defineXML(xml)
				# if imgtype=="imgvgtls":
				# 	macaddr=get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[%s]/mac/@address" % num)
				# 	br_MacAddr[vmname+','+macaddr] = brname
			except libvirtError ,diag:
				logger.error('vm_br:1xml  failed,'+str(diag))
				return 0
def img_vm(conn,statetext,groid,usebystudent,imgid,key,vmisconsole,teacherid,examID,imgtype,imgname,vmaddr):
	global groQueInfilTopo
	global container_ip
	vms = Vm.objects.filter(state=0, imgtype=imgid, containerIP=container_ip).order_by('id')
	if  vms:
		if conn:
			try:
				vmname = vms[0].name
				examres = Res(userid=teacherid,usebygroup_id=groid,rectname=key,usebystu=usebystudent,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,mac1='',mac2='',addr=vmaddr,isconsole=vmisconsole,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
				examres.save()

				strinfo = re.compile('\''+statetext+'\'')
				groQueInfilTopo=strinfo.sub('\''+vmname+'**\'',groQueInfilTopo)

				dom = conn.lookupVM(vmname)
				vm_br(conn,examID,groid,teacherid,dom,key,imgtype,vmname,vmaddr,vmisconsole)
				vmmac1 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[1]/mac/@address")
				vmmac2 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[2]/mac/@address")
				if not vmmac1:
					vmmac1=""
				if not vmmac2:
					vmmac2=""
				try:
					dom.create()
					time.sleep(3)
				except libvirtError ,diag:
					logger.error('startvms:0vm start failed,'+str(diag))
				vm = Vm.objects.get(name=vms[0].name)

				examres.mac1=vmmac1
				examres.mac2=vmmac2
				examres.save()

				vm.state=1#启动
				vm.usetype=2
				vm.useNo=Atkdfs.objects.get(id=examID).atkdfsNo
				vm.save()
			except libvirtError ,diag:
				logger.error('startvms:vm start failed,'+str(diag))
				return 0		
	else:
		return 2
	return 1
def startvm(conn,groid,topo,teacherid,examID,key,imgtype,imgname,vmaddr):
	global vm_ovs
	global vm_vgt
	global g_ethlist
	global br_Addr
	global container_ip
	global groQueInfilTopo

	pc =None
	ethlist = None
	vmisconsole=0
	usebystudent = None

	statetext=topo["states"][key]["vm"]
	

	if imgtype == "imgls":
		try:
			imgid = Img.objects.get(name=imgname).id
		except:
			logger.error('startvms:vmimg not exist')
			return 4

		vmisconsole=int(topo["states"][key]["props"]["isconsole"]["value"])
		if not vmisconsole:
			usebystudent = None
			result = img_vm(conn,statetext,groid,usebystudent,imgid,key,vmisconsole,teacherid,examID,imgtype,imgname,vmaddr)			
			if result != 1:
				return result
		else:#此镜像是控制台
			groupMembers = GroupMembers.objects.filter(groupid_id=groid)
			for gm in groupMembers:
				usebystudent = gm.studentid

				result = img_vm(conn,statetext,groid,usebystudent,imgid,key,vmisconsole,teacherid,examID,imgtype,imgname,vmaddr)
				if result != 1:
					return result
				vmisconsole = 0#vmisconsole在for循环中只能有一次等于1，只能连接br1一次
	elif imgtype=="pc":
		try:
			pc = Device.objects.get(devname=imgname,devtype="pc",state=0)			
			ethx = pc.ethx
			if ethx == None:
				ethx=''
			ethlist = ethx.split(',')
		except :
			logger.error('startvms:get pc Device failed')
			return 3#物理资源不够
		if ethlist !=[''] and ethlist !=[]:#pc连接的是物理资源，可以不予考虑,终端设备可以使用网卡来判断连接方式
			examres = Res(userid=teacherid,usebygroup_id=groid,rectname=key,rname=imgname,insname=imgname,rtype="pc",resid=examID,addr=vmaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pc.state = 1
			pc.examuseNo = Atkdfs.objects.get(id=examID).atkdfsNo
			pc.usetype=2
			pc.save()
			for brname in vm_ovs:
				if key == vm_ovs[brname]:
					if ethlist!=[''] and ethlist!=[]:
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+ethlist[0]
						os.system(cmd1)
						ethlist.pop(0)	
					else:
						return 5
					br_Addr[brname]=vmaddr

	elif imgtype=="imgvgtls":#防火墙是虚拟墙
		try:
			imgvgtid = ImgVgt.objects.get(name=imgname).id
		except:
			logger.error('startvms:vgtimg not exist')

			# print "vgtimg not exist"
			return 4
		vms = Vgate.objects.filter(state=0, imgtype=imgvgtid, containerIP=container_ip).order_by('id')
		if vms:
				try:
					vmname = vms[0].name
					examres = Res(userid=teacherid,usebygroup_id=groid,rectname=key,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,mac1='',mac2='',addr=vmaddr,restype=2,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()

					dom = conn.lookupVM(vmname)
					vm_br(conn,examID,groid,teacherid,dom,key,imgtype,vmname,vmaddr,0)

				except Exception ,diag:
					logger.error('startvms:'+str(diag))
					return 0
				try:
					vmmac1 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[1]/mac/@address")
					vmmac2 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[2]/mac/@address")
					if not vmmac1:
						vmmac1=""
					if not vmmac2:
						vmmac2=""

					dom.create()
					time.sleep(3)
					vm = Vgate.objects.get(name=vms[0].name)
					
					examres.mac1=vmmac1
					examres.mac2=vmmac2
					examres.save()
					
					strinfo = re.compile('\''+statetext+'\'')
					groQueInfilTopo=strinfo.sub('\''+vmname+'**\'',groQueInfilTopo)

					vm.usetype=2
					vm.useNo=Atkdfs.objects.get(id=examID).atkdfsNo
					vm.state=1
					vm.save()
				except Exception ,diag:
					logger.error('startvms:vgate start failed,'+str(diag))
					return 0
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
def clearExamRes(examID):
	res = Res.objects.filter(Q(resid=examID) & Q(restype = 2))
	for r in res:
		r.delete()

def controlVm(request):
	examid = request.POST["examid"]
	sptype = request.POST["sptype"]
	host_ip = request.POST["host_ip"]

	# try:
	# 	cmd = "/usr/local/bin/ovs-vsctl del-br br1_"+str(examid)
	# 	os.system(cmd)
	# except:
	# 	pass
	resvms = Res.objects.filter(resid=examid,restype=2)
	examno = Atkdfs.objects.get(id=examid).atkdfsNo

	host_id = 1
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None

	for resvm in resvms:
		
		if resvm.rtype == "imgvshls":
			try:
				ip = Vswitch.objects.get(name=resvm.rname).containerIP
			except:
				ip = None
		elif resvm.rtype == "imgls":
			try:
				ip = Vm.objects.get(name=resvm.rname).containerIP
			except:
				ip = None
		elif resvm.rtype == "imgvgtls":
			try:
				ip = Vgate.objects.get(name=resvm.rname).containerIP
			except:
				ip = None
		else:
			ip = Host.objects.get(id=2).hostname
		if ip and ip == host_ip:
			if sptype=="stop":
				if resvm.rtype=="imgvshls" :
					if conn :
						br = resvm.rname
						try:
							cmddel = "/usr/local/bin/ovs-vsctl del-br " + br
							os.system(cmddel)

							# cmdlist = '/usr/local/bin/ovs-vsctl list-ports br1'
							# status, output=commands.getstatusoutput(cmdlist)
							# outputlist=output.split('\n')
							# if 'patch-to-eth'+br in outputlist:
							# 	cmd = "/usr/local/bin/ovs-vsctl del-port br1" +' patch-to-eth'+br
							# 	os.system(cmd)
							try:
								vm=Vswitch.objects.get(name=br)
								vm.delete()
							except:
								pass
						except:
							logger.error("Vswitch or cmddel failed")
				elif resvm.rtype=="pswitch" :
					pswitch = Device.objects.filter(devtype="pswitch",examuseNo=examno,usetype=2)
					for ps in pswitch:
						ps.examuseNo = None
						ps.usetype=None
						ps.state = 0

						ps.save()
				elif resvm.rtype=="pc" :
					pcs = Device.objects.filter(devtype="pc",examuseNo=examno,usetype=2)
					for pc in pcs:
						pc.examuseNo = None
						pc.usetype=None
						pc.state = 0

						pc.save()
				elif resvm.rtype=="pgate" :
					pgate = Device.objects.filter(devtype="pgate",examuseNo=examno,usetype=2)
					for pg in pgate:
						pg.examuseNo = None
						pg.usetype=None
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
					except Exception:
						logger.exception('destroy domain error: {0}'.format(vmgt.name))

					vmgt.state=0#停止
					vmgt.usetype=None
					vmgt.useNo=None
					try:
						xml = dom.XMLDesc(0)
						tree = ET.fromstring(xml)
						interface1 = tree.find("devices").findall('interface')
						for i,interface in  enumerate(interface1):
							if interface.get('type') =="direct":
								if resvm.rtype=="imgls":
									interface.find('source').set('dev','br2')
								else:#vgate
									if interface.find('source').get('dev') != str(i):
										interface.find('source').set('dev',str(i))
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
					try:
						dom.resume()
						vmgt.state = 1#启动
					except Exception:
						logger.exception('resume domain error: {0}'.format(vmgt.name))
				else:#sptype =="suspend"
					try:
						dom.suspend()
						vmgt.state=2#暂停，Vm数据表使用的是bool类型？？？？？？
					except Exception:
						logger.exception('suspend domain error: {0}'.format(vmgt.name))
				vmgt.save()
			
	
	conn.close()
	return HttpResponse(1)

def clearExamAnswerInfo(examID):
	ansinfos = AnswerInfo.objects.filter(Q(examid=examID) & Q(anstype = 2))
	for ansinfo in ansinfos:
		ansinfo.delete()
def clearAtkGroQue(examID):
	atkgros = AtkdfsGroup.objects.filter(Q(atkdfsID=examID))
	for atkgro in atkgros:
		atkgro.quesID=None
		atkgro.copytopo=None
		atkgro.save()
def atkdfsHistoryCur(request):
	global logger
	data={}
	dic={}
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examCur: get examination ID error")
			raise Http404
		examno = Atkdfs.objects.get(id=examid).atkdfsNo
		path = os.path.join( HERE , 'document/atkfile/')
		filenames=os.listdir(path)
		for filename in filenames:
			f=filename.split('_')#获取到_前面的禁赛编号
			if examno == f[0]:
				fileno=filename
				dic[f[1].split('.')[0]]=fileno
		dic=OrderedDict(sorted(dic.items(), key=lambda t:t[0], reverse=True))
		data['files'] = dic

		return HttpResponse(json.dumps(data))				
def delHistoryCur(request):
	global logger
	result = 1
	data={}
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examCur: get examination ID error")
			result = 0
		examno = Atkdfs.objects.get(id=examid).atkdfsNo
		path = os.path.join( HERE , 'document/atkfile/')
		filenames=os.listdir(path)

		for filename in filenames:
			f=filename.split('_')
			if examno == f[0]:
				cmd='rm -rf '+path+filename
				os.system(cmd)
		data['result'] = result
		return HttpResponse(json.dumps(data))
def atkdfsCur(request):
	global logger
	result = 0
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examCur: get examination ID error")
			raise Http404
		exam = Atkdfs.objects.get(id=examid)

		if exam.atkdfsStatus == 3:
			xlsname=createcurxls(examid,exam,request)

			clearExamRes(examid)
			clearExamAnswerInfo(examid)
			clearAtkGroQue(examid)

			exam.atkdfsStatus=0
			exam.atkdfsEditTime=datetime.datetime.now()
			exam.save()

	return HttpResponse(xlsname)
def createcurxls(examid,exam,request):
	examres = Res.objects.filter(Q(resid=examid) & Q(restype=2))
	answerinfo = AnswerInfo.objects.filter(Q(examid=examid) & Q(anstype = 2))
	examtea = AtkdfsTeacher.objects.filter(atkdfsID=examid)
	examgroups = AtkdfsGroup.objects.filter(atkdfsID=examid)

	count1 = examres.count()
	count2 = examtea.count()
	if count1>count2:
		count = count1
	elif count1==0 and count2==0:
		count=1
	else:
		count = count2
	w = Workbook(encoding='utf-8')
	font0 = xlwt.Font()
	font0.name = 'Times New Roman'
	# font0.colour_index = 2
	font0.bold = True
	style0 = xlwt.XFStyle()
	style0.font = font0

	ws = w.add_sheet('基本信息')

	ws.write_merge(0,0,0,0,"攻防编号",style0)#前面2个数字是行，后面两个是列
	ws.write_merge(0,0,1,1,"攻防名称",style0)
	ws.write_merge(0,0,2,2,"试卷编号",style0)
	ws.write_merge(0,0,3,3,"试卷名称",style0)
	ws.write_merge(0,0,4,4,"操作教师账号",style0)
	ws.write_merge(0,0,5,5,"教练账号",style0)
	ws.write_merge(0,0,6,6,"攻防开始时间",style0)
	ws.write_merge(0,0,7,7,"攻防结束时间",style0)
	ws.write_merge(0,0,8,8,"归档时间",style0)
	ws.write_merge(0,0,9,9,"使用的资源",style0)
	ws.write_merge(0,0,10,10,"资源镜像",style0)

	ws.write_merge(0,0,11,11,"是否控制台",style0)
	ws.write_merge(0,0,12,12,"使用学生学号",style0)


	ws.write_merge(1,count,0,0,exam.atkdfsNo)
	ws.write_merge(1,count,1,1,exam.atkdfsName)
	ws.write_merge(1,count,2,2,exam.atkdfsPaperID.papid)
	exampapername = exam.atkdfsPaperID.papname
	ws.write_merge(1,count,3,3,exampapername)

	teaccount=Teacher.objects.filter(id=request.session["userid"])
	if teaccount:
		ws.write_merge(1,count,4,4,teaccount[0].account)#操作教师
	else:
		ws.write_merge(1,count,4,4,'已删除')

	
	for i in range(0,count2):
		ws.write_merge(i+1,i+1,5,5,examtea[i].teaID.account)#操练

	ws.write_merge(1,count,6,6,exam.atkdfsStartTime.strftime("%Y-%m-%d %H:%M"))
	ws.write_merge(1,count,7,7,exam.atkdfsEndTime.strftime("%Y-%m-%d %H:%M"))
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	ws.write_merge(1,count,8,8,now)
	if examres:
		for i in range(0,count1):
			ws.write_merge(i+1,i+1,9,9,examres[i].rname)
			ws.write_merge(i+1,i+1,10,10,examres[i].insname)
			ws.write_merge(i+1,i+1,11,11,examres[i].isconsole)
			if examres[i].usebystu==None:
				ws.write_merge(i+1,i+1,12,12,'--')
			else:
				ws.write_merge(i+1,i+1,12,12,examres[i].usebystu.stuno)

	ws1 = w.add_sheet('成绩统计',style0)#------------------------------------------------团队成绩统计tab页
	ws1.col(2).width = 8000
	ws1.col(3).width = 4000
	ws1.col(4).width = 4000
	ws1.write_merge(0,0,0,0,"团队名称",style0)
	ws1.write_merge(0,0,1,1,"团队队长",style0)
	ws1.write_merge(0,0,2,2,"团队成员[姓名（学号）]",style0)
	ws1.write_merge(0,0,3,3,"得分",style0)
	groupresultS={}
	grototalinfo={}
	for i in range(0,examgroups.count()):
		score=0
		groinfo={}
		groupresult = {}
		group=examGetGroups(examgroups[i].groupID.id)
		groinfo['gname']=group[0]["gname"]
		groinfo['gcaptain']=group[0]["captain"]
		groinfo['gronum_name']=group[0]["gronum_name"]

		answers = answerinfo.filter(Q(groupid=group[0]["id"]))
		lasttime = None
		if answers:
			groupresult={}
			for ans in answers:
				anslist={}
				if not lasttime:
					lasttime = ans.extime
				if ans.is_correct == True:
					last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
					ex = ans.extime.strftime("%Y-%m-%d %H:%M:%S")
					if (cmp(last,ex)<=0):
						lasttime = ans.extime
					sco = ans.queid.qscore.split(',')
					score+=int(sco[ans.keyid-1])
				anslist[int(ans.keyid)]=ans.answer.encode('utf-8')
				if ans.queid.qid in groupresult:
					groupresult[ans.queid.qid][int(ans.keyid)]=ans.answer.encode('utf-8')
				else:
					groupresult[ans.queid.qid]	= anslist
			groupresultS[examgroups[i].groupID.gname] = groupresult
				#.............................................................................


		else:
			lasttime=datetime.datetime.now()

		groinfo['score']=score
		groinfo['lasttime']=lasttime.strftime("%Y-%m-%d %H:%M:%S")
		grototalinfo[examgroups[i].groupID.gname] = groinfo
	data_time = OrderedDict(sorted(grototalinfo.items(), key=lambda t:t[1]['lasttime'], reverse=False))
	data_total = OrderedDict(sorted(data_time.items(), key=lambda t:t[1]['score'], reverse=True))
	i=0	
	for key in data_total:
		ws1.write_merge(i+1,i+1,0,0,data_total[key]['gname'])
		ws1.write_merge(i+1,i+1,1,1,data_total[key]["gcaptain"])
		ws1.write_merge(i+1,i+1,2,2,data_total[key]["gronum_name"])
		ws1.write_merge(i+1,i+1,3,3,data_total[key]["score"])
		i +=1

	ws2 = w.add_sheet('团队所属题目详情',style0)#------------------------------------------------团队成绩统计tab页
	ws2.write_merge(0,0,0,0,"团队名称",style0)
	ws2.write_merge(0,0,1,1,"题目编号",style0)
	ws2.write_merge(0,0,2,2,"题目内容",style0)
	ws2.write_merge(0,0,3,3,"题目连接",style0)
	ws2.write_merge(0,0,4,4,"key",style0)
	ws2.write_merge(0,0,5,5,"对应key的分数",style0)
	i=1
	for eg in examgroups:
		ws2.write_merge(i,i,0,0,eg.groupID.gname)
		ws2.write_merge(i,i,1,1,eg.quesID.qid)
		ws2.write_merge(i,i,2,2,eg.quesID.qtitle)
		inf=Infiltration.objects.filter(queid_id=eg.quesID_id)
		if inf:
			ws2.write_merge(i,i,3,3,inf[0].link)
			ws2.write_merge(i,i,4,4,inf[0].result)
			ws2.write_merge(i,i,5,5,eg.quesID.qscore)
		i=i+1

	ws3 = w.add_sheet('答题详情',style0)#------------------------------------------------
	ws3.write_merge(0,0,0,0,"团队名称",style0)
	ws3.write_merge(0,0,1,1,"所提key",style0)
	ws3.write_merge(0,0,2,2,"key所属题",style0)
	i=0
	j=1
	for gn in groupresultS:
		lenc=len(groupresultS[gn])	
		ws3.write_merge(i+1,i+lenc,0,0,gn,style0)
		for q in groupresultS[gn]:
			ws3.write_merge(j,j,1,1,str(groupresultS[gn][q]))
			ws3.write_merge(j,j,2,2,q)
			j=j+1
		i=i+lenc

	xlsname=exam.atkdfsNo+'_'+datetime.datetime.now().strftime("%Y%m%d%H%M%s")+".xls"
	
	w.save(xlsname)


	path = os.path.join( HERE , 'document/atkfile/')
	if not os.path.exists(path):
		os.makedirs(path)
	command= "mv "+xlsname+" "+path
	os.system(command)
	return xlsname
