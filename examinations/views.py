#-*- coding: utf-8 -*- 

'''
1. 添加竞赛：调用examSave方法，根据前端提交的数据，在Examinations表中添加一条数据，并根据选择的教练和
参加的团队，分别在ExamTeacher和ExamGroup中添加数据；

2. 编辑竞赛：首先调用examEdit方法，获取选中竞赛的所有信息，用于填充表单，在用户点击保存后，调用examUpdate
方法，修改数据库中保存的数据；

3. 启动竞赛：调用examControl方法，首先获取竞赛所使用的试卷，并由试卷获取题目中所有的拓扑图，然后调用
ftTopos方法，先调用controlChecklab方法清除所有服务器上启动但未使用的虚拟机，然后将拓扑图尽可能平均地
分配给所有的服务器(一个拓扑图只能分配给一台服务器)，最后调用每台服务器上的controlRes方法，并为其传递
分配的拓扑图数据。controlRes方法为拓扑图中的每个设备都分配并启动一个虚拟机，并使用openvswitch创建虚拟
交换机，将虚拟机连接到虚拟交换机之上，实现虚拟机之间的通信；

4. 暂停竞赛：调用examControl方法，获取相关试卷与拓扑图，调用gbTopos方法，遍历所有服务器，并调用每台服
务器上的controlVm方法，该方法只处理与自己相关的所有虚拟机，这里会将与选中竞赛相关的所有虚拟机给暂停掉，
最后修改完成后，在examControl方法中，修改数据库中该竞赛的状态；

5. 停止竞赛：依然调用examControl方法，获取相关试卷与拓扑图，调用gbTopos方法，遍历所有服务器，并调用
controlVm方法，将本机上与选中竞赛相关的虚拟机全部关闭，并删除为其创建的openvswitch虚拟交换机，最后回到
examControl方法中，修改数据库中该竞赛的状态；

6. 恢复竞赛：暂停竞赛后，可以再次点击启动按键恢复竞赛，首先调用examControl方法，获取拓扑图，然后调用
gbTopos方法，遍历调用所有服务器上的controlVm方法，将所有与选中竞赛相关的虚拟机，恢复至启动状态，最后
回到examControl方法中，修改数据库中该竞赛的状态；

7. 竞赛详情：调用examDisplay方法，从数据库中获取与竞赛相关的所有数据，并返回给前端页面；

8. 统计归档并导出：停止竞赛后，需要将本次竞赛的数据导出并保存为excel文件，调用examCur方法，将竞赛信息
以及各个团队的答题、得分与排名情况导出，并保存为excel文件，存放在服务器上；

9. 历史存档记录：调用examHistoryCur方法，根据竞赛id，获取存放在服务器上的所有历史归档excel文件，并返回
给前端页面，以供下载；

10. 简答题打分界面：调用askActualGrade方法，返回一个新的html页面，用于显示当前竞赛中学生提交的所有简答题；

11. 简答题打分：选中一个简答题，点击打分按键，调用getAnsInfo方法，获取简答题的答案，教练打分后，点击保存
，调用givemark方法，如果该简答题已经被别的教练打过分，则打分不成功，否则打分成功；

12. 竞赛展现界面：调用examination_show方法，返回一个新的html页面，页面加载过程中，调用get_exam_info获取
指定竞赛的详细信息，并返回给前端页面，页面加载完成后，每隔30秒，前端页面请求一次get_new_datas方法，获取
最新的竞赛数据，并返回；

13. 删除竞赛：首先调用delHistoryCur方法，删除与选中竞赛有关的所有归档excel文件，然后调用examDelete方法，
从数据库中删除与该竞赛有关的所有数据。
'''

from django.shortcuts import render_to_response
from teachers.models import Teacher
from papers.models import *
from questions.models import *
from vms.models import *
from vgates.models import *
from vswitches.models import *
from sysmgr.models import *
from students.models import Student
from groups.models import *
from tsssite.server import *
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT
import sys, os, libvirt, subprocess,commands
from xlwt import *
import xlwt
from libvirt import libvirtError
from examinations.models import *
from client.models import *
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import time
import json
import zipfile
import logging
from django.db.models import Q
from devices.models import Device
import pdb
# from vms.views import *
# from  import createbr
from xml.etree import cElementTree as ET
from  xml.dom import minidom
# from tsssite.settings import CONSOLE_ETH
from tsssite.settings import HERE
import urllib
import urllib2
import sys
from os.path import basename

from collections import OrderedDict

logger = logging.getLogger('mysite.log')

reload(sys)
sys.setdefaultencoding('utf8')

vm_ovs ={}
vm_vgt = {}
g_ethlist = {}
rectFlag = {}
br_MacAddr={}#vgate的mac地址
br_Addr={}#ovs和终端的ip
container_ip = ""

