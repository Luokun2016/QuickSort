#-*- coding: utf-8 -*- 
'''
实现对试卷的管理功能
包括对试卷的增(手动选题，一键组卷)，删，改，查（试卷详情与预览试卷）的功能
'''

from django.shortcuts import render_to_response
from teachers.models import Teacher
from papers.models import Paper, PaperQuestion
from examinations.models import Examinations
from atkdfs.models import *
from questions.models import Question
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import json
import logging
from django.db.models import Q
import pdb
import string
from adminsys.views import funcando


logger = logging.getLogger('mysite.log')
def managePaper(request):
	#pdb.set_trace()
	#add()
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	#权限判断，如果是教练员就返回到登录页面，暂时没意义
	# if request.session['userroletype']==0:
	# 	return HttpResponseRedirect('/Login/')

	papselect=''
	papers = Paper.objects.order_by('-id')
	#for pap in papers:
	#	print pap.papname
	if 'querytext' in request.GET and request.GET['querytext']:
		querytext = request.GET['querytext']
		papers = papers.filter(Q(papid__icontains=querytext)|Q(papname__icontains=querytext))
		papselect=querytext
	if 'paperselect' in request.GET:
		papers = Paper.objects.order_by('-id')
		querytext = request.GET.get('paperselect')
		papers = papers.filter(Q(papid__icontains=querytext)|Q(papname__icontains=querytext))
		papselect = querytext

	after_range_num = 10
	befor_range_num = 4
	try:
		page = int(request.GET.get("page",1))
		if page < 1:
			page = 1
	except ValueError:
		page = 1
	
	paginator = Paginator(papers,10)
	
	try:
		papers_list = paginator.page(page)
	except(EmptyPage, InvalidPage, PageNotAnInteger):
		papers_list = paginator.page(paginator.num_pages)

	if page >= after_range_num:
		page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
	else:
		page_range = paginator.page_range[0:int(page)+befor_range_num]

	return render_to_response('templates/papers.html',
				{'papselect':papselect,
				'paperls':papers_list,
				'papers':papers,
				'page_range':page_range},
				context_instance=RequestContext(request))

def GetQueType(qtype):
	quetype = ""
	if qtype=="1":
		quetype = "基础题"
	elif qtype == "4":
		quetype = "简答题"	
	elif qtype == "2":
		quetype = "技能题"
	elif qtype == "3":
		quetype = "渗透题"

	return quetype



def GetQuestionInfo(querytext):
	data={}
	ques=[]
	quetype=['all','choose','ask','skill','infiltration']

	questions = Question.objects.order_by('-id')
	
	if querytext == '1' or querytext == '2' or querytext == '3' or querytext == '4':
		questions = questions.filter(qtype=querytext)
	else:
		questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))

	
	for item in questions:
		que={}
		# if item.qtype == querytext:
		que["id"] = item.id
		que["qid"] = item.qid
		que["qtitle"] = item.qtitle
		que["qscore"] = item.qscore
		que["teaname"] = item.teacherid.teaname
		que["qtype"] = item.qtype
		que["edittime"] = item.edittime.strftime("%Y-%m-%d %H:%M")
		ques.append(que)

	data["questions"] = ques
	if querytext == '1'or querytext == '2'or querytext == '3' or querytext == '4':
		data[quetype[int(querytext)]] = len(ques)
	else:
		data[quetype[0]] =len(ques)
	return data

#获取添加考试所需的基础题目，简答题目，技能题目，渗透题目
def GetAddPaperInfo(request):
	#pdb.set_trace()
	datas = {}
	BasicData = GetQuestionInfo('1')
	AskData = GetQuestionInfo('4') 
	SkillData = GetQuestionInfo('2') 
	InfilData = GetQuestionInfo('3') 
	datas["BasicData"] = BasicData
	datas["AskData"] = AskData
	datas["SkillData"] = SkillData
	datas["InfilData"] = InfilData
	return HttpResponse(json.dumps(datas))

def GetPapBaseInfo(request):
	if request.method == 'POST':
		try:
			strQueIds = request.POST.get('Info', '')
		except ValueError:
			raise Http404

	listQueIds = strQueIds.split(',')

	totalCount = 0
	totalScore = 0
	chooseCount = 0
	chooseScore = 0
	askCount = 0
	askScore = 0	
	skillCount = 0
	skillScore = 0
	infiltrationCount = 0
	infiltrationScore = 0
	for qid in listQueIds:
		que = Question.objects.get(id=int(qid))
		if "," in que.qscore:
			score = 0
			infil = que.qscore.split(",")
			for sc in infil:
				score += int(sc)
		else:
			score = int(que.qscore)
		totalCount += 1
		totalScore += score
		if(que.qtype == '1'):
			chooseCount += 1
			chooseScore += score
		elif(que.qtype == '2'):
			askCount += 1
			askScore += score	
		elif(que.qtype == '3'):
			skillCount += 1
			skillScore += score
		else:
			infiltrationCount += 1
			infiltrationScore += score

	data={}
	data["totalCount"] = str(totalCount)
	data["totalScore"] = str(totalScore)
	data["chooseCount"] = str(chooseCount)
	data["chooseScore"] = str(chooseScore)
	data["askCount"] = str(askCount)
	data["askScore"] = str(askScore)	
	data["skillCount"] = str(skillCount)
	data["skillScore"] = str(skillScore)
	data["infiltrationCount"] = str(infiltrationCount)
	data["infiltrationScore"] = str(infiltrationScore)

	return HttpResponse(json.dumps(data))

