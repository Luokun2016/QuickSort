#-*- coding: utf-8 -*- 
'''
1. 添加系：adddepartment
2. 添加班级：addclass
3. 删除系：deldepartment
4. 删除班级：delclass
5. 编辑系：editdepartment
6. 编辑班级：editclass
'''

from django.shortcuts import render_to_response
from django.template import RequestContext, Template, Context
from classes.models import Class, Department
from teachers.models import Teacher
from students.models import Student
from django.http import HttpResponse, Http404, HttpResponseRedirect
import datetime
import json
import logging
logger = logging.getLogger('mysite.log')
def adddepartment(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        deptls = Department.objects.order_by('id')
        classls = Class.objects.order_by('id')
        judgeadd=0
        errors = []
        if request.method == 'POST':
                if not request.POST.get('deptname',''):
                        errors.append('deptname')
                for dept in deptls:
                        if(dept.deptname==request.POST['deptname']):
                                judgeadd=1
                                break;
                if(judgeadd==0):
                        dept = Department(deptname=request.POST['deptname'],teacherid_id= request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
                        dept.save()      
        deptls = Department.objects.order_by('id')
        departments = Department.objects.order_by('id')
        return HttpResponseRedirect('/students/')


def addclass(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        deptls = Department.objects.order_by('id')
        classls = Class.objects.order_by('id')
        judgeadd=0
        errors = []
        if request.method == 'POST':
                if not request.POST.get('claname',''):
                        errors.append('claname')
                for clas in classls:
                        if(clas.claname == request.POST['claname']):
                                if(clas.grade == int(request.POST['grade'])):
                                        if(clas.departmentid_id ==int(request.POST['deptid'])):
                                                judgeadd=1
                                                break;
                if(judgeadd==0):
                        cla = Class(claname=request.POST['claname'],departmentid_id=int(request.POST['deptid']),grade=int(request.POST['grade']),teacherid_id= request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
                        cla.save()
        deptls = Department.objects.order_by('id')
        classes = Class.objects.order_by('id')
        return HttpResponseRedirect('/students/')


def delclass(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                cla = Class.objects.get(id=did)
        except ValueError:
                logger.error("classes")
                raise Http404()
        
        cla.delete()
        return HttpResponseRedirect('/students/')


def deldepartment(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                dept = Department.objects.get(id=did)
        except ValueError:
                logger.error("classes")
                raise Http404()
        
        dept.delete()
        return HttpResponseRedirect('/students/')



def editdepartment(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        errors = []
        deptls = Department.objects.order_by('id')
        classls = Class.objects.order_by('id')
        judgeadd=0
        try:
                did = int(did)
                dept= Department.objects.get(id=did)
        except ValueError:
                logger.error("classes")
                raise Http404()
        
        if request.method == 'POST':
                if not request.POST.get('deptname',''):
                        errors.append('deptname')
                for deptl in deptls:
                        if(deptl.deptname==request.POST['deptname']):
                                if(dept.deptname!=request.POST['deptname']):
                                        judgeadd=1
                                        break;
                if(judgeadd==0):
                        dept.deptname = request.POST['deptname']
                        dept.edittime=datetime.datetime.now()
                        dept.save()
        deptls = Department.objects.order_by('id')
        departments = Department.objects.order_by('id')
        return HttpResponseRedirect('/students/')


def editclass(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        errors = []
        deptls = Department.objects.order_by('id')
        classls = Class.objects.order_by('id')
        judgeadd=0
        try:
                did = int(did)
                clas=Class.objects.get(id=did)
        except ValueError:
                logger.error("classes")
                raise Http404()
        
        if request.method == 'POST':
                if not request.POST.get('claname',''):
                        errors.append('claname')
                for clasl in classls:
                        if(clasl.claname == request.POST['claname']):
                                if(clasl.grade == int(request.POST['grade'])):
                                        if(clasl.departmentid_id ==int(request.POST['deptid'])):
                                                judgeadd=1
                                                break;
                if(judgeadd==0):
                        clas.claname = request.POST['claname']
                        clas.grade = request.POST['grade']
                        clas.departmentid_id = request.POST['deptid']
                        clas.edittime=datetime.datetime.now()
                        clas.save()
        deptls = Department.objects.order_by('id')
        classes = Class.objects.order_by('id')
        return HttpResponseRedirect('/students/')

def deptnamecheck(request):
        departments = Department.objects.order_by('-id')
        judgedeptname= 0
        if request.method == 'POST':
                deptdeptname=request.POST['deptname']
               # print deptdeptname
                for dept in departments:
                        if (dept.deptname == deptdeptname):
                                judgedeptname=1
                                break
        data={}
        data["judgedeptname"]=judgedeptname
        return HttpResponse(json.dumps(data))

def clanamecheck(request):
        classes = Class.objects.order_by('-id')
        judgeclaname= 0
        if request.method == 'POST':
                cladeptid= int(request.POST['deptid'])
                clagrade = int(request.POST['grade'])
                claclaname = request.POST['claname']
                for cla in classes:
                        if (cla.claname==claclaname):
                                if(cla.grade==clagrade):
                                        #print cla.departmentid_id
                                        #print cladeptid
                                        if(cla.departmentid_id==cladeptid):
                                                judgeclaname=1
                                                break
        data={}
        data["judgeclaname"]=judgeclaname
        return HttpResponse(json.dumps(data))


