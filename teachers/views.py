#-*- coding: utf-8 -*- 
# Create your views here.
#教练管理模块功能，主要有增删改查
from django.shortcuts import render_to_response
from teachers.models import Teacher
from students.models import Student
from classes.models import *
from outlines.models import Outline
from groups.models import Group
from papers.models import Paper
from examinations.models import *
from atkdfs.models import *
from courses.models import *
from questions.models import Question
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import json
import logging
from django.db.models import Q
from adminsys.views import add_record

logger = logging.getLogger('mysite.log')
def mgrteacher(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')

        teaselect=''
        currenttea = Teacher.objects.get(id=request.session['userid'])

        if currenttea.roletype ==0:
                teachers= Teacher.objects.filter(id=request.session['userid'])
        else:
                teachers= Teacher.objects.filter(needaudit=0)

        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                teachers=teachers.filter(Q(account__icontains=querytext)|Q(teaname__icontains=querytext))
                teaselect=querytext
        if 'teacherselect' in request.GET:
                teachers= Teacher.objects.filter(needaudit=0)
                querytext = request.GET.get("teacherselect")
                teachers=teachers.filter(Q(account__icontains=querytext)|Q(teaname__icontains=querytext))
                teaselect=querytext
        after_range_num=10
        befor_range_num=4
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(teachers,10)
        try:
                teachers_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                teachers_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                page_range = paginator.page_range[0:int(page)+befor_range_num]
        return render_to_response('templates/teacher.html',{'teaselect':teaselect,'teacherls':teachers_list,'teachers':teachers,'page_range':page_range,'page':page},context_instance=RequestContext(request))

def addteacher(request):
        if request.POST.get('createsadmin',''):
                if request.POST.get('createsadmin','')=='1':
                        createsadmin=1
                else:
                        return HttpResponseRedirect('/Login/')
        else:
                createsadmin=0
                if not 'username' in request.session:
                        return HttpResponseRedirect('/Login/')
        # if request.session['userroletype']==0:
        #         return HttpResponseRedirect('/Login/')
        teachers= Teacher.objects.order_by('-id')
        judgeadd=0
        errors = []
        if request.method == 'POST':
                if not request.POST.get('teaname',''):
                        errors.append('teaname')
                for tea in teachers:
                        if(tea.account==request.POST['account']):
                                judgeadd=1
                                break;
                if(judgeadd==0):
                        if createsadmin==1:
                                tea1 = Teacher(teaname=request.POST['teaname'], account=request.POST['account'], pwd=request.POST['pwd'], roletype=int(request.POST['roletype']),sex=int(request.POST['sex']),email=request.POST['email'],mobile=request.POST['mobile'],otherlink=request.POST['otherlink'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),needaudit=1)
                                tea1.save()
                        else:     
                                tea1 = Teacher(teaname=request.POST['teaname'], account=request.POST['account'], pwd=request.POST['pwd'], roletype=int(request.POST['roletype']),sex=int(request.POST['sex']),email=request.POST['email'],mobile=request.POST['mobile'],otherlink=request.POST['otherlink'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),needaudit=0)
                                tea1.save()
        teachers= Teacher.objects.order_by('-id')
        if createsadmin==1:
                data = {}
                data["result"] = judgeadd
                add_record(request.POST['account'], "管理员注册成功，等待审核。", 1)
                return HttpResponse(json.dumps(data))


        return HttpResponseRedirect('/teachers/')

def editteacher(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        # if request.session['userroletype']==0:
        #         return HttpResponseRedirect('/Login/')
        teachers= Teacher.objects.order_by('-id')
        judgeadd=0
        errors = ''
        try:
                did = int(did)
                tea = Teacher.objects.get(id=did)   
        except ValueError:
                logger.error("teachers")
                raise Http404()                                     
        if request.method == 'POST':
                if not request.POST.get('teaname',''):
                        errors.append('teaname1')
                for teal in teachers:
                        if(teal.account==request.POST['account']):
                                if(teal.account!=tea.account):
                                        judgeadd=1
                                        break;
                if(judgeadd==0):
                        if not request.POST.get('pwd',''):
                                tea.teaname = request.POST['teaname']
                                tea.account = request.POST['account']
                                tea.roletype=int(request.POST['roletype'])
                                tea.sex=int(request.POST['sex'])
                                tea.email=request.POST['email']
                                tea.mobile=request.POST['mobile']
                                tea.otherlink=request.POST['otherlink']
                                tea.edittime=datetime.datetime.now()
                                tea.save()
                        else:
                                tea.teaname = request.POST['teaname']
                                tea.account = request.POST['account']
                                tea.pwd = request.POST['pwd']
                                tea.roletype=int(request.POST['roletype'])
                                tea.sex=int(request.POST['sex'])
                                tea.email=request.POST['email']
                                tea.mobile=request.POST['mobile']
                                tea.otherlink=request.POST['otherlink']
                                tea.edittime=datetime.datetime.now()
                                tea.save()
        request.session["userroletype"] = tea.roletype
        teachers= Teacher.objects.order_by('-id')
        return HttpResponseRedirect('/teachers/')

def delteacher(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        # if request.session['userroletype']==0:
        #         return HttpResponseRedirect('/Login/')
        error = ''
        try:
                teachers = Teacher.objects.order_by('-id')
                outlines = Outline.objects.order_by('-id')
                students = Student.objects.order_by('-id')
                groups = Group.objects.order_by('-id')
                papers = Paper.objects.order_by('-id')
                questions = Question.objects.order_by('-id')
                atkdfs = Atkdfs.objects.order_by('-id')
                examinations = Examinations.objects.order_by('-id')

                did = int(did)
                tea = Teacher.objects.get(id=did)
        except ValueError:
                logger.error("teachers")
                raise Http404()
        if(did != 0): 
                #获取admin的id，更新course表的teacherid和outline表的teacherid
                # adminId = Teacher.objects.get(account = "admin").id
                adminId = Teacher.objects.extra(where=["binary account='admin'"])[0].id
                
                #获取课程表中所有课程创建者id=did的数据
                oldscourse = Course.objects.filter(createrid_id = did)
                for co in oldscourse:
                        co.createrid_id = adminId
                        co.save()

                #获取学生表中创建者Id=did的数据
                oldsStu = Student.objects.filter(createbytea_id = did)
                oldsClass = Class.objects.filter(teacherid_id = did)
                oldsDep = Department.objects.filter(teacherid_id = did)
                for students in oldsStu:
                        students.createbytea_id = adminId
                        students.save()
                for cla in oldsClass:
                        cla.teacherid_id = adminId
                        cla.save()
                for dep in oldsDep:
                        dep.teacherid_id = adminId
                        dep.save()

                #获取大纲表中创建者id=did的数据
                oldsoutline = Outline.objects.filter(teacherid_id = did)
                for outline in oldsoutline:
                        outline.teacherid_id = adminId
                        outline.save()

                #团队
                oldsgroups = Group.objects.filter(createrid_id = did)
                for groups in oldsgroups:
                        groups.createrid_id = adminId
                        groups.save()

                #题目
                oldsquerstions = Question.objects.filter(teacherid_id = did)
                for questions in oldsquerstions:
                        questions.teacherid_id = adminId
                        questions.save()

                #竞赛
                oldsExaminations = Examinations.objects.filter(examCreatorID_id = did)
                for examinations in oldsExaminations:
                        examinations.examCreatorID_id = adminId
                        examinations.save()        

                #组卷
                oldspapers = Paper.objects.filter(creatorid_id = did)
                for papers in oldspapers:
                        papers.creatorid_id = adminId
                        papers.save()

                #攻防
                oldsatkdfs = Atkdfs.objects.filter(atkdfsCreatorID_id = did)
                for atkdfs in oldsatkdfs:
                        atkdfs.atkdfsCreatorID_id = adminId
                        atkdfs.save()
                
                tea.delete()

        # 获取所有课程
        all_course = Course.objects.all()
        # admin = Teacher.objects.get(account = "admin")
        admin = Teacher.objects.extra(where=["binary account='admin'"])[0]
        # 查询每个课程是否都包含有任课教练，如果没有，则指定该课程的任课教练为admin
        for course in all_course:
                data = Courseteacher.objects.filter(courseid_id=course.id)
                if len(data) == 0:  # 该课程没有任课教练
                        ct = Courseteacher(courseid=course, teacherid=admin)
                        ct.save()

        # 获取所有竞赛
        all_exam = Examinations.objects.all()
        for exam in all_exam:
                data = ExamTeacher.objects.filter(examID_id=exam.id)
                if len(data) == 0:
                        et = ExamTeacher(examID=exam, teaID=admin)
                        et.save()

        # 获取所有攻防
        all_atkdfs = Atkdfs.objects.all()
        for atkdfs in all_atkdfs:
                data = AtkdfsTeacher.objects.filter(atkdfsID_id=atkdfs.id)
                if len(data) == 0:
                        at = AtkdfsTeacher(atkdfsID=atkdfs, teaID=admin)
                        at.save()

        teachers = Teacher.objects.order_by('-id')
        return HttpResponseRedirect('/teachers/')


def teacherinfo(request):
        global logger
        tea = ''
        if request.method == 'POST':
                try:
                        teaid = request.POST['teaid']
                        tea = Teacher.objects.get(id=teaid)
                except ValueError:
                        logger.error("teachers")
                        raise Http404()                                
        data = {}
        data["teaid"] = tea.id
        data["teaname"] = tea.teaname
        data["account"] = tea.account
        data["roletype"] = tea.roletype
        data["sex"] = tea.sex
        data["email"] = tea.email
        data["mobile"] = tea.mobile
        data["otherlink"] = tea.otherlink
        return HttpResponse(json.dumps(data))

def teacheraccountcheck(request):
        global logger
        teachers = Teacher.objects.order_by('-id')
        judgeaccount = 0
        if request.method == 'POST':
                try:
                        teaaccount=request.POST['account']
                except ValueError:
                        logger.error("teachers")
                        raise Http404()                                 
                for tea in teachers:
                        if (tea.account.lower() == teaaccount.lower()):
                                judgeaccount=1
                                break
        data={}
        data["judgeaccount"]=judgeaccount
        return HttpResponse(json.dumps(data))


def  roletypecheck(request):
        data={}
        try:
                data["roletype"]=request.session['userroletype']
                data["id"]=request.session['userid']
                data["teaname"]=request.session['username']
                data["useraccount"]=request.session['useraccount']
        except Exception, e:
                data={}
        return HttpResponse(json.dumps(data))

def findTeacherbyExam(request, did):
        global logger
        is_ok = 'false'
        data = {}
        data['cando'] = "true"
        try:
                m_id = int(did)
                #print type(m_id)
                tea = Teacher.objects.get(id=m_id)#要删除的
                if tea.account == "admin":
                        data['cando'] = "false"
        except ValueError:
                logger.error("teachers")
                raise Http404()
        con = tea.examteacher_set.count()
        if con>0:
                is_ok = 'true'
        data["success"] = is_ok 
        return HttpResponse(json.dumps(data))

def findTeacherbyCourse(request, did):
        global logger
        is_ok = 'false'
        try:
                m_id = int(did)
                #print type(m_id)
                tea = Teacher.objects.get(id=m_id)
        except ValueError:
                logger.error("teachers")
                raise Http404()
        con = tea.courseteacher_set.count()
        if con>0:
                is_ok = 'true'
        data = {}
        data["success"] = is_ok 
        return HttpResponse(json.dumps(data))


def registerteacher(request):
        teachers= Teacher.objects.filter(needaudit=1)
        after_range_num=10
        befor_range_num=4
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(teachers,10)
        try:
                teachers_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                teachers_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                page_range = paginator.page_range[0:int(page)+befor_range_num]
        if request.session['userroletype']==0:
                return render_to_response('templates/registeradmin.html',{'page_range':page_range},context_instance=RequestContext(request))
        
        return render_to_response('templates/registeradmin.html',{'teacherls':teachers_list,'teachers':teachers,'page_range':page_range},context_instance=RequestContext(request))


def accetpadmin(request):
        if request.method == 'POST':
                accent=0
                teaid = request.POST['teacherid']
                tea = Teacher.objects.get(id=teaid)
                try:
                        tea.needaudit = 0
                        tea.save()
                except Exception, e:
                        accent=1
                if accent==0:
                        add_record(request.session['useraccount'], u'审核通过，%s：%s' % (u'管理员' if tea.roletype else u'教练员', tea.account), 1)
                        return render_to_response('templates/registeradmin.html')
                else:
                        add_record(request.session['useraccount'], u'审核失败，%s：%s' % (u'管理员' if tea.roletype else u'教练员', tea.account), 0)
                        data = {}
                        data["error"] = 1 
                        return HttpResponse(json.dumps(data))        
    
def canceladmin(request):
        if request.method == 'POST':
                accent=0
                tea = request.POST['teacherid']   
                try:
                        did = int(tea)
                        tea = Teacher.objects.get(id=did)
                except ValueError:
                        accent=1
                tea.delete()
                if accent==0:
                        add_record(request.session['useraccount'], u'审核不通过，%s：%s' % (u'管理员' if tea.roletype else u'教练员', tea.account), 1)
                        return render_to_response('templates/registeradmin.html')
                else:
                        add_record(request.session['useraccount'], u'审核失败，%s：%s' % (u'管理员' if tea.roletype else u'教练员', tea.account), 0)
                        data = {}
                        data["error"] = 1 
                        return HttpResponse(json.dumps(data))  