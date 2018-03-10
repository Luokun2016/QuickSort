#-*- coding: utf-8 -*- 
'''
完成对课程的增删改查功能。
'''
from django.shortcuts import render_to_response
from teachers.models import Teacher
from experiments.models import  Experiment
from vms.models import Vm
from courses.models import *
from classes.models import *
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from outlines.models import  Outline
from students.models import  Student
from os.path import basename
from os.path import splitdrive
import os.path
import datetime
import zipfile
import shutil
import json
import xlrd
import os
import sys
import re
import logging
from tsssite.settings import HERE
from client.views import decorator
from adminsys.views import add_record

logger = logging.getLogger('mysite.log')

def mgrcourse(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	data = privateGetCoursesInfo(0,request)
	add_record(request.session['useraccount'], u"访问课程安排", 1)
 	return  render_to_response('templates/course.html',{'data':json.dumps(data)}, context_instance=RequestContext(request))

def selectcourse(request):
	
	if request.method == 'POST':
		try:
			selecourse = request.POST['selecourse']
		except ValueError:
			logger.error("courses")
			raise Http404()
	data = privateGetCoursesInfo(0,request,selecourse)

	
	return HttpResponse(json.dumps(data))
			
#get teachers and courses infomation 
def GetAddConfig(request):
	data=privateGetPopConfig()
	return HttpResponse(json.dumps(data))

def  CouresPageChage(request):
	if not 'username' in request.session:
		return HttpResponseRedirect('/Login/')
	page=0
	if request.method == 'POST':
		page = int(request.POST['page'])
	data = privateGetCoursesInfo(page,request)
	return HttpResponse(json.dumps(data))

def privateGetPopConfig():
	teachers = Teacher.objects.order_by('-id')
	#print("teachers");
	outlines = Outline.objects.order_by('-id')
	#print("outlines");
	students = Student.objects.order_by('-id')
	#print("students");
	data={}
	ths=[]
	ous=[]
	sts=[]

	for item in teachers:
		th={}
		th["id"]=item.id
		th["teaname"]=item.teaname
		th["roletype"]=item.roletype
		th["sex"]=item.sex
		th["mobile"]=item.mobile
		th["email"]=item.email
		ths.append(th)
	data["teachers"]=ths
	

	for item in outlines:
		ou={}
		ou["id"]=item.id
		ou["onid"]=item.onid
		ou["onname"]=item.onname
		ou["teacher"]=item.teacherid.teaname
		ou["isdefaultoutline"]=item.isdefaultoutline
		ou["createtime"]=str(item.createtime.strftime("%Y-%m-%d %H:%M"))
		ou["edittime"]=str(item.edittime.strftime("%Y-%m-%d %H:%M"))
		try:
			ou["remark"]=str(item.remark)
		except Exception, e:
			ou["remark"]=item.remark
		ous.append(ou)

	data["outlines"]=ous

	for item in students:
		st={}		
		st["id"]=item.id

		st["stuname"]=item.stuname		
		try:
			st["stuno"]=str(item.stuno)
		except Exception, e:
			st["stuno"]=item.stuno
		st["sex"]=item.sex
		st["grade"]=item.clasid.grade
		st["clasid"]=item.clasid.id
		st["claname"]=item.clasid.claname
		st["departmentid"]=item.clasid.departmentid.id
		st["departmentname"]=item.clasid.departmentid.deptname
		st["clasid"]=item.clasid.id
		sts.append(st)
	data["students"]=sts
	
	return data	

# 查看是否有课程正在使用的虚拟机，使用课程名查找，没有返回0，有返回2
def getstartmvMsg(cname):
	vms=Vm.objects.filter(usetype=0, state=1)
	get_result=0
	for vm in vms:
		if vm.useNo == cname:
			get_result = 2
	return get_result

def GetEditConfig(request):
	global logger
	data=privateGetPopConfig()
	data["result"]=0
	try:
		if request.method == 'POST':
			courseid = int(request.POST['Info'])
			course=Course.objects.get(id=courseid)
			students =  Coursestudent.objects.filter(courseid_id=courseid).order_by('-id')
			teachers =  Courseteacher.objects.filter(courseid_id=courseid).order_by('-id')
			co={}
			co["id"] = course.id
			co["cname"] = course.cname
			co["creater"] = course.createrid.teaname
			co["comments"] = course.comments
			co["begintime"] = course.begintime.strftime("%Y-%m-%d %H:%M")
			co["endtime"] = course.endtime.strftime("%Y-%m-%d %H:%M")
			co["createtime"] = course.createtime.strftime("%Y-%m-%d %H:%M")
			co["edittime"] = course.edittime.strftime("%Y-%m-%d %H:%M")
			co["outlineid"] = course.outlineid_id

			ths=[]
			sts=[]
			for x in students:
				sts.append(x.studentid_id)
			for x in teachers:
				ths.append(x.teacherid_id)

			co["students"]=sts
			co["teachers"]=ths
			data["edit"]=co
			data["result"]=getstartmvMsg(course.cname)

	except: 
		logger.error("courses")
		data["result"]=1
	finally:
		return HttpResponse(json.dumps(data))

def GetViewConfig(request):
	global logger
	data={}
	try:
		if request.method == 'POST':

			courseid = int(request.POST['Info'])
			course=Course.objects.get(id=courseid)
			students =  Coursestudent.objects.filter(courseid_id=courseid).order_by('-id')
			teachers =  Courseteacher.objects.filter(courseid_id=courseid).order_by('-id')
			
			data["id"] = course.id
			data["cname"] = course.cname
			data["creater"] = course.createrid.teaname
			data["comments"] = course.comments
			data["begintime"] = course.begintime.strftime("%Y-%m-%d %H:%M")
			data["endtime"] = course.endtime.strftime("%Y-%m-%d %H:%M")
			data["createtime"] = course.createtime.strftime("%Y-%m-%d %H:%M")
			data["edittime"] = course.edittime.strftime("%Y-%m-%d %H:%M")
			data["outlinename"] = course.outlineid.onname

			ths=[]
			sts=[]
			for item in students:
				st={}
				st["id"]=item.id
				st["stuname"]=item.studentid.stuname
				st["stuno"]=item.studentid.stuno
				st["sex"]=item.studentid.sex
				st["grade"]=item.studentid.clasid.grade
				st["claname"]=item.studentid.clasid.claname
				st["departmentname"]=item.studentid.clasid.departmentid.deptname
				sts.append(st)
			for x in teachers:
				ths.append(x.teacherid.teaname)

			data["students"]=sts
			data["teachers"]=ths

	except: 
		logger.error("courses")
		data["result"]=1
	else:
		data["result"]=0
	finally:
		return HttpResponse(json.dumps(data))

#when course information changed,refresh the main page's courses list
def RefreshCourse(request):
	data = privateGetCoursesInfo(0,request)
	return HttpResponse(json.dumps(data))

def seleCoursesInfo(page,request,selecourse):
	pageMaxcount=10
	data={}
	cous=[]


	courses = Course.objects.filter(cname__icontains=selecourse).order_by('-id')[page*pageMaxcount:(page+1)*pageMaxcount]

	if courses:
		for co in courses:
			# tename = Teacher.objects.get(id=co.createrid_id)
			cou={}
			cou["id"] =co.id
			cou["cname"] =co.cname
			cou["creater"] = co.createrid.teaname
			cou["comments"] = co.comments
			cou["begintime"] = co.begintime.strftime("%Y-%m-%d %H:%M")
			cou["endtime"] = co.endtime.strftime("%Y-%m-%d %H:%M")
			cou["createtime"] = co.createtime.strftime("%Y-%m-%d %H:%M")
			cou["edittime"] = co.edittime.strftime("%Y-%m-%d %H:%M")
			cou["outlineid"] = co.outlineid_id

			students =  Coursestudent.objects.filter(courseid_id=co.id).order_by('-id')
			teachers =  Courseteacher.objects.filter(courseid_id=co.id).order_by('-id')
			ths=[]
			sts=[]
			for x in students:
				sts.append(x.studentid_id)
			for x in teachers:
				ths.append(x.teacherid.teaname)

			cou["students"]=sts
			cou["teachers"]=ths
			cous.append(cou) 
	data["courses"] = cous

	# data["page"]=privateGetCoursePageInfo(page,request)
	return data

def privateGetCoursesInfo(page,request,selecourse=None):
	global logger
	pageMaxcount=10
	data={}
	cous=[]

	courses_con=[]
	currenttea = Teacher.objects.get(id=request.session['userid'])
	if currenttea.roletype == 0:#教练员
		courses = Course.objects.filter(createrid_id=request.session['userid']).order_by('-id')[page*pageMaxcount:(page+1)*pageMaxcount]
	else:
		courses=Course.objects.order_by('-id')[page*pageMaxcount:(page+1)*pageMaxcount]
	for m_course in courses:
		courses_con.append(m_course)
	m_courses_teacher = Courseteacher.objects.filter(teacherid_id=request.session['userid']).order_by('-id')
	for courses_teacher in m_courses_teacher:
		current_course = Course.objects.get(id=courses_teacher.courseid_id)
		if current_course in courses:
			continue		
		else:
			courses_con.append(current_course)
	if selecourse is not None:
		m_courses_con=[]
		for course_con in courses_con:
			if course_con.cname.find(selecourse)>-1:
				m_courses_con.append(course_con)
		courses_con=m_courses_con
	for item in courses_con:
		co={}
		co["id"] = item.id
		co["cname"] = item.cname
		co["creater"] = item.createrid.teaname
		co["comments"] = item.comments
		co["begintime"] = item.begintime.strftime("%Y-%m-%d %H:%M")
		co["endtime"] = item.endtime.strftime("%Y-%m-%d %H:%M")
		co["createtime"] = item.createtime.strftime("%Y-%m-%d %H:%M")
		co["edittime"] = item.edittime.strftime("%Y-%m-%d %H:%M")
		co["outlineid"] = item.outlineid_id
		students =  Coursestudent.objects.filter(courseid_id=item.id).order_by('-id')
		teachers =  Courseteacher.objects.filter(courseid_id=item.id).order_by('-id')
		ths=[]
		sts=[]
		for x in students:
			try:
				sts.append(x.studentid_id)
			except Exception, e:
				logger.error("studentid:"+str(x.studentid_id)+" inexistence")
				pass
			
		for x in teachers:
			try:
				ths.append(x.teacherid.teaname)
			except Exception, e:
				logger.error("teacherid:"+str(x.teacherid_id)+" inexistence")
				pass

		co["students"]=sts
		co["teachers"]=ths
		cous.append(co)
	data["courses"]=cous
	data["page"]=privateGetCoursePageInfo(page,request)
	return data

def  AddNewCourses(request):
	global logger
	if request.method == 'POST':
		try:
			Infostring = request.POST['Info']
			
		except ValueError:
			logger.error("courses")
			raise Http404()
		JsonInfo = json.loads(Infostring)
		start = datetime.datetime.strptime(JsonInfo["startTime"],"%Y-%m-%d %H:%M") 
		end=datetime.datetime.strptime(JsonInfo["endTime"],"%Y-%m-%d %H:%M") 
		co=Course(cname=JsonInfo["name"],createrid_id= int(request.session['userid']),outlineid_id=int(JsonInfo["outlineId"]),comments=JsonInfo["comments"],begintime=start,endtime=end,createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
		co.save()
		coid=co.id
		for item in JsonInfo["teacherIds"]:
			th=Courseteacher(courseid_id=coid,teacherid_id=int(item))
			th.save()
		for item in JsonInfo["studentIds"]:
			st=Coursestudent(courseid_id=coid,studentid_id=int(item))
			st.save()
	data = privateGetCoursesInfo(0,request)
	add_record(request.session['useraccount'], u"添加课程："+co.cname, 1)
	return HttpResponse(json.dumps(data))
	#return HttpResponseRedirect('/courses/')

def  UpdateCourses(request):
	global logger
	page=0
	if request.method == 'POST':
		try:
			Infostring = request.POST['Info']
			page=int(request.POST['page'])
		except ValueError:
			logger.error("courses")
			raise Http404()		
		JsonInfo = json.loads(Infostring)
		start = datetime.datetime.strptime(JsonInfo["startTime"],"%Y-%m-%d %H:%M") 
		end=datetime.datetime.strptime(JsonInfo["endTime"],"%Y-%m-%d %H:%M") 
		coid=int(JsonInfo["id"])

		co=Course.objects.get(id=coid)
		co.cname=JsonInfo["name"]
		# co.createrid_id= int(request.session['userid'])
		co.outlineid_id=int(JsonInfo["outlineId"])
		co.comments=JsonInfo["comments"]
		co.begintime=start
		co.endtime=end
		co.edittime=datetime.datetime.now()
		co.save()

		olds = Courseteacher.objects.filter(courseid_id=coid)
		for item in olds:
			item.delete()

		for item in JsonInfo["teacherIds"]:
			th=Courseteacher(courseid_id=coid,teacherid_id=int(item))
			th.save()

		olds =Coursestudent.objects.filter(courseid_id=coid)
		for item in olds:
			item.delete()
		for item in JsonInfo["studentIds"]:
			st=Coursestudent(courseid_id=coid,studentid_id=int(item))
			st.save()
	data = privateGetCoursesInfo(page,request)
	add_record(request.session['useraccount'], u"修改课程："+co.cname, 1)
	return HttpResponse(json.dumps(data))

@decorator('course')
def  RemoveCourses(request):
	global logger
	page=0
	if request.method == 'POST':
		try:
			courseid = int(request.POST['Info'])
			page=int(request.POST['page'])
		except ValueError:
			logger.error("courses")
			raise Http404()		
		olds = Courseteacher.objects.filter(courseid_id=courseid)
		for item in olds:
			item.delete()

		olds =Coursestudent.objects.filter(courseid_id=courseid)
		for item in olds:
			item.delete()
		course=Course.objects.get(id=courseid)
		course.delete()
		add_record(request.session['useraccount'], u"删除课程："+course.cname, 1)
	data = privateGetCoursesInfo(page,request)

	while page!=0 and len(data["courses"])==0:
		page=page-1
		data = privateGetCoursesInfo(page,request)
	return HttpResponse(json.dumps(data))

def UpdateStudents(request):
	global logger
	stds=[]
	if request.method == 'POST':
		try:
			mfile=request.FILES['image_file']
		except ValueError:
			logger.error("courses")
			raise Http404()		
		f = handle_uploaded_file(mfile)
		if(f.name == 'model.xlsx'):
	    		excel = xlrd.open_workbook(f.name)
	    		table = excel.sheets()[0]
	    		i=0
	    		while i<table.nrows-1:  
	    			std={}
	    			std["line"]=i+1;
	    			std["stdno"]=table.cell(i+1,1).value
	 			stds.append(std)
				i=i+1       
                        	os.remove(f.name)
        	data={}
        	data["students"]=stds
	return HttpResponse(json.dumps(data))

def zip_dir(path,zipfilename):
    
    if not os.path.isdir(path):
        exit()
    
    if os.path.exists(zipfilename):
        # zipfilename is exist.Append.
        os.remove(zipfilename)
        # zipfp = zipfile.ZipFile(zipfilename, 'a' ,zipfile.ZIP_DEFLATED)
        # for dirpath, dirnames, filenames in os.walk(path, True):
        #     for filaname in filenames:
        #         direactory = os.path.join(dirpath,filaname)
        #         zipfp.write(direactory)
    # else:
        # zipfilename is not exist.Create.
    zipfp = zipfile.ZipFile(zipfilename, 'w' ,zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(path, True):
        for filaname in filenames:
            direactory = os.path.join(dirpath,filaname)
            #解决在windows下压缩包里面中文乱码问题
            direactory = direactory.decode("utf8")
            size = direactory.find('downpath')
            dirs = direactory[size+9:]
            zipfp.write(direactory,dirs)
            # zipfp.write(direactory)
    # Flush and Close zipfilename at last. 
    zipfp.close()
    return zipfilename

def gci(filepath,value):
	allfile=[]
	num=0
	if value:
		if os.path.exists(filepath):
			files = os.listdir(filepath)
			for fi in files:
				ename = Experiment.objects.get(id=int(fi))
				fi_d = os.path.join(filepath,fi)
				rname = ename.name.find(value) #匹配前台的输入
				#如果输入的是实验名称，存储该实验所有文件传到前台
				if rname != -1:
					if os.path.isdir(fi_d):
						filelist = os.listdir(fi_d)
						for li in filelist:
							allfile.append([ename.name,li,fi_d])
							num=num+1

				#匹配学生上传的实验传到前台 
				else:
					filelist = os.listdir(fi_d)
					for fl in filelist:
						fl = fl.decode("utf8")
						lname = fl.find(value)
						if lname != -1:
							allfile.append([ename.name,fl,fi_d])
							num=num+1
			
	else:
		#判断是否存在该实验的实验报告文件夹
		if os.path.exists(filepath):
			files = os.listdir(filepath)
			for fi in files:
				ename = Experiment.objects.get(id=int(fi))
				fi_d = os.path.join(filepath,fi)
				if os.path.isdir(fi_d):
					filelist = os.listdir(fi_d)
					allfile.append([ename.name,filelist,fi_d])
					num=num+1
				else:
					pass

	return allfile,num
# allfile=[]
def fileCheck(request):
	global logger
	data={}
	if request.method == 'POST':
		try:
			courseid = int(request.POST['Info'])
			huntval = request.POST['huntfile']
			downval = request.POST['downfile']
		except ValueError:
			logger.error("courses")
			raise Http404()
		path = HERE +'/document/upfile/'+str(courseid)
		allfile,num = gci(path,huntval)

		# data["downfile"] = downfile
		data["file"] = allfile

	return HttpResponse(json.dumps(data))

def getfile(filepath,value):
	allfile=[]
	ph= HERE+'/document/upfile/downpath/'
	# 每次点击下载按钮都要删除以前有过的
	if os.path.exists(ph):
		shutil.rmtree(ph)
	
	os.makedirs(ph)
	vali = value.split(",")
	#选中的要下载的实验
	for va in vali:
		va = va.split()
		files = os.listdir(filepath)
		for fi in files:
			#获取实验名称
			ename = Experiment.objects.get(id=int(fi))
			
			#判断实验名称与选中的实验名称是否符合
			if va[0] == ename.name:
				fi_d = os.path.join(filepath,fi)
			 	#临时目录以实验名命名
			 	pathname = filepath+'/'+ename.name
		 		filelist = os.listdir(fi_d)
		 		#编码问题只能放在循环外
		 		va[1]=va[1].encode("utf8")
		 		for li in filelist:
		 			#如果要下载的实验名称与里面的一致do something
		 			if li == va[1]:
		 				li=va[1].decode("utf8")
		 				path = fi_d+'/'+ li
		 				#将要下载的文件拷贝到一个临时目录里
		 				pth = HERE+'/document/upfile/downpath/'+ename.name
		 				if not os.path.exists(pth):
		 					os.makedirs(pth)
		 				pth =os.path.join(pth,li)
		 				shutil.copy(path,pth)
		 			else:
		 				pass
	
	phl = HERE+'/document/upfile/downfile.zip'
	zip_dir(ph,phl)
	return phl

def fileDown(request):
	global logger
	data={}
	if request.method == 'POST':
		try:
			courseid = int(request.POST['Info'])
			huntval = request.POST['huntfile']
			downval = request.POST['downfile']
		except ValueError:
			logger.error("courses")
			raise Http404()
		path = HERE +'/document/upfile/'+str(courseid)
		allfile = getfile(path,downval)

		# data["downfile"] = downfile
		data["downfile"] = allfile
	return HttpResponse(json.dumps(data))

def RoleCheck(request):
	global logger
	data={}
	data["hasRole"]=0
	if request.method == 'POST':
		try:
			courseid = int(request.POST['Info'])
			course=Course.objects.get(id=courseid)
		except ValueError:
			logger.error("courses")
			raise Http404()	
		userid = int(request.session['userid'])
		user = Teacher.objects.get(id=userid)
		if(user.roletype==1):
			data["hasRole"]=1

		if (course.createrid.id  ==userid):
			data["hasRole"]=1
	return HttpResponse(json.dumps(data))		

def handle_uploaded_file(f):
        with open(f.name, 'wb+') as info:
                for chunk in f.chunks():
                        info.write(chunk)
        return f

def privateGetCoursePageInfo(page,request):
	info={}
	info["page"]=page

	currenttea = Teacher.objects.get(id=request.session['userid'])
	if currenttea.roletype == 0:#教练员
		info["count"] = Course.objects.filter(createrid_id=request.session['userid']).count()
	else:
		info["count"]=Course.objects.count()

	info["max"]=10
	return info

def CourseCheckCname(request):
	global logger
	judgeCname = 0
	if request.method == 'POST':
		try:
			strCourseInfo = request.POST['name']
		except ValueError:
			logger.error("courses")
			raise Http404()
		cou = Course.objects.order_by("-id")
		for courses in cou:
			if strCourseInfo == courses.cname:
				judgeCname = 1
				break
		data={}
		data["judgeCname"] = judgeCname
		return HttpResponse(json.dumps(data))

	