# -*- coding: UTF-8 -*-
'''
实现的主要功能有返回并显示竞赛答题页面，提交答案，统计分数与排名，试卷预览
'''

import json
import datetime
import sys, os, libvirt, subprocess
from libvirt import libvirtError
from atkdfs.models import *

from django.shortcuts import render_to_response, render
from django.views.decorators.http import require_http_methods, require_GET
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.models import Q
from questions.models import *
from students.models import Student
from groups.models import *
from client.models import *
from courses.models import Course
from outlines.models import Exprelation
from experiments.models import Experiment
from sysmgr.models import *
from vms.models import *
from vgates.models import *
from vswitches.models import *
from examinations.models import *
from papers.models import *
from Tools.models import Tool
from tsssite.server import ConnServer
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT
#from examinations.views import statisticGrade
from collections import OrderedDict
from adminsys.views import add_record

def contest(request):
  if not 'cusername' in request.session:
    return HttpResponseRedirect('/Login/')
  try:
    exam_id = request.GET['exam_id']
    request.session['exam_id'] = exam_id
    content={}
    uname = request.session['cusername']
    content["uname"]=uname
    content["hhdata"]=exam_id

    add_record(request.session["stuno"], operate=u'开始竞赛:'+Examinations.objects.get(id=exam_id).examNo, re=1, type=1)

    return render_to_response('templates/contest.html',content,context_instance=RequestContext(request))
  except: 
    content={}
    uname = request.session['cusername']
    try:    
        content["hhdata"]=request.session['exam_id']
    except:
        print "the page has not exam_id!!!"
    content["uname"]=uname
    add_record(request.session["stuno"], operate=u'开始竞赛:', re=1, type=1)

    return render_to_response('templates/contest.html',content,context_instance=RequestContext(request))
#********5555555555555个选择题
#require_GET
# def load_student_questions(request):
#     temp =""
#     exam_id = request.GET['exam_id']

#     gopid =ExamGroup.objects.filter(examID_id = exam_id)


#     gpid = GroupMembers.objects.filter(studentid_id = request.session["cuserid"])
#     for gp in gpid:
#       for gop in gopid:
#         if gp.groupid_id == gop.groupID_id:
#           temp = gop.groupID_id

#     examination = Examinations.objects.get(id=exam_id)

#     paper_questions = PaperQuestion.objects.filter(paperid=examination.examPaperID).order_by('id')

#     questions = {}
#     answer = {}
#     li = []
#     ops=[]
#     cholist=[]
#     # questions['choiceQuestionIds'] = [question.id for question in paper_questions 
#     #                                     if question.questionid.qtype == '1']
#     choiceQuestionIds= [question.id for question in paper_questions if question.questionid.qtype == '1']

#     for queid in choiceQuestionIds:
#         que = PaperQuestion.objects.get(id=queid)
#         que = Question.objects.get(id=que.questionid_id)
#         ops=[]
#         cho={}

#         if que.qtype == '1':
#             qtinfo = Choose.objects.get(queid_id=que.id)
#             options = Option.objects.order_by('id').filter(choid_id=qtinfo.id)
#             if  options:
#                 for op in options:
#                     ops.append([op.content,op.oid])
#             cho["qid"]= que.id
#             cho["qtype"] = que.qtype
#             cho["content"] = qtinfo.content
#             cho["options"] = ops
#             cho["ans"]=""
#             ansinfo=AnswerInfo.objects.filter(groupid_id=temp, queid_id=que.id,examid=exam_id,anstype=1)
#             if ansinfo:
#                 cho["ans"]=ansinfo[0].answer
#             cholist.append(cho)
#     questions["choiceQuestionIds"]=cholist

#     questions['skillQuestionIds'] = [question.id for question in paper_questions 
#                                         if question.questionid.qtype == '2']

#     questions['infiltrationQuestionIds'] = [question.id for question in paper_questions 
#                                               if question.questionid.qtype == '3']
#     try:
#       ansinfo = AnswerInfo.objects.filter(groupid_id=temp, examid=exam_id,anstype=1)
#     except:
#         print "null"

#     if ansinfo:
#         for awer in ansinfo:
#             for qt in paper_questions:
#                 if qt.questionid_id == awer.queid_id:
#                     li.append(qt.id * 10 + awer.keyid)

