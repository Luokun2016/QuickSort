# -*- coding: UTF-8 -*-
#实验体系模块功能文件，完成对实验的增删该查操作
# Create your views here.
from django.shortcuts import render_to_response
from teachers.models import Teacher
from experiments.models import  *
from outlines.models import Exprelation
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from courses.models import *
from vgates.models import *
from vms.models import *
from vswitches.models import *
from devices.models import *
from myexp.models import *
from tsssite.settings import HERE
import json
import time, os,os.path, shutil
import datetime
import zipfile
import logging
import re
from adminsys.views import funcando
from adminsys.views import add_record

logger = logging.getLogger('mysite.log')
# 获取页面展示信息
def mgrexperiment(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        treedetail = {}
        tree = []
        detail=[]
        experiments = Experiment.objects.order_by('id')
        for  exp in experiments:
                detail = [str(exp.id),exp.name,str(exp.parent_id),exp.isFolder]
                tree.append(detail)
        treedetail["key"] = tree
        add_record(request.session['useraccount'], u"访问实验体系", 1)
        return render_to_response('templates/experiments.html',{'experiments': experiments,'tree1':json.dumps(treedetail)}, context_instance=RequestContext(request))
# 恢复出厂功能
def resetexp(request):
        global logger
        result = 0
        if request.method == 'POST':
                try:
                        expid = int(request.POST['hidId'])
                        try:
                                expbak = ExperimentBak.objects.get(id=expid)
                                exp = Experiment.objects.get(id=expid).updateFromBak(expbak)
                        except:
                                result = 1
                                return HttpResponse(result)
                except ValueError:
                        logger.error("experiments")
                        raise Http404()
                        
                pathbakzip = os.path.join( HERE , 'document/elesbak/')
                pathbakzip = pathbakzip + str(expid)+'/eles.pdf'
                path = os.path.join( HERE , 'document/eles/')
                path = path + str(expid)
                cmd = 'rm -rf '+path+'/*'
                os.system(cmd)
                pathzip = path +'/eles.pdf'
                if os.path.exists(pathbakzip) and os.path.exists(path):
                    shutil.copyfile(pathbakzip, pathzip)
                    # unzip_file(pathzip,path)

                pathbakzip = os.path.join( HERE , 'document/stepsbak/')
                pathbakzip = pathbakzip + str(expid)+'/steps.pdf'
                path = os.path.join( HERE , 'document/steps/')
                path = path + str(expid)
                cmd = 'rm -rf '+path+'/*'
                os.system(cmd)
                pathzip = path +'/steps.pdf'
                if os.path.exists(pathbakzip) and os.path.exists(path):
                    shutil.copyfile(pathbakzip, pathzip)
                    # unzip_file(pathzip,path)


                pathbakzip = os.path.join( HERE , 'document/toolsbak/')
                pathbakzip = pathbakzip + str(expid)+'/tools.zip'
                path = os.path.join( HERE , 'document/tools/')
                path = path + str(expid)
                cmd = 'rm -rf '+path+'/*'
                os.system(cmd)
                pathzip = path +'/tools.zip'
                if os.path.exists(pathbakzip) and os.path.exists(path):
                    shutil.copyfile(pathbakzip, pathzip)
                    unzip_file(pathzip,path)


                pathbakzip = os.path.join( HERE , 'document/videosbak/')
                pathbakzip = pathbakzip + str(expid)+'/videos.zip'
                path = os.path.join( HERE , 'document/videos/')
                path = path + str(expid)
                cmd = 'rm -rf '+path+'/*'
                os.system(cmd)
                pathzip = path +'/videos.zip'
                if os.path.exists(pathbakzip) and os.path.exists(path):
                    shutil.copyfile(pathbakzip, pathzip)
                    unzip_file(pathzip,path)

                return HttpResponse(result)
# 保存实验
def saveexperiment(request):
        global logger
        if request.method == 'POST':
                try:
                        expid = int(request.POST['hidId'])
                        exp = Experiment.objects.get(id=expid)
                        exp.name = request.POST['txtName']
                        exp.code = request.POST['txtCode']
                        exp.speciality = request.POST['txtSpeciality']
                        exp.remark = request.POST['txtRemark']
                        exp.description = request.POST['txtDescription']
                except ValueError:
                        logger.error("experiments")
                        raise Http404()                                    
                #exp.topo = request.POST['topo']
                #exp.elements = request.POST['elements']
                #exp.step = int(request.POST['txtStep'])
                #exp.createDate = request.POST['txtCreateDate']
                #exp.createUser = int(request.POST['vmtype'])

                result = exp.save()
                add_record(request.session['useraccount'], u"实验:"+exp.name+u",保存基本信息", 1)
        return HttpResponse(result)
# 保存目录节点
def savenode(request):
        global logger
        if request.method == 'POST':
                if 'nodetitle' in request.POST:
                        try:
                                nodetitle = request.POST['nodetitle']
                                nodekey = int(request.POST['nodekey'])
                        except ValueError:
                                logger.error("experiments")
                                raise Http404()                        
                        
                        if request.POST['nodeisfolder'] == "true":
                                nodeisfolder = 1
                                add_record(request.session['useraccount'], u"实验体系添加目录："+request.POST['nodetitle'], 1)
                        else:
                                nodeisfolder = 0
                                add_record(request.session['useraccount'], u"实验体系添加实验："+request.POST['nodetitle'], 1)
                        
                        nodeparent = int(request.POST['nodeparent'])
                        
                        if nodekey > 0:
                                exp = Experiment.objects.get(id=nodekey)
                                exp.name=nodetitle
                        else:
                                exp = Experiment(
                                        name=nodetitle, 
                                        isFolder=nodeisfolder, 
                                        parent_id=nodeparent,
                                        createDate=time.strftime('%Y-%m-%d',time.localtime(time.time())),
                        
                                        createUser_id=request.session['userid'])
                        
                        if nodeisfolder == 1:
                        #限制实验体系目录名不相同或者不为空
                            isexp = Experiment.objects.filter(isFolder=1,name=nodetitle)
                            if isexp or nodetitle == '':
                                exp.id=-1
                                pass
                            else:
                                exp.save()
                        else:
                            exp.save()
        return HttpResponse(exp.id)
# 删除目录节点
def delnodecando(request, expid):
        data={}
        data['cando'] = "true"
        exp = Experiment.objects.get(id=expid)
        cando = funcando(request,exp.createUser)
        if cando == "false":
            data['cando'] = "false"
        return HttpResponse(json.dumps(data))

def getchildnode(request, expid):
        exp = Experiment.objects.filter(parent_id=expid)
        if len(exp)>0:
            hadnode=1
        else:
            hadnode=0
        data={}
        data['hadnode'] = hadnode
        return HttpResponse(json.dumps(data))

def testdel(request,expid):
        data={}
        out = Exprelation.objects.filter(exp_id=expid)
        if out:
            data["isexist"] = "true"
        else:
            data["isexist"] = "false"
        return HttpResponse(json.dumps(data))

def delnode(request, expid):
        data={}
        exp = Experiment.objects.get(id=expid)
        result = exp.delete()
        path = os.path.join( HERE , 'document/eles/')
        path = path + str(expid)
        if os.path.exists(path):
            shutil.rmtree(path)

        path = os.path.join( HERE , 'document/steps/')
        path = path + str(expid)
        if os.path.exists(path):
            shutil.rmtree(path)

        path = os.path.join( HERE , 'document/tools/')
        path = path + str(expid)
        if os.path.exists(path):
            shutil.rmtree(path)

        path = os.path.join( HERE , 'document/videos/')
        path = path + str(expid)
        if os.path.exists(path):
            shutil.rmtree(path)

        add_record(request.session['useraccount'], u"实验体系删除节点："+exp.name, 1)
        return HttpResponse(data)

def elesdel(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/eles/')
        filename = path+ str(expid) +'/eles.pdf'
        try:
            exp = Experiment.objects.get(id=expid)
            exp.elements=""
            exp.save()
            if os.path.exists(filename):
                os.remove(filename)
                data["file"] = "true"
            else:
                print "not exists"
                data["file"] = "false"
        except:
            pass
        
        return HttpResponse(json.dumps(data))

def stepsdel(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/eles/')
        filename = path+ str(expid) +'/steps.pdf'
        try:
            exp = Experiment.objects.get(id=expid)
            exp.step=""
            exp.save()
            if os.path.exists(filename):
                os.remove(filename)
                data["file"] = "true"
            else:
                print "not exists"
                data["file"] = "false"
        except:
            pass
        return HttpResponse(json.dumps(data))
def toolsdel(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/eles/')
        path_file = path+ str(expid)
        filename = path+ str(expid) +'/tools.html'
        exp = Experiment.objects.get(id=expid)
        
        exp.tool=""
        exp.save()
        if os.path.exists(filename):
            # os.remove(filename)
            shutil.rmtree(path_file)
            data["file"] = "true"
        else:
            print "not exists"
            data["file"] = "false"
        return HttpResponse(json.dumps(data))
def videosdel(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/eles/')
        path_file = path+ str(expid)
        filename = path+ str(expid) +'/videos.html'
        exp = Experiment.objects.get(id=expid)
        exp.video=""
        exp.save()
        if os.path.exists(filename):
            shutil.rmtree(path_file)
            # os.remove(filename)
            data["file"] = "true"
        else:
            print "not exists"
            data["file"] = "false"
        return HttpResponse(json.dumps(data))

def elesinfo(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/eles/')
        filename = path+ str(expid) +'/eles.pdf'
        if os.path.exists(filename):
            data["isexist"] = "true"
        else:
            data["isexist"] = "false"
        return HttpResponse(json.dumps(data))

def stepsinfo(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/steps/')
        filename = path+ str(expid) +'/steps.pdf'
        if os.path.exists(filename):
            data["isexist"] = "true"
        else:
            data["isexist"] = "false"
        return HttpResponse(json.dumps(data))

def toolsinfo(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/tools/')

        filename = path+ str(expid) +'/tools.html'
        if os.path.exists(filename):
            data["isexist"] = "true"
        else:
            data["isexist"] = "false"
        return HttpResponse(json.dumps(data))

def videosinfo(request, expid):
        data = {}
        path = os.path.join( HERE , 'document/videos/')
        filename = path+ str(expid) +'/videos.html'
        if os.path.exists(filename):
            data["isexist"] = "true"
        else:
            data["isexist"] = "false"
        return HttpResponse(json.dumps(data))


def experimentinfo(request, expid):
        exp = Experiment.objects.get(id=expid)
        data = {}
        print exp.step
        data["id"] = exp.id
        #if exp.parent != None:
            #data["parent"] = exp.parent.id
        data["name"] = exp.name
        data["isFolder"] = exp.isFolder
        data["code"] = exp.code
        data["speciality"] = exp.speciality
        data["remark"] = exp.remark
        data["description"] = exp.description
        data["topo"] = exp.topo
        data["elementsType"] = exp.elementsType
        data["elements"] = exp.elements
        data["stepType"] = exp.stepType
        data["step"] = exp.step
        data["toolType"] = exp.toolType
        data["tool"] = exp.tool
        data["videoType"] = exp.videoType
        data["video"] = exp.video
        data["createDate"] = exp.createDate.strftime('%Y-%m-%d')
        data["createUser"] = exp.createUser.teaname
        return HttpResponse(json.dumps(data))

def savetopo(request, expid):
        global logger
        if request.method == 'POST':
                try:
                        expid = int(expid)
                        exp = Experiment.objects.get(id=expid)
                        exp.topo = request.POST['hidTopo']
                except ValueError:
                        logger.error("experiments")
                        raise Http404()
                
                result = exp.save()
                add_record(request.session['useraccount'], u"实验:"+exp.name+u",保存拓扑", 1)
        data={}
        data["topo"] = exp.topo
        # print json.dumps(data)
        return HttpResponse(json.dumps(data))
def savefile(request):
    global logger
    uploadError=0 
    if request.method == 'POST':
        try:
            outlid = int(request.POST['courseid'])
            expid = int(request.POST['experid'])
            cuexpid = int(request.POST['curexpid'])
            coursname = request.POST['coursename']
            stuname = request.FILES['thisfile']
        except:
            logger.error("experiments")
            raise Http404()
        #创建学生提交压缩包的主目录
        path_file = os.path.join( HERE , 'document/upfile/')
        cour = Course.objects.get(cname=coursname)
        #creat courses folder 
        path = path_file + str(cour.id)
        #根据课程ID创建目录
        if not os.path.exists(path):
            os.makedirs(path)
        #根据实验ID创建目录
        path = path + '/' + str(cuexpid)
        if not os.path.exists(path):
            os.makedirs(path)
        #拼装要上传文件的路径
        filepath = path + '/' + str(stuname)
        f = handle_uploaded_file(stuname,filepath)
        if f:
            uploadError = 1
    data={}
    data["finish"]=uploadError
    return HttpResponse(json.dumps(data))

def savetool(request):
        global logger
        uploadError=0                           
        if request.method == 'POST':
                try:
                        ht = request.POST['hidType']
                except ValueError:
                        logger.error("experiments")
                        raise Http404()
                path_file = os.path.join( HERE , 'document/')
                path_file = path_file + ht + 's/'
                path = './document/' + ht + 's/'
                if not os.path.exists(path_file):
                        os.makedirs(path_file)
                if ht == 'ele':
                        expid = int(request.POST['hidEleId'])
                        exp = Experiment.objects.get(id=expid)
                        exp.elementsType = request.POST['hidEleFileType']
                        add_record(request.session['useraccount'], u"实验:"+exp.name+u",上传实验原理", 1)
                        if exp.elementsType == '1':
                                mfile=request.FILES['fileEle']

                                # zp = zipfile.ZipFile(mfile,'r')  
                                # for filename in zp.namelist():
                                #     if re.search(u'.pdf$|.pdf$',filename):     
                                #         uploadError=1
                                fname = str(mfile)
                                if fname == "eles.pdf":
                                    uploadError=1
                                path = path + str(expid)
                                path_file = path_file + str(expid)
                                if os.path.exists(path_file):
                                        shutil.rmtree(path_file) 
                                if not os.path.exists(path_file):
                                        os.makedirs(path_file)
                                filepath =  path_file + '/' + ht + 's.pdf'
                                # print filepath
                                # print mfile
                                # print type(mfile)
                                if uploadError == 1:
                                    f = handle_uploaded_file(mfile,filepath)
                                #unzip_file(r'' + filepath,r'' + path_file)
                                exp.elements = path.lstrip('.') + '/eles.pdf'
                        else:
                                exp.elements = request.POST['txtEleURL']
                if ht == 'step':
                        expid = int(request.POST['hidStepId'])
                        exp = Experiment.objects.get(id=expid)
                        exp.stepType = request.POST['hidStepFileType']
                        add_record(request.session['useraccount'], u"实验:"+exp.name+u",上传实验步骤", 1)
                        if exp.stepType == '1':
                                mfile=request.FILES['fileStep']

                                # zp = zipfile.ZipFile(mfile,'r')  
                                # for filename in zp.namelist():
                                #     if re.search(u'.pdf$|.pdf$',filename):     
                                #         uploadError=1
                                fname = str(mfile)
                                if fname == "steps.pdf":
                                    uploadError=1
                                path = path + str(expid)
                                path_file = path_file + str(expid)

                                if os.path.exists(path_file):
                                        shutil.rmtree(path_file) 
                                if not os.path.exists(path_file):
                                        os.makedirs(path_file)
                                filepath =  path_file + '/' + ht + 's.pdf'
                                if uploadError == 1:
                                    f = handle_uploaded_file(mfile,filepath)
                                #unzip_file(r'' + filepath,r'' + path_file)
                                exp.step = path.lstrip('.') + '/steps.pdf'
                        else:
                                exp.step = request.POST['txtStepURL']

                if ht == 'tool':
                        expid = int(request.POST['hidToolId'])
                        exp = Experiment.objects.get(id=expid)
                        exp.toolType = request.POST['hidToolFileType']
                        add_record(request.session['useraccount'], u"实验:"+exp.name+u",上传实验工具", 1)
                        if exp.toolType == '1':
                                mfile=request.FILES['fileTool']

                                zp = zipfile.ZipFile(mfile,'r')  
                                for filename in zp.namelist():
                                    if re.search(u'.zip$',filename):     
                                        uploadError=1

                                path = path + str(expid)
                                path_file = path_file + str(expid)
                                if os.path.exists(path_file):
                                        shutil.rmtree(path_file) 
                                if not os.path.exists(path_file):
                                        os.makedirs(path_file)
                                filepath =  path_file + '/' + ht + 's.zip'
                                f = handle_uploaded_file(mfile,filepath)
                                unzip_file(r'' + filepath,r'' + path_file)
                                exp.tool = path.lstrip('.') + '/tools.html'
                        else:
                                exp.tool = request.POST['txtURL']

                if ht == 'video':
                        expid = int(request.POST['hidVideoId'])
                        exp = Experiment.objects.get(id=expid)
                        exp.videoType = request.POST['hidVideoFileType']
                        add_record(request.session['useraccount'], u"实验:"+exp.name+u",上传实验录像", 1)
                        if exp.videoType == '1':
                                mfile=request.FILES['fileVideo']

                                zp = zipfile.ZipFile(mfile,'r')  
                                for filename in zp.namelist():
                                    if re.search(u'.mp4$',filename):     
                                        uploadError=1

                                path = path + str(expid)
                                path_file = path_file + str(expid)
                                if os.path.exists(path_file):
                                        shutil.rmtree(path_file) 
                                if not os.path.exists(path_file):
                                        os.makedirs(path_file)
                                filepath =  path_file + '/' + ht + 's.zip'
                                f = handle_uploaded_file(mfile,filepath)
                                unzip_file(r'' + filepath,r'' + path_file)
                                exp.video = path.lstrip('.') + '/videos.html'
                        else:
                                exp.video = request.POST['txtVideoURL']
                #if uploadError==1:
        exp.save()
        data={}
        data["type"] = ht
        data["finish"]=uploadError
        return HttpResponse(json.dumps(data))

def handle_uploaded_file(f,path):
        with open(path, 'wb+') as info:
                for chunk in f.chunks():
                        info.write(chunk)
        return f

def unzipfile(file):
        cmd = 'unzip "%s"' % file
        exccmd = cmd.decode('UTF-8').encode('gbk')
        result = os.system(exccmd)
        return result

def unzip_file(zipfilename, unziptodir):
        if not os.path.exists(unziptodir):
            os.makedirs(unziptodir, 0777)
        zfobj = zipfile.ZipFile(zipfilename)
        for name in zfobj.namelist():
            name = name.replace('\\','/')
           
            if name.endswith('/'):
                os.makedirs(os.path.join(unziptodir, name))
            else:
                ext_filename = os.path.join(unziptodir, name)
                ext_dir= os.path.dirname(ext_filename)
                if not os.path.exists(ext_dir):
                    os.makedirs(ext_dir,0777)
                outfile = open(ext_filename, 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()

def initmyflowtools(request, expid):
        data = {}
        detail = []
        lists =[]
        imgls = Img.objects.order_by('-id')
        for  img in imgls:
                        dic_name = DicContent.objects.get(id=img.ostype_id).id
                        detail = [str(img.id), img.name, img.remark, dic_name]
                        lists.append(detail)
        data["imgls"] = lists


        lists =[]
        imgvgtls = ImgVgt.objects.order_by('-id')
        for  img in imgvgtls:
                        dic_name = DicContent.objects.get(id=img.vgttype_id).id
                        detail = [str(img.id), img.name, img.remark, dic_name]
                        lists.append(detail)
        data["imgvgtls"] = lists

        lists =[]
        imgvshls = ImgVsh.objects.order_by('-id')
        for  img in imgvshls:
                        dic_name = DicContent.objects.get(id=img.vshtype_id).id
                        detail = [str(img.id), img.name, img.remark, dic_name]
                        lists.append(detail)
        data["imgvshls"] = lists

        lists = []
        physics = Device.objects.order_by('-id')
        for p in physics:
                        detail = [str(p.id), p.devname, p.devtype]
                        lists.append(detail)
        data["physics"] = lists

        return HttpResponse(json.dumps(data))


def viewpdf(request):
    return render_to_response("templates/viewer.html")