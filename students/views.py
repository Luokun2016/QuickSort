#-*- coding: utf-8 -*- 
# Create your views here.
#from django.views.decorators.csrf import csrf_protect

'''
学员增删改操作
包含解析Excel文件实现批量创建功能
'''

from django.shortcuts import render_to_response,render
from students.models import Student
from classes.models import Class,Department
from groups.models import Group,GroupMembers
from courses.models import Course,Coursestudent,Courseteacher
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import xlrd
import os
import json
from teachers.models import Teacher
import re
import logging
from django.db.models import Q
from tsssite.settings import HERE

from adminsys.views import funcando
from client.views import decorator
from adminsys.views import add_record

logger = logging.getLogger('mysite.log')
# 返回展示学员信息页面信息
def mgrstudent(request,aaa=0):
        if request.POST.get('createstu',''):
                if request.POST.get('createstu','')=='1':
                        createstu=1
                else:
                        return HttpResponseRedirect('/Login/')
        else:
                createstu=0
                if not 'username' in request.session:
                        return HttpResponseRedirect('/Login/')
        students = Student.objects.filter(needaudit=0)
        classes = Class.objects.order_by('id')
        depts = Department.objects.order_by('id')
        deptls = Department.objects.order_by('id')
        cladic= {}
        stuselect=''
        depttree={}
        clatree={}
        treedept=[]
        treecla=[]
        for dp in depts:
                treedept.append([str(dp.id),dp.deptname]);
        for  ca in classes:
                treecla.append([str(ca.departmentid_id),ca.grade,ca.claname,str(ca.id)]);
        depttree["key"]=treedept
        clatree["key"]=treecla
        judgeclass = 0
        classinformation=''
        deptinformation=''
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                students=students.filter(Q(stuname__icontains=querytext)|Q(stuno__icontains=querytext))
                stuselect=querytext
        else:
                if 'judgeall' in request.GET and  request.GET['judgeall'] == '1':
                        students = Student.objects.order_by('-id')
                        stuselect=''
                else:    
                        if 'studentselect' in request.GET:
                                if request.GET.get("studentselect")=='':
                                        students= Student.objects.filter(needaudit=0)
                                        stuselect=''
                                else:
                                        students= Student.objects.filter(needaudit=0)
                                        querytext = request.GET.get("studentselect")
                                        students=students.filter(Q(stuname__icontains=querytext)|Q(stuno__icontains=querytext))
                                        stuselect=querytext
                        else:
                                departments=Department.objects.order_by('-id')
                                classes= Class.objects.order_by('-id')
                            
                                if  len(departments) == 0:
                                        students=[] 
                                elif len(classes) == 0:
                                        deptidgather=[]
                                        judgeclass=2
                                        students=[]
                                        for dept in depts:
                                                deptidgather.append(dept.id)
                                        firstdept=min(deptidgather)
                                        deptinformation=Department.objects.get(id=firstdept)    
                                else:
                                        deptidgather=[]
                                        for dept in depts:
                                                deptidgather.append(dept.id)
                                        firstdept=min(deptidgather)
                                        claidgather=[]
                                        classels=classes.filter(departmentid_id=firstdept)
                                        for clasl in classels:
                                                claidgather.append(clasl.id)
                                        if len(claidgather) > 0:
                                                firstclass=min(claidgather)
                                                students=students.filter(clasid_id=firstclass)
                                                judgeclass=1
                                                classinformation=Class.objects.get(id=firstclass)
                                                deptinformation=Department.objects.get(id=classinformation.departmentid_id)  
    
                            
        after_range_num = 4        
        befor_range_num = 3      
        try:                     
                 page = int(request.GET.get("page",1))
                 if page < 1:
                         page = 1
        except ValueError:
                 page = 1
        paginator = Paginator(students,10) 
        try:                  
                 students_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                 students_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                 page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                 page_range = paginator.page_range[0:int(page)+befor_range_num]
        classes = Class.objects.order_by('id')
        clss=[]
        clas=[]
        judge=0
        judges=0
        judg=0
        departments=Department.objects.order_by('-id')
        dept=''
        for department in departments:
                dept=department
        departments=Department.objects.order_by('id')       
        for c in classes:
                for cls in clss:
                        if(cls.grade==c.grade):
                                if(cls.departmentid_id==c.departmentid_id):
                                        judg=1
                if(judg==0):
                        clss.append(c)
                else:
                        judg=0 
        
        if dept != '':
                classes=classes.filter(departmentid_id=dept.id)
        grade=''      
        for cla in classes:
                for cl in clas:
                        if (cl.grade==cla.grade):
                                judge=1
                if(judge==0):
                        judges=judges+1
                        clas.append(cla)
                        if(judges==1):
                                grade=cla.grade        
                else:
                        judge=0
        classes = Class.objects.order_by('id')

        if createstu==1:
                datas=[]
                for m_tree in treedept:
                        data={}
                        data[m_tree[0]]=m_tree[1]
                        datas.append(data) 
                return HttpResponse(json.dumps(datas))
        return render_to_response('templates/student.html',{'stuselect':stuselect,'depttree':json.dumps(depttree),'clatree':json.dumps(clatree),'clss':clss,'dept':dept,'grade':grade,'classes':classes,'clas':clas,'departments':departments,'deptls':deptls,'judgeclass':judgeclass,'deptinformation':deptinformation,'classinformation':classinformation,'students':students_list,'studen':students,'page_range':page_range,'classes':classes,'cladic':cladic, 'depts':depts,'claseid':aaa},context_instance=RequestContext(request))
