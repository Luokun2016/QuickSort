#-*- coding: utf-8 -*- 
'''
1. 创建攻防展现界面：调用showstate方法，初始化并返回html页面；
2. 页面加载过程中获取攻防对抗比赛的所有信息：调用getSelectItem方法；
3. 页面加载完成后，每30秒获取一次数据：调用getSelectItem方法；
'''

from django.shortcuts import render_to_response
from students.models import Student
from groups.models import *
from teachers.models import Teacher
from questions.models import *
import time
from papers.models import *
from client.models import *
from groups.models import *
from tsssite.server import *
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT,HERE
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.models import Q
import json
import datetime
import time
from atkdfs.models import *
import sys, os, libvirt, subprocess,commands
from libvirt import libvirtError
from collections import OrderedDict


def showstate(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	names={}
	post_examID=0
	return_group=[]
	range_num=30.0
	if request.method == 'GET':
		try:
			post_examID = request.GET['examIDInfo']
			# 根据对抗ID获取所有团队
			atkdfsGroup = AtkdfsGroup.objects.filter(atkdfsID=post_examID).order_by('-id')
			g_group=Group.objects.all()

			m_count_1 = int(round(range_num/atkdfsGroup.count()))#四舍五入商
			m_count = int(range_num/atkdfsGroup.count())#整除商
			remainder = int(range_num%atkdfsGroup.count())#余数
			# print m_count_1
			# print m_count
			m=0
			n=0
			for i in range(0, int(range_num)+1):
				if m<atkdfsGroup.count():
					if i%m_count_1==0:
						atkg=atkdfsGroup[m]
				 		atkGroup = g_group.filter(Q(id=atkg.groupID_id))
						names[atkg.groupID_id]=atkGroup[0].gname
						atkg.name=atkGroup[0].gname
						return_group.append(atkg)
						m=m+1
					else:
						return_group.append('')
	
			if len(return_group)<int(range_num)+1:
				for i in range(1,int(range_num)+1-len(return_group)):
					return_group.append('')


			# for atkg in atkdfsGroup:
			# 	atkGroup = g_group.filter(Q(id=atkg.groupID_id))
			# 	names[atkg.groupID_id]=atkGroup[0].gname
			# 	atkg.name=atkGroup[0].gname
			# 	return_group.append(atkg)
		except:
			atkdfsGroup=''
			return HttpResponseRedirect('/atkdfs/')


	return render_to_response('templates/showstate.html',
								{'gros':return_group,
								'time':time.strftime('%H:%M:%S',time.localtime(time.time())),
								'names':names,
								'examID':post_examID,
								},
								context_instance=RequestContext(request))



def getSelectItem(request):
	global global_atkdfsGroup #全局变量记录AtkdfsGroup.objects获取信息
	global global_answerInfo #全局变量记录AnswerInfo.objects获取信息
	global global_group #全局变量记录Group.objects获取信息

	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	post_examID = request.POST['examIDInfo']

	#获取所有团队，用于获取团队名称使用
	global_group=Group.objects.all()

	#获取竞赛中的所有团队与分配题目信息
	global_atkdfsGroup = AtkdfsGroup.objects.filter(atkdfsID=post_examID).order_by('-id')	

	#获取当前对抗所有答题信息
	global_answerInfo = AnswerInfo.objects.filter(Q(anstype=2)& Q(examid=post_examID)).order_by('-id')
	
	data = {} #返回信息对象
	groups = []
	#遍历所有在竞赛中的团队
	for atkdfsGroup in global_atkdfsGroup:

		#将当前组的ID赋值给post_groupId
		post_groupId = atkdfsGroup.groupID.id

		#获取当前团队答题信息（统计发起攻击使用）
		m_answerInfo = global_answerInfo.filter(Q(groupid_id=post_groupId))
		
		message = {} 

		# 如果获取攻击信息不为空
		if m_answerInfo:
			# 通过获取不重复的queid_id数据项个数得到攻击团队数
			atkgups=m_answerInfo.filter(examid=post_examID)
			atkgups=atkgups.values('queid_id').distinct() 
			
			atknum=0 # 计算攻击成功次数
			queids=[] #存储攻下题目ID
			qudkeys=[]#存储攻下key
			quenames=[]#存储攻下题目所属团队名称
			groupids=[] #存储攻下团队ID
			for atks in m_answerInfo:
				atknum=atknum+1 #发起攻击次数
				queids.append(atks.queid_id) #攻下题目ID
				qudkeys.append(atks.answer) #攻下题目key
				quenames.append(global_group.filter(Q(id=global_atkdfsGroup.filter(Q(quesID_id=atks.queid_id))[0].groupID_id))[0].gname)

				groupids.append(global_atkdfsGroup.filter(Q(quesID_id=atks.queid_id))[0].groupID_id)
			message["atkgroup_id"]=post_groupId #发起攻击次数
			message["atkgroup_name"]=global_group.filter(Q(id=atkdfsGroup.groupID_id))[0].gname
			message["atknum"]=atknum #发起攻击次数
			message["queid_id"]=queids #攻下题目ID
			message["qud_key"]=qudkeys
			message["que_name"]=quenames
			message["group_id"]=groupids #攻下团队ID

			# print post_groupId #当前团队ID
			# print message["atknum"] 
			# print message["queid_id"] 
			# print message["group_id"] 
			groups.append(message)
			
	data["groups"] = groups		
	# print json.dumps(data)
	return HttpResponse(json.dumps(data))

def warnMsg(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	post_examID = request.POST['examIDInfo']
	data = {}
	# 获取所有AnswerInfo中信息
	m_atkdfsGroup= global_answerInfo.filter(Q(examid=post_examID)).order_by("-extime")
	# 存储被攻击次数最多团队信息
	m_dir={}
	# 存储已经发起攻击团队信息
	m_dir1={}
	m_times=[]
	if len(m_atkdfsGroup)>0:
		for atg in m_atkdfsGroup:
			# 将时间，题目ID，组ID写入返回值中(时间格式不转化不能进行赋值)
			if len(m_times)<10:
				m_atkgup= global_atkdfsGroup.filter(Q(quesID_id=atg.queid_id))	
				atk_group=global_group.filter(Q(id=atg.groupid_id))
				atked_group=global_group.filter(Q(id=m_atkgup[0].groupID_id))
				times={}
				times["m_time"]=str(atg.extime)
				times["m_atked_groupid"]=atked_group[0].gname
				times["m_atk_groupid"]=atk_group[0].gname
				m_times.append(times)
			# 使用字典存储被攻击团队
			if(m_dir.has_key(atg.queid_id)):
				m_dir[atg.queid_id]=m_dir[atg.queid_id]+1
			else:
				m_dir[atg.queid_id] = 1
			# 使用字典存储已经发起攻击团队
			if(m_dir1.has_key(atg.groupid_id)):
				m_dir1[atg.groupid_id]=m_dir1[atg.groupid_id]+1
			else:
				m_dir1[atg.groupid_id] = 1
		# 记录所有有效攻击的时间
		data["m_times"] = m_times
		# 取字典value最大值，作为被攻击次数最多
		max_value= max(m_dir.values())
		# 遍历字典找到团队，并将次数与guoupID保存
		for max_key in m_dir.items():
			if max_key[1] == max_value:
				data["key"]=max_key[0]
				data["value"]=max_key[1]
			
		# 获取字典key的个数，用于表示已经发起攻击团队数
		data["counts"]=len(m_dir1.keys())
		# 根据groupID找到被攻击次数最多团队名
		gros = global_atkdfsGroup.filter(Q(quesID=data["key"])).order_by('-id')
		
		gro=global_group.filter(Q(id=gros[0].groupID_id))
		data["gname"]=gro[0].gname
		quests=[]
		data["out"]=0

		# 每队剩余key个数小于等于1个即为濒临出局
		quest = Infiltration.objects.all()
		for m_key in m_dir.keys():
			quests.append((quest.filter(queid_id=m_key))[0])
		for a in quests:
			# 每队被答对的题数
			m_answered = len(m_atkdfsGroup.filter(queid_id=a.queid_id))
			# 每队总题数
			m_total = len((a.result).split(","))
			if (m_total-m_answered)<1:
				data["out"]=data["out"]+1

	if m_dir1=={}:
		data["counts"]=0
		data["out"]=0
		data["gname"]='--'
	# 实时攻击信息
			
	return HttpResponse(json.dumps(data))

def teamrank(request):
    hack_id = request.POST['examIDInfo']
    data = getGrade(hack_id)
    data = OrderedDict(sorted(data.items(), key=lambda t:t[1]['lasttime'], reverse=False))
    data1 = OrderedDict(sorted(data.items(), key=lambda t:t[1]['total'], reverse=True))
    dic = {}
    arry = []

    for key in data1:
        item = {}
        item[key] = data1[key]
        arry.append(item)
    dic["arry"] = arry
    # print dic
    return HttpResponse(json.dumps(dic))  

def getGrade(hackid):
    grosGrade={}
    hackgroups = global_atkdfsGroup.filter(Q(atkdfsID_id=hackid))
    answerinfo = global_answerInfo.filter(Q(examid=hackid) & Q(anstype = 2))
    for gro in hackgroups:
        grograde={}
        total,lasttime = getscores(gro.groupID_id)
        grograde["total"] = total
        grograde["lasttime"] = lasttime
        grograde["group_id"] = gro.groupID_id
        grosGrade[gro.groupID.gname] = grograde


    return grosGrade     	

def getscores(gro_id):
    scores = 0
    #获取团队得分
    lasttime = None
    #获取本团队都答对了哪些题目
    gr_an_qus = global_answerInfo.filter(Q(groupid_id=gro_id) & Q(anstype=2))
    if gr_an_qus:
        for gr in gr_an_qus:
            #获取question表中的score切分取值
            ques_score = Question.objects.get(id=gr.queid_id)
            list_score = ques_score.qscore.split(',')
            scores += int(list_score[gr.keyid-1])
            #获取最后答题时间
            if not lasttime:
                lasttime = gr.extime
            last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
            ex = gr.extime.strftime("%Y-%m-%d %H:%M:%S")
            if (cmp(last,ex)<=0):
                lasttime = gr.extime
            else:
                if not lasttime:
                    lasttime = an.extime
                last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
                ex = gr.extime.strftime("%Y-%m-%d %H:%M:%S")

                if (cmp(last,ex)<=0):
                    lasttime = gr.extime
    else:
        lasttime =datetime.datetime.now()
    return scores,lasttime.strftime("%Y-%m-%d %H:%M:%S")

def getgroups(request):
	data = {}
	groupname = []
	hack_id = request.POST['examIDInfo']
	#获取参加对抗的团队
	groups = global_atkdfsGroup.filter(Q(atkdfsID_id=hack_id))
	if len(groups) > 0:
		for i in groups:
			name = Group.objects.get(id=i.groupID_id)
			quest = Infiltration.objects.get(queid_id=i.quesID_id)
			groupname.append([name.gname,quest.result,i.quesID_id,quest.link,name.id])#团队名称+key答案+题目ID
	data["groups"] = groupname #参加对抗的团队名称
	return HttpResponse(json.dumps(data))

def getAllgroup(request):
	data = {}
	groups=Group.objects.all()
	for group in groups:
		data[group.id]=group.gname
	return HttpResponse(json.dumps(data))