#     answer['question'] = li


#     data = {'meta': {'error': False}, 'questions': questions, 'answer':answer,}
#     # print json.dumps(data)
   
#     return HttpResponse(json.dumps(data))    


def previewpapers(request):
    # preview
    # if not 'cusername' in request.session:
    #     return HttpResponseRedirect('/Login/')

    exam_id = request.GET['preview']
    return render_to_response('templates/previewpapers.html',{'exam_id': exam_id}, context_instance=RequestContext(request))


def previewpapers1(request):
    temp =""
    exam_id = request.GET['exam_id']
    paper_questions = PaperQuestion.objects.filter(paperid=exam_id).order_by('id')

    questions = {}
    answer = {}
    li = []
    questions['choiceQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '1']

    questions['askQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '4']

    questions['skillQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '2']

    questions['infiltrationQuestionIds'] = [question.id for question in paper_questions 
                                              if question.questionid.qtype == '3']


    try:
      ansinfo = AnswerInfo.objects.filter(examid=exam_id,anstype=1)
    except:
        pass
        # print "null"

    if ansinfo:
        for awer in ansinfo:
            for qt in paper_questions:
                if qt.questionid_id == awer.queid_id:
                    li.append(qt.id * 10 + awer.keyid)

    answer['question'] = li
    data = {'meta': {'error': False}, 'questions': questions, 'answer':answer,}

    return HttpResponse(json.dumps(data))    

def load_student_questions(request):
    temp =""
    exam_id = request.GET['exam_id']

    gopid =ExamGroup.objects.filter(examID_id = exam_id)


    gpid = GroupMembers.objects.filter(studentid_id = request.session["cuserid"])
    for gp in gpid:
      for gop in gopid:
        if gp.groupid_id == gop.groupID_id:
          temp = gop.groupID_id

    examination = Examinations.objects.get(id=exam_id)

    paper_questions = PaperQuestion.objects.filter(paperid=examination.examPaperID).order_by('id')

    questions = {}
    answer = {}
    li = []
    questions['choiceQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '1']

    questions['askQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '4']

    questions['skillQuestionIds'] = [question.id for question in paper_questions 
                                        if question.questionid.qtype == '2']

    questions['infiltrationQuestionIds'] = [question.id for question in paper_questions 
                                              if question.questionid.qtype == '3']


    try:
      ansinfo = AnswerInfo.objects.filter(groupid_id=temp, examid=exam_id,anstype=1)
    except:
        pass
        # print "null"

    if ansinfo:
        for awer in ansinfo:
            for qt in paper_questions:
                if qt.questionid_id == awer.queid_id:
                    li.append(qt.id * 10 + awer.keyid)

    answer['question'] = li


    data = {'meta': {'error': False}, 'questions': questions, 'answer':answer,}
   
    return HttpResponse(json.dumps(data))    

def loadflags(request):
    data = {}
    answers = []
    try:
        ansinfo = AnswerInfo.objects.filter(examid=request.session["hack_id"],anstype=2)
    except:
        print "null"
    for ans in ansinfo:
        answers.append([ans.keyid,ans.queid_id])
    data["datas"] = answers
    return HttpResponse(json.dumps(data)) 

def groupinfo(request):
    if not 'cusername' in request.session:
        return HttpResponseRedirect('/Login/')
    errors=[]
    uname = request.session['cusername']
    return render_to_response('templates/groupinfo.html',{'errors': errors, 'uname':uname}, context_instance=RequestContext(request))

def downresource(request):
    # if request.session['userroletype']==0:
    #   return HttpResponseRedirect('/Login/')
    #获取所有信息
    tools = Tool.objects.order_by('-id')
    #翻页参数设置
    toolselect=''
    if 'querytext' in request.GET and request.GET['querytext']:
        querytext = request.GET['querytext']
        #筛选匹配的字段
        tools=tools.filter(Q(toolname__icontains=querytext)|Q(toolmessage__icontains=querytext))
        toolselect=querytext
    if 'toolselected' in request.GET:
        tools= Tool.objects.order_by('-id')
        querytext = request.GET.get("toolselected")
        tools=tools.filter(Q(toolname__icontains=querytext)|Q(toolmessage__icontains=querytext))
        toolselect=querytext
    after_range_num=5
    befor_range_num=4
    try:
        page = int(request.GET.get("page",1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    paginator = Paginator(tools,10)
    try:
        t_list = paginator.page(page)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        t_list = paginator.page(paginator.num_pages)
    if page >= after_range_num:
        page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
    else:
        page_range = paginator.page_range[0:int(page)+befor_range_num]

    return render_to_response('templates/downresource.html',{'toolselect':toolselect,'tool_list':t_list,'tools':tools,'page_range':page_range},context_instance=RequestContext(request))

# 统计每队的各项总分
def statisticGrade(examid):
    grosGrade={}#{"groname":{"choscore":--,"skillscore":--}}
    examgroups = ExamGroup.objects.filter(examID=examid)
    answerinfo = AnswerInfo.objects.filter(Q(examid=examid) & Q(anstype = 1))
    for gro in examgroups:
        grograde={}
        answerinfos = answerinfo.filter(Q(groupid=gro.groupID_id))
        choscore,askscore,skillscore,infilscore,lasttime = getScoreByGroid(answerinfos)
        grograde["choscore"] = choscore
        grograde["askscore"] = askscore
        grograde["skillscore"] = skillscore
        grograde["infilscore"] = infilscore
        grograde["total"] = choscore + askscore + skillscore + infilscore
        grograde["lasttime"] = lasttime

        grosGrade[gro.groupID.gname] = grograde

    return grosGrade
def getGrade(hackid):

    grosGrade={}#{"groname":{"total":--}}
    hackgroups = AtkdfsGroup.objects.filter(atkdfsID_id=hackid)

    answerinfo = AnswerInfo.objects.filter(Q(examid=hackid) & Q(anstype = 2))

    for gro in hackgroups:
        grograde={}
        total,lasttime = getscores(gro.groupID_id)
        grograde["total"] = total
        grograde["lasttime"] = lasttime

        grosGrade[gro.groupID.gname] = grograde

    return grosGrade

# 计算各种题型分数    
def getScoreByGroid(answerinfo):
    choscore=0
    askscore=0
    skillscore=0
    infilscore=0
    lasttime=None
    # import pdb
    # pdb.set_trace()
    if answerinfo:
        for ans in answerinfo:
            if ans.is_correct == True:
                if not lasttime:
                    lasttime = ans.extime
                last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
                ex = ans.extime.strftime("%Y-%m-%d %H:%M:%S")

                if (cmp(last,ex)<=0):
                    lasttime = ans.extime
                if ans.queid.qtype=='1' :
                    choscore+=int(ans.queid.qscore)
                elif ans.queid.qtype=='2':
                    skillscore+=int(ans.queid.qscore)
                elif ans.queid.qtype=='3':
                    # 获取成绩列表
                    slist = ans.queid.qscore.split(',')
                    infilscore+=int(slist[ans.keyid-1])
                elif ans.queid.qtype=='4':
                    if ans.askActualGrade!=None:
                        if ans.askActualGrade!='':
                            askscore+=int(ans.askActualGrade)    
            else:
                if not lasttime:
                    lasttime = ans.extime
                last = lasttime.strftime("%Y-%m-%d %H:%M:%S")
                ex = ans.extime.strftime("%Y-%m-%d %H:%M:%S")

                if (cmp(last,ex)<=0):
                    lasttime = ans.extime
                if ans.queid.qtype=='1' :
                    choscore+=0
                elif ans.queid.qtype=='2':
                    skillscore+=0
                elif ans.queid.qtype=='3':
                    infilscore+=0
                elif ans.queid.qtype=='4':
                    if ans.askActualGrade!='':
                        askscore+=0    
    else:
        lasttime =datetime.datetime.now()
    return choscore,askscore,skillscore,infilscore,lasttime.strftime("%Y-%m-%d %H:%M:%S")
    
def teaminfo(request):
    exam_id = request.session['exam_id']
    data = statisticGrade(exam_id)
    data = OrderedDict(sorted(data.items(), key=lambda t:t[1]['lasttime'], reverse=False))
    data1 = OrderedDict(sorted(data.items(), key=lambda t:t[1]['total'], reverse=True))

    dic = {}
    arry = []
    for key in data1:
        item = {}
        item[key] = data1[key]
        arry.append(item)
    dic["arry"] = arry
    return HttpResponse(json.dumps(dic))

def getteaminfo(request):
    data={}
    groupid = ""
    members = []
    groupids = ExamGroup.objects.filter(examID_id=request.session['exam_id'])
    groups = GroupMembers.objects.filter(studentid_id=request.session['cuserid'])
    for i in groups:
        for j in groupids:
            if j.groupID_id == i.groupid_id:
                groupid = j.groupID_id
    gname = Group.objects.get(id=groupid)

    num = GroupMembers.objects.filter(groupid_id=groupid)
    for k in num:
        if k.iscaptain == True:
            captain = Student.objects.get(id=k.studentid_id)
            data["captain"] = captain.stuname
        stuname = Student.objects.get(id=k.studentid_id)
        members.append(stuname.stuname)

    grades = statisticGrade(request.session['exam_id'])

    scoreall = OrderedDict(sorted(grades.items(), key=lambda t:t[1]['lasttime'], reverse=False))
    scoreall = OrderedDict(sorted(scoreall.items(), key=lambda t:t[1]['total'], reverse=True))
    arry = []
    for key in scoreall:
        item = {}
        item[key] = scoreall[key]
        arry.append(item)
    data["groupname"] = gname.gname
    data["members"] = members
    data["grades"] = grades[gname.gname]
    data["scoreall"] = arry
    return HttpResponse(json.dumps(data))

#计算总分以及最后提交最后一个正确题目的时间
def getscores(gro_id):
    scores = 0
    #获取团队得分
    lasttime = None
    #获取本团队都答对了哪些题目
    gr_an_qus = AnswerInfo.objects.filter(Q(groupid_id=gro_id) & Q(anstype=2))
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

def teamrank(request):

    hack_id = request.session['hack_id']
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
    # print json.dumps(dic)
    return HttpResponse(json.dumps(dic))    
#对抗模块获取团队信息
def getteamess(request):
    scores = 0
    data={}
    groupid = []
    members = []
    groupids = AtkdfsGroup.objects.filter(atkdfsID_id=request.session['hack_id'])
    groups = GroupMembers.objects.filter(studentid_id=request.session['cuserid'])
    #获取唯一的参加对抗的团队ID
    for gr in groupids:
        for gs in groups:
            if gr.groupID_id == gs.groupid_id:
                gro_id =  gr.groupID_id
                g_name =Group.objects.get(id=gro_id)
                data["groupid"] = gro_id
                data["groupname"] = g_name.gname
    #获取拓扑
    ids = AtkdfsGroup.objects.filter(atkdfsID_id=request.session['hack_id'],groupID_id=gro_id)
    # qeid = ids[0].quesID_id
    # tp = Infiltration.objects.get(queid = ids[0].quesID_id)
    data["topo"] = ids[0].copytopo
    #通过得到的团队ID,得到团队成员以及团队队长
    grmember = GroupMembers.objects.filter(groupid_id=gro_id)
    for g_member in grmember:
        if g_member.iscaptain == True:
            captain = Student.objects.get(id=g_member.studentid_id)
            data["captain"] = captain.stuname
        stuname = Student.objects.get(id=g_member.studentid_id)
        members.append(stuname.stuname)
    scores,lasttime = getscores(gro_id)
    #获取本人控制台的IP

    res = Res.objects.filter(resid = request.session['hack_id'],usebystu_id=request.session['cuserid'])
    if res:
        data["addr"] = res[0].addr
    else:
        data["addr"] = "127.0.0.1"
    data["members"] = members
    data["scores"] = scores
    return HttpResponse(json.dumps(data))

def competorder(request):
    if not 'cusername' in request.session:
        return HttpResponseRedirect('/Login/')
    errors=[]
    uname = request.session['cusername']

    return render_to_response('templates/competorder.html',{'errors': errors, 'uname':uname}, context_instance=RequestContext(request))
def infiltration_question_info(request):
    qscore = PaperQuestion.objects.get(id=request.POST["qid"]).questionid.qscore
    count = len(qscore.split(','))
    return HttpResponse(json.dumps(count))


def get_question_title(request):
    title = PaperQuestion.objects.get(id=request.POST["qid"]).questionid.qtitle
    return HttpResponse(json.dumps(title))