# 添加学员方法    
def addstudent(request):
        createstu=0
        if request.POST.get('createstu',''):
                if request.POST.get('createstu','')=="1":
                        createstu=1
                else:
                        return HttpResponseRedirect('/Login/')
        else:
                createstu=0
                if not 'username' in request.session:
                        return HttpResponseRedirect('/Login/')

        judgeadd=0
        errors = []
        departments=Department.objects.order_by('-id')
        for department in departments:
                dept=department
        departments=Department.objects.order_by('id')
        
        classes = Class.objects.order_by('id')
        clss=[]
        clas=[]
        judg=0
        judge=0
        judges=0
        students= Student.objects.order_by('-id')
        for c in classes:
                for cls in clss:
                        if(cls.grade==c.grade):
                                if(cls.departmentid_id==c.departmentid_id):
                                        judg=1
                if(judg==0):
                        clss.append(c)
                else:
                        judg=0

        classes=classes.filter(departmentid_id=dept.id)
        for cla in classes:
                for cl in clas:
                        if (cl.grade==cla.grade):
                                judge=1
                if(judge==0):
                        judges=judges+1
                        clas.append(cla)
                        if(judges==1):
                                grade=cla.grade        
                else:
                        judge=0
        classes=Class.objects.order_by('id')

        classes = Class.objects.order_by('id')
        if request.method == 'POST':
                if not request.POST.get('stuname',''):
                        errors.append('stuname')
                for stud in students:
                        if(stud.stuno==request.POST['stuno']):
                                judgeadd=1
                                break;
                if(judgeadd==0):
                        if(createstu==1):
                                stu = Student(stuname=request.POST['stuname'], stuno=request.POST['stuno'], pwd=request.POST['pwd'],sex=int(request.POST['sex']),clasid_id=int(request.POST['clasid']),email=request.POST['email'],mobile=request.POST['mobile'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),createbytea_id=1,needaudit=1)
                                stu.save()
                        else:   
                                stu = Student(stuname=request.POST['stuname'], stuno=request.POST['stuno'], pwd=request.POST['pwd'],sex=int(request.POST['sex']),clasid_id=int(request.POST['clasid']),email=request.POST['email'],mobile=request.POST['mobile'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),createbytea_id=request.session["userid"],needaudit=0)
                                stu.save()
        students= Student.objects.order_by('-id')
        if createstu==1:
                data = {}
                data["result"] = judgeadd
                add_record(request.POST['stuno'], u'学员注册成功，等待审核。', 1, 1)
                return HttpResponse(json.dumps(data)) 

        return mgrstudent(request,int(request.POST['clasid']))
        
        # return HttpResponseRedirect('/students/')
