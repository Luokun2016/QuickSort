# -*- coding: UTF-8 -*-
#团队管理模块增删改查功能
# Create your views here.
from django.shortcuts import render_to_response
from teachers.models import Teacher
from examinations.models import ExamGroup
from students.models import Student
from classes.models import Class,Department
from groups.models import Group,GroupMembers
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import xlrd
import json
import logging
from django.db.models import Q
from adminsys.views import funcando
from examinations.models import *
from atkdfs.models import *

logger = logging.getLogger('mysite.log')
def mgrgroup(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        #权限判断，如果是教练员就返回到登录页面，暂时没意义
        # if request.session['userroletype']==0:
        #         return HttpResponseRedirect('/Login/')
        groselect=''
        groups= Group.objects.order_by('-id')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                groups=groups.filter(Q(gname__icontains=querytext))
                groselect=querytext
        if 'groupselect' in request.GET:
                groups= Group.objects.order_by('-id')
                querytext = request.GET.get("groupselect")
                groups=groups.filter(Q(gname__icontains=querytext))
                groselect=querytext
        after_range_num=10
        befor_range_num=4
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(groups,10)
        try:
                groups_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                groups_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                page_range = paginator.page_range[0:int(page)+befor_range_num]
        gms=GroupMembers.objects.order_by('-id')
        return render_to_response('templates/group.html',{'groselect':groselect,'groupls':groups_list,'groups':groups,'gms':gms,'page_range':page_range},context_instance=RequestContext(request))

def Checkgruse(request):
    data = {}
    data['cando'] = "true"
    data["isexam"] = "0"
    data["names"]=''
    try:
        if request.method == 'POST':
            exams = Examinations.objects.order_by("id")
            atks=Atkdfs.objects.order_by("id")
            gid = request.POST['Info']
            gro = Group.objects.get(id=gid)
            cando = funcando(request,gro.createrid)
            if cando == "false":
                data['cando'] = "false"
                return HttpResponse(json.dumps(data))
            egps = ExamGroup.objects.filter(groupID_id=gid)
            for egp in egps:
                exam=exams.filter(id=egp.examID_id)
                if len(exam)>0:
                    data["isexam"] = "1"
                    data["names"] = exam[0].examName
                    return HttpResponse(json.dumps(data))
            atkgs=AtkdfsGroup.objects.filter(groupID_id=gid)
            for atkg in atkgs:
                atk=atks.filter(id=atkg.atkdfsID_id)
                if len(atk)>0:
                    data["isexam"] = "2"
                    data["names"] =atk[0].atkdfsName
                    return HttpResponse(json.dumps(data))
            return HttpResponse(json.dumps(data))
    except Exception,e:
        data["isexam"] = "3"
        return HttpResponse(json.dumps(data))

def delgroup(request, did):
    global logger
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    #权限判断，如果是教练员就返回到登录页面，暂时没意义
    # if request.session['userroletype']==0:
    #     return HttpResponseRedirect('/Login/')
    error = ''
    try:
        did = int(did)
        gro = Group.objects.get(id=did)
    except ValueError:
        logger.error("groups")
        raise Http404()
    if(did != 0):
        gms=GroupMembers.objects.filter(groupid_id=did)
        for gm in gms:
            gm.delete()
        gro.delete()
    groups = Group.objects.order_by('-id')
    return HttpResponseRedirect('/groups/')

def groupstudenttree(request):
    classes = Class.objects.order_by('id')
    depts = Department.objects.order_by('id')
    students = Student.objects.order_by('-id')
    data={}
    treedept=[]
    treecla=[]
    tempclass=[]
    tempdept=[]
    judgecla=0
    judgedept=0
    for de in depts:
        treedept.append([de.id,de.deptname])
    for stu in students:
        for cla in tempclass:
                if stu.clasid_id == cla:
                    judgecla=1
        if judgecla==0:
            tempclass.append(stu.clasid_id)
            treecla.append([str(stu.clasid.departmentid.id),stu.clasid.grade,stu.clasid.claname,str(stu.clasid.id)])
        else:
            judgecla=0
    for ca in treecla:
        for dp in tempdept:
            if ca[0]==dp:
                judgedept=1
        if judgedept==0:
            tempdept.append(ca[0])
            deptname=Department.objects.get(id=int(ca[0])).deptname
            # treedept.append([ca[0],deptname])
        else:
            judgedept=0
    data["depttree"]=treedept
    data["clatree"]=treecla
    return HttpResponse(json.dumps(data))

def groupstudentinfo(request,pagenum):
        pageMaxcount = 7
        if request.method == 'POST':
                try:
                        claid = request.POST['Info']
                        students=Student.objects.filter(clasid_id=claid)
                        stupage=students[int(pagenum)*pageMaxcount:(int(pagenum)+1)*pageMaxcount]
                except ValueError:
                        logger.error("groups")
                        raise Http404()
        student=[]
        for stu in stupage:
                student.append([stu.id,stu.stuno,stu.stuname,stu.sex,stu.clasid.claname])
        data = {}
        data["student"] = student
        data["totalcount"] = students.count()

        return HttpResponse(json.dumps(data))

def checkgroname(request):
        global logger
        groups = Group.objects.order_by('-id')
        judgegname=0
        if request.method == 'POST':
                try:
                        groname=request.POST['gname']
                except ValueError:
                        logger.error("groups")
                        raise Http404()
                for  gro in groups:
                        if groname==gro.gname:
                                judgegname=1
                                break
                data={}
                data["judgegname"]=judgegname
                return HttpResponse(json.dumps(data))

def addgroup(request):
        global logger
        if request.method == 'POST':
                try:
                        Infostring = request.POST['Infoform']
                except ValueError:
                        logger.error("groups")
                        raise Http404()
                JsonInfo = json.loads(Infostring)

                gp = Group(gname=JsonInfo["name"],createrid_id= int(request.session['userid']),createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
                gp.save()
                gid = gp.id
                for item in JsonInfo["studentIds"]:
                        if item == int(JsonInfo["selectcaptain"]):
                                groupmer=GroupMembers(groupid_id=gid,studentid_id=int(item),iscaptain=True)
                        else:
                                groupmer=GroupMembers(groupid_id=gid,studentid_id=int(item),iscaptain=False)
                        groupmer.save()
        return HttpResponseRedirect('/groups/')

def GetEditInfo(request,pagenum):
        setnu = 0
        pageMaxcount = 7
        data={}
        try:
            if request.method == 'POST':
                gid = request.POST['Infoform']
                gp = Group.objects.get(id=gid)
                students=GroupMembers.objects.filter(groupid_id=gid).order_by("id")
                stupage = students[int(pagenum)*pageMaxcount:(int(pagenum)+1)*pageMaxcount]
                data["id"] = gid
                data["name"] = gp.gname
                sts=[]#GroupMembers student id
                groupmers=[]#Student object
                for x in stupage:#遍历所有分页选出的学生，数据传给前台
                    sts.append(x.studentid_id)
                    stu = Student.objects.get(id=x.studentid_id)
                    if x.iscaptain == True:
                        data["captain"] = stu.stuno+","+stu.stuname
                        data["captainid"] = stu.id
                    groupmers.append([stu.id,stu.stuno,stu.stuname,stu.sex,stu.clasid.claname])
                for x in students:#遍历所有学生找出队长
                    if x.iscaptain == True:
                        setnu = 1
                        stu=Student.objects.get(id=x.studentid_id)
                        data["captain"] = stu.stuno+","+stu.stuname
                if(setnu == 0):
                    data["captain"] = ""
                data["groupmers"] = groupmers
                data["students"] = sts 
                data["totalcount"] = students.count()     
        except ValueError:
            logger.error("groups")
            raise Http404()
        finally:
            return HttpResponse(json.dumps(data))

def Isinexam(request):
    data = {}
    data['cando'] = "true"
    data["isexam"] = "0"
    data["names"]=''
    try:
        if request.method == 'POST':
            exams = Examinations.objects.order_by("id")
            atks=Atkdfs.objects.order_by("id")
            gid = request.POST['Infoform']
            gro = Group.objects.get(id=gid)
            cando = funcando(request,gro.createrid)
            if cando == "false":
                data['cando'] = "false"
                return HttpResponse(json.dumps(data))
            egps = ExamGroup.objects.filter(groupID_id=gid)
            for egp in egps:
                exam=exams.filter(id=egp.examID_id)
                if len(exam)>0:
                    if exam[0].examStatus!=0:
                        data["isexam"] = "1"
                        data["names"] = exam[0].examName
                        return HttpResponse(json.dumps(data))
            atkgs=AtkdfsGroup.objects.filter(groupID_id=gid)
            for atkg in atkgs:
                atk=atks.filter(id=atkg.atkdfsID_id)
                if len(atk)>0:
                    if atk[0].atkdfsStatus!=0:
                        data["isexam"] = "2"
                        data["names"] =atk[0].atkdfsName
                        return HttpResponse(json.dumps(data))
            return HttpResponse(json.dumps(data))
    except Exception:
        data["isexam"] = "3"
        return HttpResponse(json.dumps(data))
#all groupmembers
def Getgroupmembers(request):
        data={}
        try:
                if request.method == 'POST':
                        gid = request.POST['Infoform']
                        gp = Group.objects.get(id=gid)
                        students=GroupMembers.objects.filter(groupid_id=gid).order_by("id")
                        data["id"] = gid
                        data["name"] = gp.gname
                        groupmers=[]#Student object

                        for x in students:#遍历所有学生找出队长
                            stu=Student.objects.get(id=x.studentid_id)
                            if x.iscaptain == True:
                                data["cap"] = stu.id
                            groupmers.append([stu.id,stu.stuno,stu.stuname,stu.sex,stu.clasid.claname])
                        data["groupmers"] = groupmers                          
        except ValueError:
            logger.error("groups")
            raise Http404()
        finally:
            return HttpResponse(json.dumps(data))
       

def addmer(groID, JsonInfo):
        for item in JsonInfo['studentIds']:
                if item == int(JsonInfo["selectcaptain"]):
                        groupmer=GroupMembers(groupid_id=groID,studentid_id=int(item),iscaptain=True)
                else:
                        groupmer = GroupMembers(groupid_id=groID, studentid_id=int(item),iscaptain=False)
                groupmer.save()

def clearmer(groID):
        groupmer = GroupMembers.objects.filter(groupid_id = int(groID))
        for item in groupmer:
                item.delete() 

def updateproup(request):
        global logger
        if request.method == 'POST':
                try:
                        Infostring = request.POST['Infoform']#前台表单的数据
                except ValueError:
                        logger.error("groups")
                        raise Http404()
                JsonInfo = json.loads(Infostring)
                editgroid = JsonInfo["id"]
                gp = Group.objects.get(id=editgroid)
                clearmer(editgroid)
                gp.gname = JsonInfo["name"]
                gp.edittime = datetime.datetime.now() 
                gp.save()
                addmer(editgroid,JsonInfo)

        return HttpResponseRedirect('/groups/')