def selectque(request):
	data={}
	quesid = []
	score = 0
	setnum = "true"
	if request.method == 'POST':
		try:
			strPapInfo = request.POST['Info']
			choose = request.POST['choose']
			ask = request.POST['ask']
			skill = request.POST['skill']
			infil = request.POST['infil']
		except ValueError:
			logger.error("error")
			raise Http404
		ch = Question.objects.filter(qtype=1).order_by('-times')
		sk = Question.objects.filter(qtype=2).order_by('-times')
		inf = Question.objects.filter(qtype=3).order_by('-times')
		ak = Question.objects.filter(qtype=4).order_by('-times')

		if int(choose) <= ch.count():
			chos = 0
			for c in ch:
				if chos < int(choose):
					score += int(c.qscore)
					chos+=1
					quesid.append(c.id)
				else:
					break;
		else:
			setnum = "false"
		if int(ask) <= ak.count():
			chos = 0
			for c in ak:
				if chos < int(ask):
					score += int(c.qscore)
					chos+=1
					quesid.append(c.id)
				else:
					break;
		else:
			setnum = "false"
		if int(skill) <= sk.count():
			
			chos = 0
			for c in sk:
				if chos < int(skill):
					score += int(c.qscore)
					chos+=1
					quesid.append(c.id)
				else:
					break;
		else:
			setnum = "false"
		if int(infil) <= inf.count():
			chos = 0
			for c in inf:
				if chos < int(infil):
					if "," in c.qscore:
						sl = c.qscore.split(",")
						for sc in sl:
							score += int(sc)
					else:
						score += int(c.qscore)
					chos+=1
					quesid.append(c.id)
				else:
					break;
		else:
			setnum = "false"
		# for i in rang(1,int(choose)):
		# 	print i
	data["quesid"] = quesid
	data["score"] =score
	data["setnum"]=setnum

	print json.dumps(data)
	return HttpResponse(json.dumps(data))
def SaveAddPap(request):
	global logger
	#pdb.set_trace()
	if request.method == 'POST':
		try:
			strPapInfo = request.POST['Info']
		except ValueError:
			logger.error("SaveAddPap():get paper info error")
			raise Http404

	jsonPapInfo = json.loads(strPapInfo)

	paper = Paper(papid=jsonPapInfo["papno"],
			papname=jsonPapInfo["papname"],
			remark=jsonPapInfo["remark"],
			score=jsonPapInfo["score"],
			creatorid_id=int(request.session["userid"]),
			frequency=0,
			createtime=datetime.datetime.now(),
			edittime=datetime.datetime.now())
	paper.save()
	papid = paper.id
	for item in jsonPapInfo["queids"]:
		queid = Question.objects.get(id=int(item))
		queid.times+=1
		queid.save()
		PapQue=PaperQuestion(paperid_id=papid, questionid_id=int(item))
		PapQue.save()

	return HttpResponseRedirect("/papers/")

	

#display paper information
def GetPaperInfo(request):
	global logger
	pap = ''
	#pdb.set_trace()
	if request.method == 'POST':
		try:
			papid = request.POST['Info']
			paper = Paper.objects.get(id=papid)
			questions = PaperQuestion.objects.filter(paperid=papid).order_by('-id')
		except ValueError:
			logger.error("get paper info error")
			raise Http404
	data = {}
	data["paperid"] = paper.id
	data["paperno"] = paper.papid
	data["papername"] = paper.papname
	data["creatorid"] = paper.creatorid.teaname
	#data["question"] = pap.question
	data["remark"] = paper.remark
	data["score"] = paper.score
	data["frequency"] = paper.frequency
	data["createtime"] = paper.createtime.strftime("%Y-%m-%d %H:%M")
	data["edittime"] = paper.edittime.strftime("%Y-%m-%d %H:%M")

	ques=[]
	for item in questions:
		que={}
		type=""
		que["id"] = item.questionid.id
		que["qid"] = item.questionid.qid
		que["qtitle"] = item.questionid.qtitle
		que["qscore"] = item.questionid.qscore
		que["teaname"] = item.questionid.teacherid.teaname
		que["qtype"] = item.questionid.qtype
		que["edittime"] = item.questionid.edittime.strftime("%Y-%m-%d %H:%M")
		ques.append(que)
	data["questions"]=ques
	
	#print pap.questionid.qid
	url = request.get_full_path()
	return HttpResponse(json.dumps(data))