# 编辑学员方法
def editstudent(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')

        errors = ''
        classes=Class.objects.order_by('id')
        clas=[]
        clss=[]
        departments=Department.objects.order_by('id')
        judge=0
        judg=0
        students=Student.objects.order_by('-id')
        judgeadd=0
        try:
                did = int(did)
                stu = Student.objects.get(id=did)     
        except ValueError:
                logger.error("students")
                raise Http404()  
        
        for c in classes:
                for cls in clss:
                        if(cls.grade==c.grade):
                                if(cls.departmentid_id==c.departmentid_id):
                                        judg=1
                if(judg==0):
                        clss.append(c)
                else:
                        judg=0
        classes=classes.filter(departmentid_id=stu.clasid.departmentid_id)
        for cla in classes:
                for cl in clas:
                        if (cl.grade==cla.grade):
                                judge=1
                if(judge==0):
                        clas.append(cla)
                else:
                        judge=0
        classes=Class.objects.order_by('id')                        
        if request.method == 'POST':
                if not request.POST.get('stuname',''):
                        errors.append('stuname')
                for stud in students:
                        if(stud.stuno==request.POST['stuno']):
                                if(stud.stuno!=stu.stuno):
                                        judgeadd=1
                                        break;
                if(judgeadd==0):
                        if not request.POST.get('pwd',''):
                                stu.stuname = request.POST['stuname']
                                stu.stuno = request.POST['stuno']
                                stu.sex=int(request.POST['sex'])
                                stu.clasid_id=int(request.POST['clasid'])
                                stu.sex=int(request.POST['sex'])
                                stu.email=request.POST['email']
                                stu.mobile=request.POST['mobile']
                                stu.edittime=datetime.datetime.now()
                                stu.save()
                        else:
                                stu.stuname = request.POST['stuname']
                                stu.stuno = request.POST['stuno']
                                stu.pwd = request.POST['pwd']
                                stu.sex=int(request.POST['sex'])
                                stu.clasid_id=int(request.POST['clasid'])
                                stu.sex=int(request.POST['sex'])
                                stu.email=request.POST['email']
                                stu.mobile=request.POST['mobile']
                                stu.edittime=datetime.datetime.now()
                                stu.save()
        students=Student.objects.order_by('-id')

        return mgrstudent(request,int(request.POST['clasid']))
        #return HttpResponseRedirect('/students/')

@decorator('stu')
# 删除学员方法
def delstudent(request, did):
    global logger
    if not 'username' in request.session:
            return HttpResponseRedirect('/Login/')
    # import pdb
    # pdb.set_trace()


    error = ''
    try:
        did = int(did)
        stu = Student.objects.get(id=did)
    except ValueError:
        logger.error("students")
        raise Http404()
    stu.delete()
    
    #删除学生遍历团队队员为空的删除记录
    group = Group.objects.order_by('-id')
    for gup in group:
        members = GroupMembers.objects.filter(groupid_id = gup.id)
        if not members:
            gup.delete()
    students = Student.objects.order_by('-id')
    return HttpResponseRedirect('/students/')
# 下载批量创建学员模板方法
def download_file(request):
        path = os.path.join( HERE , 'students/model/model.xlsx')
        f = open(path)
        data = f.read()
        f.close()
        response = HttpResponse(data,mimetype='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % 'model.xlsx'
        return response
# 解析Excel文件批量添加学员方法
def addstudents(request):
    if not 'username' in request.session:
            return HttpResponseRedirect('/Login/')
    judge=1
    students = Student.objects.order_by('-id')
    classes = Class.objects.order_by('-id')
    departments = Department.objects.order_by('-id')
    if request.method == 'POST':
        addstudent_ids=[]
        judgerow=0
        judgeadd=0    
        classid=0          
        std=[]
        if(judgeadd==0):
            mfile=request.FILES['image_file']
            nan=request.POST['nan']
            nv=request.POST['nv']
            f = handle_uploaded_file(mfile)
            if f != None:
                    if(f.name[-5:] == '.xlsx'):
                        data = xlrd.open_workbook(f.name)
                        table = data.sheets()[0]
                        i=table.nrows-1
                        while i>0: 
                            try:
                                judgerow=0
                                classid=0
                                deptid=0
                                gradeid=0
                                if(len(table.cell(i,1).value)>20):
                                    judgerow=16
                                elif(len(table.cell(i,0).value)>20):
                                    judgerow=17                                   
                                else:
                                    if table.cell(i,5).value.isdigit():
                                        for dept in departments:
                                            if (dept.deptname == table.cell(i,4).value):
                                                deptid=dept.id
                                                for cla in classes:
                                                    if (cla.departmentid_id==dept.id):
                                                        if(cla.grade==int(table.cell(i,5).value)):
                                                            gradeid=cla.id
                                                            if(cla.claname==table.cell(i,6).value):
                                                                classid=cla.id
                                                                break
                                    if (classid==0):
                                        judgerow=5 
                                    if (gradeid==0):
                                        judgerow=15
                                    if (deptid==0):
                                        judgerow=14 
                                    if(table.cell(i,0).value==""):
                                        judgerow=6  
                                    if(table.cell(i,1).value==""):
                                        judgerow=7
                                    if(table.cell(i,3).value==nan):
                                        stusex=0
                                    else :
                                        if(table.cell(i,3).value==nv):
                                            stusex=1
                                        else:
                                            judgerow=1
                                    if(len(table.cell(i,2).value)<6):
                                        judgerow=2
                                    if(len(table.cell(i,2).value)>20):
                                        judgerow=3
                                    if(len(table.cell(i,0).value)>30):
                                        judgerow=8
                                    if(len(table.cell(i,1).value)>30):
                                        judgerow=9
                                    if((table.cell(i,8).value)!=""):
                                        try:
                                            strvalue= '%d' %(table.cell(i,8).value)
                                        except Exception, e:
                                            strvalue=table.cell(i,8).value
                                        if re.match("^1[0-9]{10}$|^0[0-9]{2,3}(-)?[0-9]{7,8}$",strvalue)==None:
                                            judgerow=10
                                    if (len(table.cell(i,7).value) > 50):
                                        judgerow=11
                                    if(table.cell(i,7).value!=""): 
                                        if (re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", table.cell(i,7).value) == None):
                                            judgerow=12
                                    for sd in students:
                                        if (sd.stuno==table.cell(i,1).value):
                                            judgerow=4
                                            break
                                    # 如果批量添加的信息中有重复学号则为错误
                                    if table.cell(i,1).value in addstudent_ids:
                                        judgerow=4
                                    else:
                                        # 将没有重复信息则添加到数组中记录
                                        addstudent_ids.append(table.cell(i,1).value) 
                            except Exception, e:
                                judgerow=13

                            #print judgerow
                            if(judgerow==0):                            
                                stu=Student(stuname=table.cell(i,0).value,stuno=table.cell(i,1).value,pwd=table.cell(i,2).value,sex=stusex,clasid_id=classid,email=table.cell(i,7).value,mobile=table.cell(i,8).value,createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),createbytea_id=request.session["userid"],needaudit=0)
                                stu.save()
                                std.append([table.cell(i,1).value,table.cell(i,0).value,table.cell(i,3).value,table.cell(i,4).value,table.cell(i,5).value,table.cell(i,6).value,table.cell(i,7).value,table.cell(i,8).value,'0'])
                            else:
                                std.append([table.cell(i,1).value,table.cell(i,0).value,table.cell(i,3).value,table.cell(i,4).value,table.cell(i,5).value,table.cell(i,6).value,table.cell(i,7).value,table.cell(i,8).value,judgerow])
                            i=i-1        
                    os.remove(f.name)
    data={}
    data["table"]=std
    # print json.dumps(data)
    return HttpResponse(json.dumps(data))
# 上传Excel文件方法
def handle_uploaded_file(f):
        global logger
        try:
                with open(f.name, 'wb+') as info:
                        for chunk in f.chunks():
                                info.write(chunk)
                return f
        except ValueError:
                logger.error("students")
                return None
# 获取学员信息                
def studentinfo(request):
        global logger
        stu = ''
        data = {}
        data['cando'] = "true"

        if request.method == 'POST':
                try:
                        stuid = request.POST['stuid']
                        stu = Student.objects.get(id=stuid)
                except ValueError:
                        logger.error("students")
                        raise Http404()

        cando = funcando(request,stu.createbytea)
        if cando == "false":
            data['cando'] = "false"
            return HttpResponse(json.dumps(data))
        data["stuid"] = stu.id
        data["stuname"]=stu.stuname
        data["stuno"] = stu.stuno
        data["sex"] = stu.sex
        data["email"] = stu.email
        data["mobile"] = stu.mobile
        data["departmentid"]=stu.clasid.departmentid_id
        data["grade"]=stu.clasid.grade
        data["clasid"]=stu.clasid_id
        cls=[]
        clas=[]
        judge=0
        classes=Class.objects.order_by('id')
        classes=classes.filter(departmentid_id=stu.clasid.departmentid_id)
        for cla in classes:
          for cl in clas:
            if (cl.grade==cla.grade):
              judge=1
          if(judge==0):
            clas.append(cla)
          else:
            judge=0
        for cl in clas:
                cls.append(cl.grade)
        data["clas"]=cls

        classels=[]
        classes = Class.objects.order_by('id')
        for cs in classes:
                classels.append([cs.id,cs.departmentid_id,cs.claname,cs.grade])
        data['classes']=classels


        return HttpResponse(json.dumps(data))
# 添加结果
def studentaddinfo(request):
        global logger
        stu = ''
        if request.method == 'POST':
                try:
                        claid = request.POST['classidadd']
                        claidcla = Class.objects.get(id=claid)
                except ValueError:
                        logger.error("students")
                        raise Http404()                
                

        data = {}
        data["departmentid"]=claidcla.departmentid_id
        data["grade"]=claidcla.grade
        data["clasid"]=claidcla.id
        cls=[]
        clas=[]
        judge=0
        classes=Class.objects.order_by('id')
        classes=classes.filter(departmentid_id=claidcla.departmentid_id)
        for cla in classes:
                for cl in clas:
                        if (cl.grade==cla.grade):
                                judge=1
                if(judge==0):
                        clas.append(cla)
                else:
                        judge=0


        for cl in clas:
                cls.append(cl.grade)
        data["clas"]=cls
        classels=[]
        classes = Class.objects.order_by('id')
        for cs in classes:
                classels.append([cs.id,cs.departmentid_id,cs.claname,cs.grade])
        data['classes']=classels


        return HttpResponse(json.dumps(data))
# 系别信息
def deptinfo(request):
        global logger
        dept = ''
        clasname=''
        stusex=''
        if request.method == 'POST':
                try:
                        deptid = request.POST['deptid']
                        dept = Department.objects.get(id=deptid)
                except ValueError:
                        logger.error("students")
                        raise Http404()                
                
                stud=[]
                judgedel=1
                studetail=[]
                cl = Class.objects.order_by('id')
                for c in cl:
                        if(c.departmentid_id==dept.id):
                                judgedel=0
                                break
                cretime = dept.createtime.strftime('%Y-%m-%d %H:%M:%S')
                createtime = datetime.datetime.strptime(cretime, '%Y-%m-%d %H:%M:%S')
                edtime = dept.edittime.strftime('%Y-%m-%d %H:%M:%S')
                edittime = datetime.datetime.strptime(edtime, '%Y-%m-%d %H:%M:%S')
                deptdetail=[dept.deptname,str(createtime),str(edittime),judgedel]
                classes = Class.objects.order_by('id')
                clas=classes.filter(departmentid_id=dept.id)
                students = Student.objects.filter(needaudit=0)
                for cla in clas:
                        for stu in students:
                                if(stu.clasid_id==cla.id):
                                        stud.append(stu)
                students=stud 
                departments=Department.objects.order_by('-id')
                after_range_num = 4        
                befor_range_num = 3       
                try:                     
                        page = int(request.POST['page'])
                        if page < 1:
                                page = 1
                except ValueError:
                        page = 1
                paginator = Paginator(students,10)   
                try:                  
                        students_list = paginator.page(page)
                except(EmptyPage,InvalidPage,PageNotAnInteger):
                        students_list = paginator.page(paginator.num_pages)
                if page >= after_range_num:
                        page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
                else:
                        page_range = paginator.page_range[0:int(page)+befor_range_num]
                has_previous = None
                if students_list.has_previous():
                    has_previous = 1
                else:
                    has_previous = 0                
                has_next = None
                if students_list.has_next():
                    has_next = 1
                else:
                    has_next = 0
                for stude in students_list:
                        if (stude.sex==0):
                                stusex='nan'
                        else:
                                stusex='nv'
                        clasname=stude.clasid.claname
                        studetail.append([stude.id,stude.stuno,stude.stuname,stusex,stude.clasid.departmentid.deptname,stude.clasid.grade,clasname,stude.email,stude.mobile])
                deptstudetail={}
                deptstudetail["deptdetail"] = deptdetail
                deptstudetail["studetail"] = studetail
                deptstudetail['has_previous']=has_previous
                deptstudetail['number']=students_list.number
                deptstudetail['has_next']=has_next
                deptstudetail['num_pages']=students_list.paginator.num_pages
                deptstudetail['page_range']=page_range
        return HttpResponse(json.dumps(deptstudetail))
# 编辑系别信息
def depteditinfo(request):
        global logger
        dept = ''
        if request.method == 'POST':
                try:
                        deptid = request.POST['deptidinfo']
                        dept = Department.objects.get(id=deptid)
                except ValueError:
                        logger.error("students")
                        raise Http404()                 
        data = {}
        data["deptname"] = dept.deptname
        return HttpResponse(json.dumps(data))
# 班级信息
def clainfo(request):
        global logger
        cla = ''
        dept = ''
        clasname=''
        stusex=''
        if request.method == 'POST':
                try:
                        claid = request.POST['claid']
                        cla = Class.objects.get(id=claid)
                except ValueError:
                        logger.error("students")
                        raise Http404()                
                
                stud=[]
                studetail=[]
                cretime = cla.createtime.strftime('%Y-%m-%d %H:%M:%S')
                createtime = datetime.datetime.strptime(cretime, '%Y-%m-%d %H:%M:%S')
                edtime = cla.edittime.strftime('%Y-%m-%d %H:%M:%S')
                edittime = datetime.datetime.strptime(edtime, '%Y-%m-%d %H:%M:%S')
                cladetail=[cla.departmentid.deptname,cla.grade,cla.claname,str(createtime),str(edittime)]
                students = Student.objects.filter(needaudit=0)
                for stu in students:
                         if(stu.clasid_id==cla.id):
                                stud.append(stu)
                students=stud 
                departments=Department.objects.order_by('-id')

                after_range_num = 4        
                befor_range_num = 3      
                try:                     
                        page = int(request.POST['page'])
                        if page < 1:
                                page = 1
                except ValueError:
                        page = 1
                paginator = Paginator(students,10)   
                try:                  
                        students_list = paginator.page(page)
                except(EmptyPage,InvalidPage,PageNotAnInteger):
                        students_list = paginator.page(paginator.num_pages)
                if page >= after_range_num:
                        page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
                else:
                        page_range = paginator.page_range[0:int(page)+befor_range_num]
                has_previous = None
                if students_list.has_previous():
                    has_previous = 1
                else:
                    has_previous = 0                
                has_next = None
                if students_list.has_next():
                    has_next = 1
                else:
                    has_next = 0
                for stude in students_list:
                        if (stude.sex==0):
                                stusex='nan'
                        else:
                                stusex='nv'
                        clasname=stude.clasid.claname
                        studetail.append([stude.id,stude.stuno,stude.stuname,stusex,stude.clasid.departmentid.deptname,stude.clasid.grade,clasname,stude.email,stude.mobile])
                deptstudetail={}
                deptstudetail['has_previous']=has_previous
                deptstudetail['number']=students_list.number
                deptstudetail['has_next']=has_next
                deptstudetail['num_pages']=students_list.paginator.num_pages
                deptstudetail['page_range']=page_range
                deptstudetail["cladetail"] = cladetail
                deptstudetail["studetail"] = studetail
        return HttpResponse(json.dumps(deptstudetail))
# 编辑班级信息
def claeditinfo(request):
        global logger
        cla = ''
        if request.method == 'POST':
                try:
                        claid = request.POST['claidinfo']
                        cla = Class.objects.get(id=claid)
                except ValueError:
                        logger.error("students")
                        raise Http404()               
                

        data = {}
        data["deptid"] = cla.departmentid_id
        data['clagrade']=cla.grade
        data['claname']=cla.claname
        return HttpResponse(json.dumps(data))
# 检查学号重复性
def studentstunocheck(request):
        global logger
        students = Student.objects.order_by('-id')
        judgestuno = 0
        if request.method == 'POST':
                try:
                        stustuno=request.POST['stuno']
                except ValueError:
                        logger.error("students")
                        raise Http404()                   
                for stu in students:
                        if (stu.stuno == stustuno):
                                judgestuno=1
                                break
        data={}
        data["judgestuno"]=judgestuno
        return HttpResponse(json.dumps(data))

def stugracla(request):
        classes = Class.objects.order_by('id')
        clss=[]
        clagrade=[]
        judg=0
        for c in classes:
                for cls in clss:
                        if(cls.grade==c.grade):
                                if(cls.departmentid_id==c.departmentid_id):
                                        judg=1
                if(judg==0):
                        clss.append(c)
                else:
                        judg=0 
        for cl in clss:
                clagrade.append([cl.grade,cl.departmentid_id])
        classels=[]
        classes = Class.objects.order_by('id')
        for cla in classes:
                classels.append([cla.id,cla.departmentid_id,cla.claname,cla.grade])
        data={}
        data['classes']=classels
        data['clss']=clagrade

        return HttpResponse(json.dumps(data))

def  coursecheck(request):
        data={}
        cours=[]
        coursesid =  Coursestudent.objects.filter(studentid_id=request.session['cuserid']).order_by('id')
        #coursesid =  Coursestudent.objects.filter(studentid_id=110)
        for courid in coursesid:
                cour=Course.objects.get(id=courid.courseid_id) 
                cours.append([cour.cname,cour.outlineid_id,cour.id])
        data["coursename"]=cours
        return HttpResponse(json.dumps(data))
# 通过组查找学员
def findStubyGroup(request, did):
        global logger
        is_ok = 'false'
        data = {}
        data['cando'] = "true"
        
        try:
                m_id = int(did)
                stu = Student.objects.get(id=m_id)
        except ValueError:
                logger.error("students")
                raise Http404()       
        cando = funcando(request,stu.createbytea)
        if cando == "false":
            data['cando'] = "false"
            return HttpResponse(json.dumps(data))
        con = stu.groupmembers_set.count()
        if con>0:
                is_ok = 'true'
        data["success"] = is_ok 
        return HttpResponse(json.dumps(data))


# 通过课程查找学员
def findStubyCourse(request, did):
        global logger
        is_ok = 'false'
        try:
                m_id = int(did)
                #print type(m_id)
                stu = Student.objects.get(id=m_id)
        except ValueError:
                logger.error("students")
                raise Http404()
        con = stu.coursestudent_set.count()
        if con>0:
                is_ok = 'true'
        data = {}
        data["success"] = is_ok 
        return HttpResponse(json.dumps(data))
# 审核学员
class Studentregister:
    def __init__(self,m_id, number,name, sex, classname,deptname,grade):
        self.id = m_id
        self.number = number
        self.name = name
        self.sex = sex
        self.classname = classname
        self.deptname = deptname
        self.grade = grade
# 审核学员页面显示信息
def registerstudent(request):
        students = Student.objects.filter(needaudit=1)
        # if len(students)>0:
        classes = Class.objects.order_by('id')
        depts = Department.objects.order_by('id')
        classes_dic= {}
        depts_dic={}
        stumsg=[]
        for dp in depts:
                depts_dic[dp.id]=dp.deptname
        for  ca in classes:
                classes_dic[ca.id]=ca
        for stu in students:
                classname=classes_dic[stu.clasid_id].claname
                grade=classes_dic[stu.clasid_id].grade
                deptname=depts_dic[classes_dic[stu.clasid_id].departmentid_id]
                m_stu=Studentregister(stu.id,str(stu.stuno) , stu.stuname, stu.sex, classname, deptname, grade)
                stumsg.append(m_stu)

        after_range_num = 4        
        befor_range_num = 3  
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(stumsg,10)
        try:
                stu_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                stu_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                page_range = paginator.page_range[0:int(page)+befor_range_num]           
        return render_to_response('templates/registerstudent.html',{'stu_list':stu_list,'page_range':page_range,'stumsg':stumsg},context_instance=RequestContext(request))
# 通过审核       
def accetstudent(request):
        if request.method == 'POST':
                accent=0
                stuid = request.POST['studentid']
                stu = Student.objects.get(id=stuid)
                try:
                        stu.needaudit = 0
                        stu.createbytea_id=request.session["userid"]
                        stu.save()
                except Exception, e:
                        accent=1
                if accent==0:
                        add_record(request.session['useraccount'], u'审核通过，学员：' + stu.stuno, 1)
                        return render_to_response('templates/registerstudent.html')
                else:
                        add_record(request.session['useraccount'], u'审核失败，学员：' + stu.stuno, 0)
                        data = {}
                        data["error"] = 1 
                        return HttpResponse(json.dumps(data))  
# 不通过审核
def cancelregister(request):
        if request.method == 'POST':
                accent=0
                stuid = request.POST['studentid']   
                try:
                        did = int(stuid)
                        stu = Student.objects.get(id=did)
                except ValueError:
                        accent=1
                stu.delete()
                if accent==0:
                        add_record(request.session['useraccount'], u'审核不通过，学员：' + stu.stuno, 1)
                        return render_to_response('templates/registerstudent.html')
                else:
                        add_record(request.session['useraccount'], u'审核失败，学员：' + stu.stuno, 0)
                        data = {}
                        data["error"] = 1 
                        return HttpResponse(json.dumps(data))  

# 需要审核的学员
def spangled(request):
    spangle=0
    students = Student.objects.filter(needaudit=1)
    if len(students)>0:
        spangle+=1

    currenttea = Teacher.objects.get(id=request.session['userid'])
    if currenttea.roletype ==1:
        teachers= Teacher.objects.filter(needaudit=1)
        if len(teachers)>0:
            spangle+=1    
    data = {}
    if spangle>0:
        data["spangled"] = 1 
    else:
        data["spangled"] = 0
    return HttpResponse(json.dumps(data))  