#根据Vswitch表格创建br
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
def examManage(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	examSelect = ''

	currenttea = Teacher.objects.get(id=request.session['userid'])
	if currenttea.roletype == 0:#教练员
		examteas = ExamTeacher.objects.filter(teaID_id=currenttea.id)
		examteaids=[]
		for examtea in examteas:
			examteaids.append(int(examtea.examID_id))
		exams = Examinations.objects.filter(id__in=examteaids)
	else:
		exams = Examinations.objects.order_by('-id')

	if 'textFilter' in request.GET and request.GET['textFilter']:
		examFilter = request.GET.get('textFilter', '')
		exams = exams.filter(Q(examNo__icontains=examFilter)|Q(examName__icontains=examFilter))
		examSelect = examFilter
		request.session['examSelect'] = examSelect

	if 'examinationSelect' in request.GET:
		exams = Examinations.objects.order_by('-id')
		examFilter = request.GET.get('examinationSelect', '')
		exams = exams.filter(Q(examNo__icontains=examFilter)|Q(examName__icontains=examFilter))
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
	return render_to_response('templates/examinations.html',
							{'examSelect':examSelect,
							'examList':examList,
							'exams':exams,
							'page_range':page_range,
							'nu':exams.count(),
							},
							context_instance=RequestContext(request))


def examDisplay(request):
	global logger
	if request.method == 'POST':
		try:
			examID = request.POST['Info']
			exam = Examinations.objects.get(id=examID)
			gros = ExamGroup.objects.filter(examID=examID).order_by('-id')
			teas = ExamTeacher.objects.filter(examID=examID).order_by('-id')
		except:
			logger.error('examDisplay:get examID failed')
			raise Http404

	data = {}
	data["examID"] = exam.id
	data["examNo"] = exam.examNo
	data["examName"] = exam.examName
	data["examDescription"] = exam.examDescription
	data["examCreator"] = exam.examCreatorID.teaname
	data["examPaper"] = exam.examPaperID.papname
	data["examStartTime"] = exam.examStartTime.strftime("%Y-%m-%d %H:%M")
	data["examEndTime"] = exam.examEndTime.strftime("%Y-%m-%d %H:%M")
	data["examEditTime"] = exam.examEditTime.strftime("%Y-%m-%d %H:%M")
	data["examCreateTime"] = exam.examCreateTime.strftime("%Y-%m-%d %H:%M")
	data["examStatus"] = exam.examStatus
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

def examGetPapers(filterStr):
	paps = Paper.objects.order_by('-id')

	if filterStr:
		paps = paps.filter(Q(papid__icontains=filterStr)|Q(papname__icontains=filterStr))

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

#获取添加考试所需的试卷，教师，学生信息
def examAddGetInfo(request):
	#pdb.set_trace()
	data = {}
	papers = examGetPapers('')
	groups = examGetGroups('')

	teachers = examGetTeachers('')

	data["papers"] = papers
	data["groups"] = groups
	data["teachers"] = teachers

	return HttpResponse(json.dumps(data))

def addExamGroup(examID, studentIDs):
	if studentIDs:
		for item in studentIDs:
			ExamStu = ExamGroup(examID_id=examID, groupID_id=int(item))
			ExamStu.save()

def addExamTeacher(examID, teacherIDs):
	for item in teacherIDs:
		ExamTea = ExamTeacher(examID_id=examID, teaID_id=int(item))
		ExamTea.save()

def clearExamGroup(examID):
	ExamGro = ExamGroup.objects.filter(examID_id = int(examID))
	for item in ExamGro:
		item.delete()

def clearExamTeacher(examID):
	ExamTea = ExamTeacher.objects.filter(examID_id = int(examID))
	for item in ExamTea:
		item.delete()

def addPaperFrequency(paperID):
	papid = int(paperID)
	paper = Paper.objects.get(id=papid)
	paper.frequency += 1;
	paper.save()
	return paper.frequency

def subPaperFrequency(paperID):
	papid = int(paperID)
	paper = Paper.objects.get(id=papid)
	paper.frequency -= 1;
	if paper.frequency < 0:
		paper.frequency = 0
	paper.save()
	return paper.frequency

def examCheckexamno(request):
	global logger
	exams = Examinations.objects.order_by("-id")
	judgeexamno = 0
	if request.method == 'POST':
		try:
			strExamInfo = request.POST['Info']
		except ValueError:
			logger.error("examination")
			raise Http404()
		for exam in exams:
			if strExamInfo == exam.examNo:
				judgeexamno = 1
				break
		data={}
		data["judgeexamno"] = judgeexamno
		return HttpResponse(json.dumps(data))

def examSave(request):
	global logger
	if request.method == 'POST':
		try:
			strExamInfo = request.POST['Info']
		except ValueError:
			logger.error("examSave: get examination information error")
			raise Http404

	jsonExamInfo = json.loads(strExamInfo)
	start = datetime.datetime.strptime(jsonExamInfo["startTime"],"%Y-%m-%d %H:%M") 
	end=datetime.datetime.strptime(jsonExamInfo["endTime"],"%Y-%m-%d %H:%M") 
	exam = Examinations(examNo=jsonExamInfo['no'],
						examName=jsonExamInfo['name'],
						examDescription=jsonExamInfo['description'],
						examStartTime=start,
						examEndTime=end,
						examCreatorID_id=int(request.session['userid']),
						examCreateTime=datetime.datetime.now(),
						examEditTime=datetime.datetime.now(),
						examStatus=0,#default
						examPaperID_id=int(jsonExamInfo['paperID']))
	exam.save()

	examID = exam.id
	
	if jsonExamInfo["studentIDs"][0]:#添加了空团队
		addExamGroup(examID, jsonExamInfo["studentIDs"])
	addExamTeacher(examID, jsonExamInfo["teacherIDs"])
	addPaperFrequency(int(jsonExamInfo['paperID']))
	# for item in jsonExamInfo["studentIDs"]:
	# 	ExamStu = ExamStudent(examID_id=examID, stuID_id=int(item))
	# 	ExamStu.save()

	# for item in jsonExamInfo["teacherIDs"]:
	# 	ExamTea = ExamTeacher(examID_id=examID, teaID_id=int(item))
	# 	ExamTea.save()
	return HttpResponseRedirect("/examinations/")

def examDelete(request):
	global logger
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examDelete: get examination ID error")
			raise Http404

	clearExamGroup(examid)
	clearExamTeacher(examid)

	exam = Examinations.objects.get(id=examid)
	
	exam.delete()
	subPaperFrequency(exam.examPaperID.id)
	return HttpResponseRedirect("/examinations/")

def examEdit(request):
	global logger
	data = {}
	try:
		if request.method == 'POST':
			examid = int(request.POST['Info'])
			examination = Examinations.objects.get(id=examid)
			examTea = ExamTeacher.objects.filter(examID_id=examid).order_by("id")
			examGro = ExamGroup.objects.filter(examID_id=examid)

			exam={}
			exam['examID'] = examination.id
			exam['examNo'] = examination.examNo
			exam['examName'] = examination.examName
			exam['examDescription'] = examination.examDescription
			exam['examStartTime'] = examination.examStartTime.strftime("%Y-%m-%d %H:%M")
			exam['examEndTime'] = examination.examEndTime.strftime("%Y-%m-%d %H:%M")
			exam['examPaperID'] = examination.examPaperID.id

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

			data['status'] = examination.examStatus
	except:
		logger.error("examEdit:get examination ID error")
		data["result"] = 1
	else:
		data["result"] = 0
	finally:
		return HttpResponse(json.dumps(data))

def examUpdate(request):
	global logger
	if request.method == 'POST':
		try:
			examInfo =  request.POST['Info']	

		except ValueError:
			logger.error('examUpdate get examination information failed')
			raise Http404

	jsonexamInfo = json.loads(examInfo)

	examID = int(jsonexamInfo["id"])

	exam = Examinations.objects.get(id=examID)

	if int(jsonexamInfo["paperID"]) != exam.examPaperID.id:
		subPaperFrequency(exam.examPaperID.id)
		exam.examPaperID_id = int(jsonexamInfo["paperID"])
		addPaperFrequency(int(jsonexamInfo["paperID"]))

	start = datetime.datetime.strptime(jsonexamInfo["startTime"],"%Y-%m-%d %H:%M") 
	end=datetime.datetime.strptime(jsonexamInfo["endTime"],"%Y-%m-%d %H:%M") 

	exam.examNo = jsonexamInfo["no"]
	exam.examName = jsonexamInfo["name"]
	exam.examStartTime = start
	exam.examEndTime = end
	exam.examDescription = jsonexamInfo["description"]
	# exam.examCreateTime=datetime.datetime.now()
	exam.examEditTime=datetime.datetime.now()
	exam.save()

	clearExamGroup(examID)
	clearExamTeacher(examID)
	addExamGroup(examID, jsonexamInfo["studentIDs"])
	addExamTeacher(examID, jsonexamInfo["teacherIDs"])
	return HttpResponseRedirect("/examinations/")

#验证数据库的状态和后台虚拟机状态是否一致
def controlCheckState(conn):
	global container_ip
	vms = Vm.objects.filter(containerIP=container_ip).order_by('-id')
	for vm in vms:
		try:
			dom = conn.lookupVM(vm.name)
			if dom.info()[0] == 5 and vm.state==1:#5关机；1开机；3暂停
				vm.state=0
				vm.save()
			elif dom.info()[0] == 1 and vm.state==0:#5关机；1开机；3暂停
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
								dom.destroy()#没有给虚拟机和br解绑？？？？？？？？？？？？？？？？？
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

def controlGetQuesID(request,paperID):
	qusetionSkillIDs = []
	questionInfiltraIDs = []
	if paperID:
		paperquestions = PaperQuestion.objects.filter(paperid=paperID)
	for item in paperquestions:
		queid = item.questionid.id
		que = Question.objects.get(id = queid)
		if que.qtype == '2':#技能题
			qusetionSkillIDs.append(queid)
		if que.qtype == '3':
			questionInfiltraIDs.append(queid)
	return qusetionSkillIDs,questionInfiltraIDs#id是Skill models中的queid字段，此字段也可以唯一标识

def controlGetTopo(request,qusetionSkillIDs,questionInfiltraIDs):
	topos = []	
	for sid in qusetionSkillIDs:
		topo = Skill.objects.get(queid=sid).topo
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
			jsontopo = json.loads(topo)#
			topos.append(jsontopo)
		except :
			# print "get topo failed"
			pass


	for iid in questionInfiltraIDs:
		topo = Infiltration.objects.get(queid=iid).topo
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
			jsontopo = json.loads(topo)#
			topos.append(jsontopo)
		except :
			# print "get topo failed"
			pass


	return topos
#遍历所有拓扑图，按拓扑图单个启动
def controlRes(request):
	global vm_ovs
	global vm_vgt
	global rectFlag
	global g_ethlist
	global br_MacAddr
	global br_Addr
	global container_ip
	host_id = 1
	host = Host.objects.get(id=host_id)
	try:
		conn = ConnServer(host)
	except libvirtError as e:
		conn = None
	# pdb.set_trace()
	teacherid = request.POST["teacherid"]
	topos = json.loads(request.POST["topos"])
	examID = request.POST["examID"]
	container_ip = request.POST["containerIP"]

	controlCheckState(conn)

	for topo in topos:
		vm_ovs={}
		vm_vgt={}
		rectFlag={}
		g_ethlist={}

		br_MacAddr={}
		br_Addr={}
		#创建br,使用vm_ovs和vm_vgt关联br和镜像rect的关系
		for key, value in topo["states"].items():
			addr = value["props"]["addr"]["value"]
			imgtype= value["props"]["type"]["value"]
			imgname = value["props"]["instance"]["value"]
			if imgtype == "imgvshls":
				rectFlag[key]='imgvshls'
				result = startovs(conn,topo,teacherid,examID,key,imgtype, imgname, addr)
				if result !=1:
					return HttpResponse(result)
			if imgtype == "pswitch":
				rectFlag[key]='pswitch'
				result = startpswitch(conn,topo,teacherid,examID,key,imgtype, imgname, addr)
				if result !=1 and result !=None:#当该物理设备本身没有连接到服务器
					return HttpResponse(result)
			if imgtype=="imgvgtls":
				rectFlag[key]='imgvgtls'
				result = startvgt(conn,topo,teacherid,examID,key,imgtype, imgname, addr)
				if result !=1:
					return HttpResponse(result)
			if imgtype=="pgate":
				rectFlag[key]='pgate'
				result = startpgate(conn,topo,teacherid,examID,key,imgtype, imgname, addr)
				if result !=1 and result !=None:
					return HttpResponse(result)
		logger.info('before starting all vms !')

		#关联好关系之后统一分配vm，和vgte，并绑定br，然后启动
		for key, value in topo["states"].items():
			addr = value["props"]["addr"]["value"]
			imgtype= value["props"]["type"]["value"]
			imgname = value["props"]["instance"]["value"]
			if imgtype != "imgvshls" and imgtype != "pswitch":
				result = startvm(conn,topo,teacherid,examID,key,imgtype, imgname, addr)
				if result !=1:
					return HttpResponse(result)

		logger.info('after starting all vms !')
		for key in br_MacAddr:
			if br_MacAddr[key] in br_Addr:
				keymac=key.split(',')
				vr = VgateRes(vgateName=keymac[0],macAddr=keymac[1],pathKey=br_Addr[br_MacAddr[key]][0],pathtext=br_Addr[br_MacAddr[key]][1],userid=teacherid,restype=1,resid=examID)
				vr.save()
		logger.info('after saving  vgate internet access information!')
	return HttpResponse(1)

def startpgate(conn,topo,teacherid,examID,gtkey,gttype, gtname, gtaddr):
	global vm_vgt
	global vm_ovs
	global g_ethlist
	global rectFlag
	pg = None
	if gttype == 'pgate':
		try:

			pg = Device.objects.get(devname=gtname,devtype="pgate",state=0)
			examres = Res(userid=teacherid,rectname=gtkey,rname=gtname,insname=gtname,rtype="pgate",resid=examID,addr=gtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pg.state = 1
			pg.examuseNo = Examinations.objects.get(id=examID).examNo
			pg.usetype=1
			pg.save()

			ethx= pg.ethx
			if ethx == None:#物理设备eth为空，则认为是外部用网线连接
				return
			g_ethlist[gtkey] = ethx.split(',')#否则将eth记录到g_ethlist变量中，然后给绑定的设备使用
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
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+gate_ethlist[gtkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=gate_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
							examres.save()
						except :
							logger.error('startpgate:1get pgate eth Device failed')

							# print "get eth failed"
							return 0

						g_ethlist[gtkey].pop(0)#pop已使用的eth
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
								examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+gate_ethlist[gtkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=gate_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
								examres = Res(userid=teacherid,rectname=gtkey,rname=brname,insname=g_ethlist[gtkey][0],rtype="imgvshls",resid=examID,addr=gtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
							except :
								logger.error('startpgate:4get pgate eth Device failed')
								return 0
							g_ethlist[gtkey].pop(0)
							vm_ovs[brname] = rectfrom
						else:
							return 5

	return 1

def startvgt(conn,topo,teacherid,examID,vgtkey,imgvgttype, imgvtname, vgtaddr):
	global vm_vgt
	global vm_ovs
	global rectFlag

	pcname=''
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
					examres = Res(userid=teacherid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=vgtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

			elif vgtkey==rectto and (rectfromtype== "imgls" or rectfromtype== "pc" or (rectfromtype== "imgvgtls" and rectfrom not in rectFlag) or rectfromtype== "pgate"):
				try:
					brname = createbr()
					cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
					os.system(cmd)
					examres = Res(userid=teacherid,rectname=vgtkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=vgtaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

def startpswitch(conn,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr):	
	global vm_ovs
	global g_ethlist
	global rectFlag
	global br_Addr
	ps = None

	if imgbrtype == "pswitch":
		try:
			ps = Device.objects.get(devname=imgbrname,devtype="pswitch",state=0)
			examres = Res(userid=teacherid,rectname=brkey,rname=imgbrname,insname=imgbrname,rtype="pswitch",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			ps.state = 1
			ps.examuseNo = Examinations.objects.get(id=examID).examNo
			ps.usetype=1
			ps.save()

			ethx = ps.ethx
			if ethx == None:#没有连接在平台服务器上
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
				if tecttotype=="imgls"or tecttotype=="imgvgtls":#一定需要eth,也就是g_ethlist[brkey]一定不为空，如果为空则return 5
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
								examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
				if tectfromtype=="imgls"or tectfromtype=="imgvgtls" :
					if g_ethlist[brkey]!=[''] and g_ethlist[brkey]!=[]:
						brname = createbr()
						cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
						os.system(cmd)
						cmd1 = "/usr/local/bin/ovs-vsctl add-port "+brname+" "+g_ethlist[brkey][0]
						os.system(cmd1)
						try:
							examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
								examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=g_ethlist[brkey][0],rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
								examres.save()
								vm_ovs[brname] = rectfrom

							except Exception:
								logger.error('startpswitch: 4get eth failed')
								return 0
							g_ethlist[brkey].pop(0)
						else:
							return 5
		return 1
#启动OVS		
def startovs(conn,topo,teacherid,examID,brkey,imgbrtype,imgbrname,braddr):	
	global vm_ovs
	global br_MacAddr
	global br_Addr
	if imgbrtype == "imgvshls":
		try:
			br = createbr()
			cmd = "/usr/local/bin/ovs-vsctl add-br " + br
			os.system(cmd)
			examres = Res(userid=teacherid,rectname=brkey,rname=br,insname=imgbrname,rtype=imgbrtype,resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

			if brkey == rectfrom:
				brname = createbr()
				cmd = "/usr/local/bin/ovs-vsctl add-br " + brname
				os.system(cmd)
				examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname="OVS",rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
				examres = Res(userid=teacherid,rectname=brkey,rname=brname,insname=br,rtype="imgvshls",resid=examID,addr=braddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
#br创建好之后分配vm和vgate,然后根据vm_ovs和vm_vgt里
# 记录的img和br绑定记录信息，绑定好br和vgate、vm,然后启动
def startvm(conn,topo,teacherid,examID,key,imgtype,imgname,vmaddr):
	global vm_ovs
	global vm_vgt
	global g_ethlist
	global container_ip
	pc =None
	ethlist = None
	vmisconsole=0
	if imgtype == "imgls":
		vmisconsole=int(topo["states"][key]["props"]["isconsole"]["value"])
		if not vmisconsole:
			try:
				imgid = Img.objects.get(name=imgname).id
			except:
				logger.error('startvms:vmimg not exist')
				return 4
			vms = Vm.objects.filter(state=0, imgtype=imgid, containerIP=container_ip).order_by('-id')
			if  vms:
				if conn:
					try:
						vmname = vms[0].name
						examres = Res(userid=teacherid,rectname=key,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,mac1='',mac2='',addr=vmaddr,isconsole=vmisconsole,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
						examres.save()
						dom = conn.lookupVM(vmname)
						result = vm_br(conn,dom,imgtype,key,vmname,vmaddr,vmisconsole)
						if result!=1:
							return result
						vmmac1 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[1]/mac/@address")
						vmmac2 = get_xml_path(dom.XMLDesc(0), "/domain/devices/interface[2]/mac/@address")
						if not vmmac1:
							vmmac1=""
						if not vmmac2:
							vmmac2=""
						dom.create() 
						time.sleep(3) 
						vm = Vm.objects.get(name=vms[0].name)

						examres.mac1=vmmac1
						examres.mac2=vmmac2
						examres.save()

						vm.state=1#启动
						vm.usetype=1
						vm.useNo=Examinations.objects.get(id=examID).examNo
						vm.save()
					except Exception ,diag:
						logger.error('startvms:vm start failed,'+str(diag))
						return 0
			#资源不够
			else:
				return 2
		else:#竞赛控制台不会分配虚拟机，直接绑定br0
			result  = convm_br(key,vmaddr)
			if result!=1:
				return result
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
		if ethlist!=['']:#pc连接的是物理资源，可以不予考虑
			examres = Res(userid=teacherid,rectname=key,rname=imgname,insname=imgname,rtype="pc",resid=examID,addr=vmaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			examres.save()
			pc.state = 1
			pc.examuseNo = Examinations.objects.get(id=examID).examNo
			pc.usetype=1
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

			# print "vgtimg not exist"
			return 4
		vms = Vgate.objects.filter(state=0, imgtype=imgvgtid, containerIP=container_ip).order_by('id')
		if  vms:
			if conn:
				try:
					vmname = vms[0].name

					examres = Res(userid=teacherid,rectname=key,rname=vms[0].name,insname=imgname,rtype=imgtype,resid=examID,mac1='',mac2='',addr=vmaddr,restype=1,lasttime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
					examres.save()

					dom = conn.lookupVM(vmname)
					result = vm_br(conn,dom,imgtype,key,vmname,vmaddr,vmisconsole)
					if result!=1:
						return result
				except libvirtError ,diag:
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

					vm.usetype=1
					vm.useNo=Examinations.objects.get(id=examID).examNo
					vm.state=1
					vm.save()
				except libvirtError ,diag:
					logger.error('startvms:vgate start failed,'+str(diag))
					return 0
					#pass
		else:
			return 2#资源不足

	elif imgtype=="pgate":
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
def convm_br(key,addr):#br0仅供竞赛控制台的br使用，br0连接eth
	global vm_ovs
	global vm_vgt
	global br_Addr
	for brname in vm_ovs:
		if key == vm_ovs[brname]:
			try:
				cmd7 = "/usr/local/bin/ovs-vsctl add-port br0"+" patch-to-eth"+brname
				os.system(cmd7)
				cmd10 = "/usr/local/bin/ovs-vsctl add-port "+brname+" patch-to-br0eth"+brname
				os.system(cmd10)
				cmd8 = "/usr/local/bin/ovs-vsctl set interface patch-to-br0eth"+brname+" type=patch"
				os.system(cmd8)
				cmd9 = "/usr/local/bin/ovs-vsctl set interface patch-to-eth"+brname+" options:peer=patch-to-br0eth"+brname
				os.system(cmd9)
				cmd11 = "/usr/local/bin/ovs-vsctl set interface patch-to-eth"+brname+" type=patch"
				os.system(cmd11)
				cmd12 = "/usr/local/bin/ovs-vsctl set interface patch-to-br0eth"+brname+" options:peer=patch-to-eth"+brname
				os.system(cmd12)

				# br_Addr[brname]=addr
			except:
				# print "console_br0 failed"
				return 6
	return 1

def vm_br(conn,dom,imgtype,key,vmname,addr,vmisconsole):
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
		for brname in vm_vgt:
			if len(vm_vgt[brname])==1 and key == vm_vgt[brname][0]:
				try:
					xml=dom.XMLDesc(0)
					tree = ET.fromstring(xml)
					interface1 = tree.find("devices").findall("interface")
					for interface in interface1:
						devnum = interface.find('source').get('dev')
						if interface.get('type') =="direct" and  devnum in frebr:
							interface.find('source').set('dev',brname)
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
				xx =  ET.tostring(tree)
				xml = xx
				conn.defineXML(xml)
			except libvirtError ,diag:
				logger.error('vm_br:1xml  failed,'+str(diag))
				return 0
	return 1

def controlVm(request):
	examid = request.POST["examid"]
	sptype = request.POST["sptype"]
	host_ip = request.POST["host_ip"]

	resvms = Res.objects.filter(resid=examid,restype=1)
	examno = Examinations.objects.get(id=examid).examNo

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

		if ip and ip == host_ip:  # 服务器只处理自己的虚拟机
			if sptype=="stop":
				if resvm.rtype=="imgvshls" :
					if conn :
						br = resvm.rname
						try:
							cmddel = "/usr/local/bin/ovs-vsctl del-br " + br
							os.system(cmddel)

							cmdlist = '/usr/local/bin/ovs-vsctl list-ports br0'
							status, output=commands.getstatusoutput(cmdlist)
							outputlist=output.split('\n')
							if 'patch-to-eth'+br in outputlist:
								cmd = "/usr/local/bin/ovs-vsctl del-port br0" +' patch-to-eth'+br
								os.system(cmd)
							try:
								vm=Vswitch.objects.get(name=br)
								vm.delete()
							except:
								# print "Vswitch or cmddel failed"
								pass

						except:
							logger.error("Vswitch or cmddel failed")
							return HttpResponse(0)
				elif resvm.rtype=="pswitch" :
					pswitch = Device.objects.filter(devtype="pswitch",examuseNo=examno,usetype=1)
					for ps in pswitch:
						ps.examuseNo = None
						ps.usetype=None
						ps.state = 0

						ps.save()
				elif resvm.rtype=="pc" :
					pcs = Device.objects.filter(devtype="pc",examuseNo=examno,usetype=1)
					for pc in pcs:
						pc.examuseNo = None
						pc.usetype=None
						pc.state = 0

						pc.save()
				elif resvm.rtype=="pgate" :
					pgate = Device.objects.filter(devtype="pgate",examuseNo=examno,usetype=1)
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
					except:
						pass

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

					except libvirtError ,diag:
						logger.error('controlVm:'+str(diag))
				elif sptype =="resume":
					dom.resume()
					vmgt.state = 1#启动
				else:#sptype =="suspend"
					dom.suspend()
					vmgt.state=2#暂停，Vm数据表使用的是bool类型？？？？？？
				vmgt.save()
	conn.close()
	return HttpResponse(1)


def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()


# 分配拓扑图到多台服务器上启动
def fpTopos(teacherid,topos,examID):
	# 获取所有服务器上虚拟终端和安全设备的数量（启动数量和未使用数量）
	infos = {}
	servers = Host.objects.order_by('id')[1:]

	# 首先清除空闲的实验环境controlChecklab
	for server in servers:
		post("http://" + server.hostname + "/examinations/controlChecklab/", {"containerIP": server.hostname})

	for server in servers:
		infos[server.hostname] = {}
		infos[server.hostname]["used"] = 0
		infos[server.hostname]["imgs"] = {}
		infos[server.hostname]["topos"] = []

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

	# 模拟分配拓扑图
	for topo in topos:
		hasPhysics = False  # topo中存在物理设备时，为True。否则为False
		img_counts = {}  # 记录每种虚拟终端的数量，名字是固定的imgls,imgvgtls
		for k, v in topo["states"].items():
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

		# 找出能够启动拓扑图，同时启动虚拟机数量最少的服务器
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

		main_server = Host.objects.get(id=2).hostname
		if hasPhysics and (main_server in passer):
			passer = [main_server]
		elif hasPhysics:
			return 2

		min_count = -1
		host_ip = ""
		for p in passer:
			if min_count == -1:
				min_count = infos[p]["used"]
				host_ip = p
			elif min_count > infos[p]["used"]:
				min_count = infos[p]["used"]
				host_ip = p

		if host_ip == "":
			return 2
		# 将拓扑图添加到找出的服务器中infos
		infos[host_ip]["topos"].append(topo)
		for i, c in img_counts.items():
			infos[host_ip]["used"] += c
			infos[host_ip]["imgs"][i] -= c

	# 将分配结果分发到对应的服务器，请求controlRes

	re = 0
	for host, value in infos.items():
		datas = {"teacherid": teacherid, "topos": json.dumps(value["topos"]), "examID": examID, "containerIP": host}
		re = post("http://" + host + "/examinations/controlRes/", datas)
		if int(re) != 1:
			break
	return int(re)


# 关闭或停止所有的拓扑图
def gbTopos(examid, sptype):
	servers = Host.objects.order_by('id')[1:]
	re = 0
	for server in servers:
		ip = server.hostname
		re = post("http://" + ip + "/examinations/controlVm/", {"examid": examid, "sptype": sptype, "host_ip": ip})
		if int(re) != 1:
			break
	return int(re)

def examControl(request):
	global logger
	result = 0
	if not 'userid' in request.session:
		return HttpResponseRedirect('/Login/')

	teacherid = request.session["userid"]

	if request.method == 'POST':
		try:
			examID = int(request.POST["eid"])
		except ValueError:
			logger.error('examStart get examination information failed')
			raise Http404
			
		#由竞赛的ID获取试卷的ID
		paperID = Examinations.objects.get(id=examID).examPaperID.id
		#由试卷的ID分别获取技能题和渗透题的ID
		qusetionSkillIDs,questionInfiltraIDs = controlGetQuesID(request,paperID)

		#获取技能题和渗透题的ID topo
		topos = controlGetTopo(request,qusetionSkillIDs,questionInfiltraIDs)

		data = {}
		print request.POST["btnname"]
		if "start" == request.POST["btnname"]:
			#分配主机
			result = fpTopos(teacherid,topos,examID)
			if result ==1:#启动成功，修改竞赛状态
				exam = Examinations.objects.get(id=examID)
				exam.examStatus = 2#启动
				exam.examEditTime=datetime.datetime.now()
				exam.save()
			else:
				gbTopos(examID, "stop")
				clearExamRes(examID)#启动失败回滚，回收资源
		if "pause" == request.POST["btnname"]:#暂停竞赛
			result = gbTopos(examID, "suspend")
			if result:
				exam = Examinations.objects.get(id=examID)
				exam.examStatus = 1#暂停
				exam.examEditTime=datetime.datetime.now()
				exam.save()
		if "resume" == request.POST["btnname"]:#恢复竞赛
			result = gbTopos(examID, "resume")
			if result:
				exam = Examinations.objects.get(id=examID)
				exam.examStatus = 2#暂停
				exam.examEditTime=datetime.datetime.now()
				exam.save()
		if "stop" == request.POST["btnname"]:#停止竞赛，回收资源
			result = gbTopos(examID, "stop")
			if result:
				exam = Examinations.objects.get(id=examID)
				exam.examStatus = 3#已完成
				exam.save()
		data["result"] = result
		return HttpResponse(json.dumps(data))

def clearExamRes(examID):
	res = Res.objects.filter(Q(resid=examID) & Q(restype = 1))
	for r in res:
		r.delete()

def clearExamAnswerInfo(examID):
	ansinfos = AnswerInfo.objects.filter(Q(examid=examID) & Q(anstype = 1))
	for ansinfo in ansinfos:
		ansinfo.delete()

def examTotal(request):
	global logger
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examTotal: get examination ID error")
			raise Http404
		data = {}
		exam = Examinations.objects.get(id=examid)
		if exam.examStatus !=0:
			orderGroupdict = orderGroups(examid)
			arry = []
			for key in orderGroupdict:
				orderGroupdict[key]["groupname"] = key
				arry.append(orderGroupdict[key])
			data['orderGroups'] = arry
		return HttpResponse(json.dumps(data))

def orderGroups(examid):
	data = statisticGrade(examid)
	data_time = OrderedDict(sorted(data.items(), key=lambda t:t[1]['lasttime'], reverse=False))
	data_total = OrderedDict(sorted(data_time.items(), key=lambda t:t[1]['total'], reverse=True))
	return data_total

def statisticGrade(examid):
	grosGrade={}#{"groname":{"choscore":--,"skillscore":--}}
	examgroups = ExamGroup.objects.filter(examID=examid)
	answerinfo = AnswerInfo.objects.filter(Q(examid=examid) & Q(anstype = 1))
	for gro in examgroups:
		grograde={}
		choqnum = []
		skillqnum = []
		infilqnum = []
		answerinfos = answerinfo.filter(Q(groupid=gro.groupID_id) )
		choscore,skillscore,infilscore,lasttime,correctlist = getScoreByGroid(answerinfos)
		grograde["choscore"] = choscore
		grograde["skillscore"] = skillscore
		grograde["infilscore"] = infilscore
		grograde["total"] = choscore+skillscore+infilscore
		grograde["lasttime"] = lasttime
		for cl in correctlist:
			if cl.qtype=='1' :
				choqnum.append(cl.qid)#获得题目的编号
			elif cl.qtype=='2':
				skillqnum.append(cl.qid)#获得题目的编号
			elif cl.qtype=='3':
				infilqnum.append(cl.qid)#获得题目的编号				
		grograde["choqnum"]  = choqnum
		grograde["skillqnum"]  = skillqnum
		grograde["infilqnum"]  = infilqnum
		grosGrade[gro.groupID.gname] = grograde

	return grosGrade

def getScoreByGroid(answerinfo):
	choscore=0
	skillscore=0
	infilscore=0
	lasttime = None
	correctlist=[]

	if answerinfo:
		for ans in answerinfo:

			if not lasttime:
				lasttime = ans.extime
			if ans.is_correct == True:
				correctlist.append(ans.queid)
				last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
				ex = ans.extime.strftime("%Y-%m-%d %H:%M:%S")

				if (cmp(last,ex)<=0):
					lasttime = ans.extime
				sco = ans.queid.qscore.split(',')
				if ans.queid.qtype=='1' :
					choscore+=int(sco[ans.keyid-1])
				elif ans.queid.qtype=='2':
					skillscore+=int(sco[ans.keyid-1])
				elif ans.queid.qtype=='3':
					infilscore+=int(sco[ans.keyid-1])
	else:
		lasttime=datetime.datetime.now()
	return choscore,skillscore,infilscore,lasttime.strftime("%Y-%m-%d %H:%M:%S"),correctlist

def examHistoryCur(request):
	global logger
	data={}
	dic={}
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examCur: get examination ID error")
			raise Http404
		examno = Examinations.objects.get(id=examid).examNo
		path = os.path.join( HERE , 'document/file/')
		filenames=os.listdir(path)
		for filename in filenames:
			f=filename.split('_')#获取到_前面的竞赛编号
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
		examno = Examinations.objects.get(id=examid).examNo
		path = os.path.join( HERE , 'document/file/')
		filenames=os.listdir(path)

		for filename in filenames:
			f=filename.split('_')
			if examno == f[0]:
				cmd='rm -rf '+path+filename
				os.system(cmd)
		data['result'] = result
		return HttpResponse(json.dumps(data))

def examCur(request):
	global logger
	result = 0
	if request.method == 'POST':
		try:
			examid = int(request.POST['Info'])
		except ValueError:
			logger.error("examCur: get examination ID error")
			raise Http404
		exam = Examinations.objects.get(id=examid)
		if exam.examStatus == 3:
			xlsname=createcurxls(examid,exam,request)
			clearExamRes(examid)
			clearExamAnswerInfo(examid)
			exam.examStatus=0
			exam.examEditTime=datetime.datetime.now()
			exam.save()

	return HttpResponse(xlsname)#返回zip包的名称，前台直接download

def createcurxls(examid,exam,request):

	dirname=exam.examNo+'_'+datetime.datetime.now().strftime("%Y%m%d%H%M%s")
	
	path = os.path.join( HERE , 'document/file/')
	if not os.path.exists(path):
		os.makedirs(path)

	os.system('mkdir '+path+dirname)

	xlspath = os.path.join( HERE , 'document/file/'+dirname)

	examres = Res.objects.filter(Q(resid=examid) & Q(restype=1))
	answerinfo = AnswerInfo.objects.filter(Q(examid=examid) & Q(anstype = 1))
	examtea = ExamTeacher.objects.filter(examID=examid)
	examgroups = ExamGroup.objects.filter(examID=examid)
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

	ws.write_merge(0,0,0,0,"竞赛编号",style0)#前面2个数字是行，后面两个是列
	ws.write_merge(0,0,1,1,"竞赛名称",style0)
	ws.write_merge(0,0,2,2,"试卷编号",style0)
	ws.write_merge(0,0,3,3,"试卷名称",style0)
	ws.write_merge(0,0,4,4,"操作教师账号",style0)
	ws.write_merge(0,0,5,5,"教练账号",style0)
	ws.write_merge(0,0,6,6,"竞赛开始时间",style0)
	ws.write_merge(0,0,7,7,"竞赛结束时间",style0)
	ws.write_merge(0,0,8,8,"归档时间",style0)
	ws.write_merge(0,0,9,9,"使用的资源",style0)
	ws.write_merge(0,0,10,10,"资源镜像",style0)
	ws.write_merge(1,count,0,0,exam.examNo)
	ws.write_merge(1,count,1,1,exam.examName)
	ws.write_merge(1,count,2,2,exam.examPaperID.papid)
	exampapername = exam.examPaperID.papname
	ws.write_merge(1,count,3,3,exampapername)
	teaccount=Teacher.objects.filter(id=request.session["userid"])
	if teaccount:
		ws.write_merge(1,count,4,4,teaccount[0].account)#操作教师
	else:
		ws.write_merge(1,count,4,4,'已删除')

	
	for i in range(0,count2):
		ws.write_merge(i+1,i+1,5,5,examtea[i].teaID.account)#操练

	ws.write_merge(1,count,6,6,exam.examStartTime.strftime("%Y-%m-%d %H:%M"))
	ws.write_merge(1,count,7,7,exam.examEndTime.strftime("%Y-%m-%d %H:%M"))
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	ws.write_merge(1,count,8,8,now)
	if examres:
		for i in range(0,count1):
			ws.write_merge(i+1,i+1,9,9,examres[i].rname)
			ws.write_merge(i+1,i+1,10,10,examres[i].insname)


	ws1 = w.add_sheet('成绩统计',style0)#------------------------------------------------团队成绩统计tab页
	ws1.col(2).width = 8000
	ws1.col(3).width = 4000
	ws1.col(4).width = 4000
	ws1.write_merge(0,0,0,0,"团队名称",style0)
	ws1.write_merge(0,0,1,1,"团队队长",style0)
	ws1.write_merge(0,0,2,2,"团队成员[姓名（学号）]",style0)
	ws1.write_merge(0,0,3,3,"基础题得分",style0)
	ws1.write_merge(0,0,4,4,"简答题得分",style0)
	ws1.write_merge(0,0,5,5,"技能题得分",style0)
	ws1.write_merge(0,0,6,6,"渗透题得分",style0)

	ws1.write_merge(0,0,7,7,"总得分",style0)

	groupresultS={}
	
	grototalinfo={}
	for i in range(0,examgroups.count()):
		groinfo={}
		choscore=0
		skillscore=0
		infilscore=0
		askscore=0
		groupresult = {}
		group=examGetGroups(examgroups[i].groupID.id)
		groinfo['gname']=group[0]["gname"]
		groinfo['gcaptain']=group[0]["captain"]
		groinfo['gronum_name']=group[0]["gronum_name"]

		answers = answerinfo.filter(Q(groupid=group[0]["id"]) )
		lasttime = None


		if answers:
			for ans in answers:
				anslist={}

				if not lasttime:
					lasttime = ans.extime

				if ans.is_correct == True:
					last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
					ex = ans.extime.strftime("%Y-%m-%d %H:%M:%S")
					if (cmp(last,ex)<=0):
						lasttime = ans.extime
					if ans.is_correct == True:
						sco=ans.queid.qscore.split(',')
						if ans.queid.qtype=='1' :
							choscore+=int(sco[ans.keyid-1])
						elif ans.queid.qtype=='2':
							skillscore+=int(sco[ans.keyid-1])
						elif ans.queid.qtype=='3':
							infilscore+=int(sco[ans.keyid-1])
						elif ans.queid.qtype=='4':
							if ans.askActualGrade:
								askscore+=int(ans.askActualGrade)
				if ans.queid.qtype=='3':
					anslist[int(ans.keyid)]=ans.answer.encode('utf-8')
					if ans.queid_id in groupresult:
						groupresult[ans.queid_id][int(ans.keyid)]=ans.answer.encode('utf-8')
					else:
						groupresult[ans.queid_id]	= anslist
				else:
					groupresult[ans.queid_id] = ans.answer
			groupresultS[examgroups[i].groupID.gname] = groupresult
		else:
			lasttime=datetime.datetime.now()
		groinfo['choscore']=choscore
		groinfo['skillscore']=skillscore
		groinfo['infilscore']=infilscore

		groinfo['askscore']=askscore

		groinfo['totalgrade']=choscore+skillscore+infilscore+askscore

		groinfo['lasttime']=lasttime.strftime("%Y-%m-%d %H:%M:%S")
		grototalinfo[examgroups[i].groupID.gname] = groinfo

	#排名完毕再填写excel表格	
	data_time = OrderedDict(sorted(grototalinfo.items(), key=lambda t:t[1]['lasttime'], reverse=False))
	data_total = OrderedDict(sorted(data_time.items(), key=lambda t:t[1]['totalgrade'], reverse=True))
	
	i=0
	for key in data_total:
		ws1.write_merge(i+1,i+1,0,0,data_total[key]['gname'])
		ws1.write_merge(i+1,i+1,1,1,data_total[key]["gcaptain"])
		ws1.write_merge(i+1,i+1,2,2,data_total[key]["gronum_name"])
		ws1.write_merge(i+1,i+1,3,3,data_total[key]["choscore"])
		ws1.write_merge(i+1,i+1,4,4,data_total[key]["askscore"])
		ws1.write_merge(i+1,i+1,5,5,data_total[key]["skillscore"])
		ws1.write_merge(i+1,i+1,6,6,data_total[key]["infilscore"])

		ws1.write_merge(i+1,i+1,7,7,data_total[key]["totalgrade"])
		i +=1

	#################################################
	row = 2

	ws2 = w.add_sheet('详细信息',style0)#------------------------------------------------详细信息tab页
	ws2.write_merge(0,0,0,0,"题目编号",style0)
	ws2.write_merge(0,0,1,1,"题目标题",style0)
	ws2.write_merge(0,0,2,2,"题目内容/题目地址",style0)
	ws2.write_merge(0,0,3,3,"题目内容插图",style0)

	ws2.write_merge(0,0,4,4,"题目选项",style0)
	ws2.write_merge(0,0,5,5,"标准答案",style0)

	gg=0
	for g in groupresultS:
		ws2.write_merge(0,0,6+gg,6+gg,"团队%s对应答案:" % str(g.encode('utf-8')),style0)
		gg+=1
	paper_questions = PaperQuestion.objects.filter(paperid=exam.examPaperID).order_by('id')
	questions = {}
	questions['choiceQuestionIds'] = [question.questionid_id for question in paper_questions if question.questionid.qtype == '1']
	questions['askQuestionIds'] = [question.questionid_id for question in paper_questions if question.questionid.qtype == '4']

	questions['skillQuestionIds'] = [question.questionid_id for question in paper_questions if question.questionid.qtype == '2']
	questions['infiltrationQuestionIds'] = [question.questionid_id for question in paper_questions if question.questionid.qtype == '3']
	clen =  len(questions['choiceQuestionIds'])

	pattern = xlwt.Pattern()
	pattern.pattern = xlwt.Pattern.SOLID_PATTERN
	pattern.pattern_fore_colour = 5
	style1 = xlwt.XFStyle() # Create the Pattern
	style1.pattern = pattern
	ws2.write_merge(1,1,0,5+len(groupresultS),"基础题",style1)

	font2 = xlwt.Font()
	font2.colour_index = 4
	style2 = xlwt.XFStyle()
	style2.font = font2
	for i in range(0,clen):
		qcho=Choose.objects.get(queid_id=questions['choiceQuestionIds'][i])#选择题题目
		options = Option.objects.order_by('id').filter(choid_id=qcho.id)
		ws2.write_merge(row,row+options.count()-1,0,0,qcho.queid.qid)
		ws2.write_merge(row,row+options.count()-1,1,1,qcho.queid.qtitle)

		ws2.write_merge(row,row+options.count()-1,2,2,qcho.content)
		picdir = qcho.picturedir
		if picdir:#如果有图片。将图片以连接的形式填写单元格，并且将图片复制到文件夹下
			d = picdir.split('/')[2]
			link = 'HYPERLINK("%s";"%s")' % (d,d)
			ws2.write_merge(row,row+options.count()-1,3,3,xlwt.Formula(link),style2)
			cmd = "cp "+os.path.join(HERE,picdir)+ ' '+xlspath
			os.system(cmd)
		else:
			ws2.write_merge(row,row+options.count()-1,3,3,'----')


		for j in range(0,options.count()):
			ws2.write_merge(row+j,row+j,4,4, chr(65 + j) + ": " + options[j].content)
			ws2.write_merge(row+j,row+j,5,5, '正确' if int(options[j].isresult) else '错误')
		j=0
		for g in groupresultS:
			if questions['choiceQuestionIds'][i] in groupresultS[g]:
				res = ""
				for x in groupresultS[g][questions['choiceQuestionIds'][i]]:
					res += chr(65 + int(x))
				ws2.write_merge(row,row+options.count()-1,6+j,6+j, res)
			else:
				ws2.write_merge(row,row+options.count()-1,6+j,6+j,'----')
			j+=1
		row+= options.count()

	ws2.write_merge(row,row,0,5+len(groupresultS),'简答题',style1)
	row +=1
	for i in range(0,len(questions['askQuestionIds'])):
		ask = Ask.objects.get(queid=questions['askQuestionIds'][i])
		ws2.write_merge(row+i,row+i,0,0,ask.queid.qid)
		ws2.write_merge(row+i,row+i,1,1,ask.queid.qtitle)

		ws2.write_merge(row+i,row+i,2,2,ask.content)
		picdir = ask.contentpic
		if picdir:
			d = picdir.split('/')[2]
			link = 'HYPERLINK("%s";"%s")' % (d,d)
			ws2.write_merge(row+i,row+i,3,3,xlwt.Formula(link),style2)

			cmd = "cp "+os.path.join(HERE,ask.contentpic)+ ' '+xlspath
			os.system(cmd)
		else:
			ws2.write_merge(row+i,row+i,3,3,'----')


		ws2.write_merge(row+i,row+i,4,4,'----')
		ws2.write_merge(row+i,row+i,5,5,ask.result)

		j=0
		for g in groupresultS:#{以团队id为key：{题目id为key:答案为值的字典}}
			if questions['askQuestionIds'][i] in groupresultS[g]:
				ws2.write_merge(row+i,row+i,6+j,6+j,groupresultS[g][questions['askQuestionIds'][i]])
			else:
				ws2.write_merge(row+i,row+i,6+j,6+j,'----')
			j+=1
	row +=len(questions['askQuestionIds'])

	ws2.write_merge(row,row,0,5+len(groupresultS),'技能题',style1)
	row +=1

	for i in range(0,len(questions['skillQuestionIds'])):

		skill = Skill.objects.get(queid=questions['skillQuestionIds'][i])
		ws2.write_merge(row+i,row+i,0,0,skill.queid.qid)
		ws2.write_merge(row+i,row+i,1,1,skill.queid.qtitle)
		ws2.write_merge(row+i,row+i,2,2,skill.link)
		ws2.write_merge(row+i,row+i,3,3,'----')
		ws2.write_merge(row+i,row+i,4,4,'----')
		ws2.write_merge(row+i,row+i,5,5,skill.result)

		j=0
		for g in groupresultS:
			if questions['skillQuestionIds'][i] in groupresultS[g]:
				ws2.write_merge(row+i,row+i,6+j,6+j,groupresultS[g][questions['skillQuestionIds'][i]])
			else:
				ws2.write_merge(row+i,row+i,6+j,6+j,'----')
			j+=1
	row +=len(questions['skillQuestionIds'])
	ws2.write_merge(row,row,0,5+len(groupresultS),'渗透题',style1)
	row +=1
	for i in range(0,len(questions['infiltrationQuestionIds'])):
		infil = Infiltration.objects.get(queid=questions['infiltrationQuestionIds'][i])

		ws2.write_merge(row+i,row+i,0,0,infil.queid.qid)
		ws2.write_merge(row+i,row+i,1,1,infil.queid.qtitle)
		ws2.write_merge(row+i,row+i,2,2,infil.link)
		ws2.write_merge(row+i,row+i,3,3,'----')
		ws2.write_merge(row+i,row+i,4,4,'----')

		ws2.write_merge(row+i,row+i,5,5,infil.result)
		j=0

		for g in groupresultS:
			if questions['infiltrationQuestionIds'][i] in groupresultS[g]:
				ws2.write_merge(row+i,row+i,6+j,6+j,str(groupresultS[g][questions['infiltrationQuestionIds'][i]]))
			else:
				ws2.write_merge(row+i,row+i,6+j,6+j,'----')
			j+=1
	xlsname=dirname+".xls"
	w.save(xlsname)
	command= "mv "+xlsname+" "+xlspath
	os.system(command)
	xlszip = xlspath+'.zip'
	zip_dir(xlspath, xlszip)#打包

	c = 'rm -rf '+ xlspath
	os.system(c)

	zipname = dirname+'.zip'
	return zipname
#打包
def zip_dir(path,zipfilename):

    if not os.path.isdir(path):
        exit()

    if os.path.exists(zipfilename):
        os.remove(zipfilename)

    zipfp = zipfile.ZipFile(zipfilename, 'w' ,zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(path, True):
        for filaname in filenames:
            direactory = os.path.join(dirpath,filaname)
            
            #解决在windows下压缩包里面中文乱码问题
            direactory = direactory.decode("utf8")
            zipfp.write(direactory,basename(direactory))
    zipfp.close()
    return zipfilename

# *******************************************下面是竞赛简答题评分*********************************************

def askActualGrade(request, examid):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
		examid=int(examid)
	# askans=[]
	# if Examinations.objects.get(id=examid).examStatus != 0:
	# 	ans = AnswerInfo.objects.filter(examid=examid,anstype=1,askActualGrade=None).order_by('-id')
	# 	for a in ans:
	# 		if a.queid.qtype=='4':
	# 			askans.append(a)
	return render_to_response('templates/askActualGrade.html',{'examid':examid,},context_instance=RequestContext(request))
def timegrade(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	examid=int(request.POST['idhide'])
	askans=[]
	if Examinations.objects.get(id=examid).examStatus != 0:
		ans = AnswerInfo.objects.filter(examid=examid,anstype=1,askActualGrade=None).order_by('-id')
		for a in ans:
			if a.queid.qtype=='4':
				askans.append([a.id,a.groupid.gname,a.extime.strftime("%Y-%m-%d %H:%M:%S")])

	datas={
		'askans':askans,
	}
	return HttpResponse(json.dumps(datas))

def getAnsInfo(request,ansid):
	if request.method == "POST":
		try:
			ansid = int(ansid)
		except:
			pass
		ansinfo = AnswerInfo.objects.get(id=ansid)
		ask = Ask.objects.get(queid_id=ansinfo.queid.id)
		datas = {
			"content": ask.content,
			"result": ask.result,
			'score':ansinfo.queid.qscore,
			"stuanswer": ansinfo.answer,
		}
		return HttpResponse(json.dumps(datas))

def givemark(request,aid):
	if request.method == "POST":
		datas={}
		aid = int(aid)
		mark = request.POST['mark']

		ans = AnswerInfo.objects.get(id=aid)
		if ans.askActualGrade:
			datas['issave'] = 'false'
		else:
			ans.askActualGrade = mark
			ans.save()

			datas['issave'] = 'true'
		return HttpResponse(json.dumps(datas))

# *******************************************下面是竞赛展现*********************************************
def examination_show(request, examid):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')

	if Examinations.objects.get(id=examid).examStatus not in (2, 3):
		raise Http404
	else:
		exam = {}
		exam["no"] = Examinations.objects.get(id=examid).examNo
		exam["name"] = Examinations.objects.get(id=examid).examName
		return render_to_response("templates/examinationshow.html", {"exam": exam})

# 获取指定竞赛的详细信息
def get_exam_info(request):
	if request.method == "POST":
		examNo = request.POST["examNo"]  # 获取竞赛编号
		# 根据竞赛编号获取竞赛开始时间
		# 获取创建竞赛时设置的时长，计算竞赛理论结束时间
		# 获取竞赛使用试卷的总分值
		# 基础题、技能题和渗透题的分值和题数
		examStartTime, examEndTime, paperTotalScore, paperInfo = get_exam_time(examNo)

		# 获取服务器当前时间
		serverNowTime = time.time()
		# 从竞赛开始到当前时间的数据记录
		oldDatas = get_datas_record(examNo, examStartTime)
		# 所有团队基础题，技能题，渗透题得分
		# 各个团队基础题，技能题和渗透题的正确错误题数
		scoreDetails, answerInfo = get_scoreDetails_answerInfo(examNo)

		datas = {
			"startTime": examStartTime,
			"endTime": examEndTime,
			"totalScore": paperTotalScore,
			"paperInfo": paperInfo,
			"nowTime": serverNowTime,
			"datas": oldDatas,
			"scoreDetails": scoreDetails,
			"answerInfo": answerInfo
		}
		return HttpResponse(json.dumps(datas))


# 获取竞赛开始时间
def get_exam_time(no):
	exam = Examinations.objects.get(examNo = no)
	# 获取竞赛开始时间，并转化为字符串
	startTime = exam.examEditTime.strftime("%Y-%m-%d %X")
	# 根据创建竞赛时设置的时间，计算竞赛时长
	timelength_days = (exam.examEndTime - exam.examStartTime).days
	timelength_seconds = (exam.examEndTime - exam.examStartTime).seconds
	endTime = exam.examEditTime + datetime.timedelta(days=timelength_days, seconds=timelength_seconds)
	endTime = endTime.strftime("%Y-%m-%d %X")

	# 获取竞赛使用试卷的信息
	# 获取试卷总分
	totalScore = exam.examPaperID.score
	# 获取基础题，技能题和渗透题信息
	paperinfo = get_paper_info(exam.examPaperID.paperquestion_set.all())

	return (startTime, endTime, totalScore, paperinfo)


# 根据试卷id，查询基础题、技能题和渗透题
def get_paper_info(paperQuestions):
	basalCount, skillCount, advancedCount, askCount = 0, 0, 0, 0
	basalScore, skillScore, advancedScore, askScore = 0, 0, 0, 0

	for q in paperQuestions:
		qt = int(q.questionid.qtype)  # 获取题目的类型，1：基础题，2：技能题，3：渗透题
		scores = score_str_to_intList(q.questionid.qscore)  # 题目的分数列表
		total = 0
		for s in scores:
			total += s

		if qt == 1:
			basalCount += len(scores)
			basalScore += total
		elif qt == 2:
			skillCount += len(scores)
			skillScore += total
		elif qt == 3:
			advancedCount += len(scores)
			advancedScore += total
		elif qt == 4:
			askCount += len(scores)
			askScore += total

	return {
		"basal": {"count": basalCount, "score": basalScore},
		"skill": {"count": skillCount,"score": skillScore},
		"advanced": {"count": advancedCount,"score": advancedScore},
		"ask": {"count": askCount, "score": askScore}
	}


# 由分数字符串返回分数列表
def score_str_to_intList(scoreStr):
	scores = scoreStr.split(',')
	for i in range(0,len(scores)):
		scores[i] = int(scores[i])
	return scores


# 获取从竞赛开始到当前时间的数据记录
def get_datas_record(no, startTime):
	# 获取竞赛的id
	exam = Examinations.objects.get(examNo=no)
	# 根据id获取参加该竞赛的所有团队id和团队name
	examgroups = exam.examgroup_set.all()
	group_id_name = []  # 将参加该竞赛所有团队的id和name保存在列表中
	for examgroup in examgroups:
		group_id_name.append([examgroup.groupID.id, examgroup.groupID.gname])

	# 创建olddatas
	olddatas = {}
	for g in group_id_name:
		olddatas[g[1]] = {"times": [startTime], "values": [0], "lastTime": ""}

	# 获取指定竞赛的所有记录
	examRecords = AnswerInfo.objects.filter(anstype=1).filter(examid=exam.id)
	# 依次获取每个团队的记录
	for group in group_id_name:
		# 按时间从小到大进行排序
		groupRecord = examRecords.filter(groupid=group[0]).order_by("extime")
		# 计算每个时刻的总分
		d = clc_score(groupRecord)
		olddatas[group[1]]["times"].extend(d["times"])
		olddatas[group[1]]["values"].extend(d["values"])
		olddatas[group[1]]["lastTime"] = d["lastTime"]

	return olddatas


# 计算各个时刻的总分
# 1.检查提交的题目是否正确，如果不正确，为0分，如果正确，那么进行第2步
# 2.根据题目的id，查询该题目的分数
def clc_score(record):
	s = 0  # 记录总分
	d = {"times": [], "values": [], "lastTime": ""}  # 记录每个时刻，以及各时刻的总分，最后一次提交正确答案的时间
	lt = ""  # 最后一次提交正确答案的时间默认为空，避免没有记录或所有题错误造成的问题
	for r in record:  # 遍历所有记录
		# 检查该条记录的is_correct，为False表示错误
		if not r.is_correct:
			s += 0
		else:
			t = int(r.queid.qtype)
			if t == 4:
				if r.askActualGrade:
					s += r.askActualGrade
					lt = r.extime.strftime("%Y-%m-%d %X")  # 将时间转化为字符串
			else:
				# 获取题目的分数列表，该题目可能由多个小题组成
				sList = score_str_to_intList(r.queid.qscore)
				s += sList[r.keyid-1]
				lt = r.extime.strftime("%Y-%m-%d %X")  # 将时间转化为字符串
		# 保存数据到d
		d["times"].append(r.extime.strftime("%Y-%m-%d %X"))  # 保存提交答案的时间
		d["values"].append(s)  # 保存对应时间的总分
		d["lastTime"] = lt

	return d


# 统计所有团队基础题，技能题，渗透题得分
# 和各个团队基础题，技能题和渗透题的正确错误题数
def get_scoreDetails_answerInfo(no):
	# 获取竞赛的id
	exam = Examinations.objects.get(examNo=no)
	# 根据id获取参加该竞赛的所有团队id和团队name
	examgroups = exam.examgroup_set.all()
	group_id_name = []  # 将参加该竞赛所有团队的id和name保存在列表中
	for examgroup in examgroups:
		group_id_name.append([examgroup.groupID.id, examgroup.groupID.gname])

	scoreDetails = {}
	answerInfo = {}

	# 获取指定竞赛的所有记录
	examRecords = AnswerInfo.objects.filter(anstype=1).filter(examid=exam.id)
	# 依次获取每个团队的记录
	for group in group_id_name:
		groupRecord = examRecords.filter(groupid=group[0])
		d = clc_details_info(groupRecord)
		scoreDetails[group[1]] = d[0]
		answerInfo[group[1]] = d[1]

	return (scoreDetails, answerInfo)


# 计算每个团队的分数详情和答题信息
def clc_details_info(record):
	basalScore, skillScore, advancedScore, askScore = 0, 0, 0, 0
	basalCorrect, skillCorrect, advancedCorrect = 0, 0, 0
	basalError = 0

	for r in record:
		# 首先获取该记录所答题目的类型和分值
		t = int(r.queid.qtype)  # 题目类型，基础题，技能题，渗透题
		scores = score_str_to_intList(r.queid.qscore)  # 题目的分数列表
		s = scores[r.keyid - 1]  # 获取指定小题的分数

		if t == 1:  # 基础题
			if not r.is_correct:  # 错误
				basalError += 1
			else:
				basalScore += s
				basalCorrect += 1
		elif t == 2:  # 技能题，只能提交正确答案
			skillScore += s
			skillCorrect += 1
		elif t == 3:  # 渗透题，只能提交正确答案
			advancedScore += s
			advancedCorrect += 1
		elif t == 4:
			if r.askActualGrade:
				askScore += r.askActualGrade
	# 返回一个列表，第一个元素为分数详情列表，第二个元素为答题情况字典
	return [
		[basalScore, skillScore, advancedScore, askScore],
		{
			"basal": {"correct": basalCorrect, "error": basalError},
			"skill": {"correct": skillCorrect},
			"advanced": {"correct": advancedCorrect},
			"ask": {"correct": askScore}
		}
	]


def get_new_datas(request):
	if request.method == "POST":
		no = request.POST["examNo"]
		# 首先检查当前竞赛的状态，2表示在进行中
		if Examinations.objects.get(examNo=no).examStatus not in (2, 3):  # 竞赛没有在进行，给前端返回false
			return HttpResponse(json.dumps(False))
		else:
			serverNowTime = time.time()
			totalScoreDatas = clc_total_score(no)
			scoreDetails, answerInfo = get_scoreDetails_answerInfo(no)

			datas = {
				"nowTime": serverNowTime,
				"datas": totalScoreDatas,
				"scoreDetails": scoreDetails,
				"answerInfo": answerInfo
			}
			return HttpResponse(json.dumps(datas))


def clc_total_score(no):
	# 获取竞赛的id
	exam = Examinations.objects.get(examNo=no)
	# 根据id获取参加该竞赛的所有团队id和团队name
	examgroups = exam.examgroup_set.all()
	group_id_name = []  # 将参加该竞赛所有团队的id和name保存在列表中
	for examgroup in examgroups:
		group_id_name.append([examgroup.groupID.id, examgroup.groupID.gname])
	# 各个团队的总分,以及最后一次提交正确答案的时间
	totalScores = {}
	for g in group_id_name:
		totalScores[g[1]] = {"totalScore":0, "lastTime": ""}

	# 获取指定竞赛的所有记录
	examRecords = AnswerInfo.objects.filter(anstype=1).filter(examid=exam.id)
	# 依次获取每个团队的记录
	for group in group_id_name:
		s = 0  # 记录总分
		lt = ""
		for r in examRecords.filter(groupid=group[0]).order_by("extime"):  # 遍历所有记录
			# 检查该条记录的is_correct，为False表示错误
			if not r.is_correct:
				s += 0
			else:
				t = int(r.queid.qtype)
				if t == 4:
					if r.askActualGrade:
						s += r.askActualGrade
						lt = r.extime.strftime("%Y-%m-%d %X")  # 将时间转化为字符串
				else:
					# 获取题目的分数列表，该题目可能由多个小题组成
					sList = score_str_to_intList(r.queid.qscore)
					s += sList[r.keyid - 1]
					lt = r.extime.strftime("%Y-%m-%d %X")  # lt记录最后一次提交正确答案的时间
		# 保存数据
		totalScores[group[1]]["totalScore"] = s
		totalScores[group[1]]["lastTime"] = lt

	return totalScores