def GetEditPaperInfo(request):
	#pdb.set_trace()
	global logger
	data = {}	
	BasicData = GetQuestionInfo('1')
	AskData = GetQuestionInfo('4') 	
	SkillData = GetQuestionInfo('2') 
	InfilData = GetQuestionInfo('3') 
	data["BasicData"] = BasicData
	data["AskData"] = AskData	
	data["SkillData"] = SkillData
	data["InfilData"] = InfilData


	try:
		if request.method == 'POST':
			paperid = int(request.POST['Info'])
			paper = Paper.objects.get(id=paperid)
			questions = PaperQuestion.objects.filter(paperid_id=paperid).order_by('-id')
			pap={}
			pap["paperid"] = paper.id
			pap["paperno"] = paper.papid
			pap["papername"] = paper.papname
			pap["creater"] = paper.creatorid.teaname
			pap["remark"] = paper.remark
			pap["score"] = paper.score
			pap["frequency"] = paper.frequency
			pap["createtime"] = paper.createtime.strftime("%Y-%m-%d %H:%M")
			pap["edittime"] = paper.edittime.strftime("%Y-%m-%d %H:%M")

			ques=[]
			for queid in questions:
				ques.append(queid.questionid_id)
			pap["questions"] = ques
			data["edit"] = pap
	except:
		logger.error("GetEditPaperInfo-error.")
		data["result"]=1
	else:
		data["result"]=0
	finally:
		return HttpResponse(json.dumps(data))


def UpdateEditPap(request):
	#pdb.set_trace()
	global logger
	if request.method == 'POST':
		try:
			editInfo = request.POST['Info']
		except ValueError:
			logger.error("UpdateEditPap::Error")
			raise Http404()
		JsonInfo = json.loads(editInfo)
		papid = int(JsonInfo["papid"])

		paper = Paper.objects.get(id=papid)
		paper.papid = JsonInfo["papno"]
		paper.papname = JsonInfo["papname"]
		paper.remark = JsonInfo["remark"]
		paper.score = int(JsonInfo["score"])
		paper.edittime = datetime.datetime.now()
		paper.save()

		oldPerQues = PaperQuestion.objects.filter(paperid_id=papid)
		for item in oldPerQues:
			item.delete()

		for item in JsonInfo["queids"]:
			PapQue=PaperQuestion(paperid_id=papid, questionid_id=int(item))
			PapQue.save()	
	return HttpResponseRedirect("/papers/")
def Checkuse(request):
	data = {}
	data['cando'] = "true"

	if request.method == 'POST':
		try:
			papid = int(request.POST['Info'])
			paper = Paper.objects.get(id=papid)
		except ValueError:
			logger.error("RemovePap::Error")
			raise Http404


	cando = funcando(request,paper.creatorid)
	if cando == "false":
	            data['cando'] = "false"
	            return HttpResponse(json.dumps(data))
	results = Examinations.objects.filter(examPaperID_id=papid,examStatus=2)
	result = Atkdfs.objects.filter(atkdfsPaperID_id=papid,atkdfsStatus=2)
	
	if results or  result :
		data["results"] = "full"
		return HttpResponse(json.dumps(data))
	else:
		data["results"] = "empty"
		return HttpResponse(json.dumps(data))
def RemovePap(request):
	global logger
	data = {}
	if request.method == 'POST':
		try:
			papid = int(request.POST['Info'])
		except ValueError:
			
			logger.error("RemovePap::Error")
			raise Http404
	#results = Examinations.objects.filter(examPaperID_id=papid)
	
	oldPerQues = PaperQuestion.objects.filter(paperid_id=papid)
	for item in oldPerQues:
		item.delete()

	paper=Paper.objects.get(id=papid)
	paper.delete()	
	return HttpResponseRedirect("/papers/")
	

def checkPapInfo(request):
	global logger
	check = 0
	if request.method == 'POST':
		try:
			papno = request.POST['Info']
		except:
			logget.error("checkPapInfo::Error")
			raise Http404

	paper = Paper.objects.filter(papid=papno)

	check = paper.count()
	#for item in paper:
	#	check += 1

	
	data = {}
	data["check"] = check

	return HttpResponse(json.dumps(data))

def SearchQue(request):
	#pdb.set_trace()
	global logger
	if request.method == 'POST':
		try:
			if 'Info' in request.POST:
				qtext = request.POST.get('Info','')
		except ValueError:
			logger.error(" SearchQue::Error")
			raise Http404

	data =  GetQuestionInfo(qtext)
	return HttpResponse(json.dumps(data))