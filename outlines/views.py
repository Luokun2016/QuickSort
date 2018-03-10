# -*- coding: UTF-8 -*-
''' 完成对实验大纲的增删改查操作 '''

# Create your views here.
from django.shortcuts import render_to_response
from teachers.models import Teacher
from outlines.models import Outline,Chapter,Outlinerelation,Exprelation
from client.models import *
from courses.models import *
from experiments.models import Experiment
from vms.models import Vm
from devices.models import Device
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import datetime
import json
import logging
from django.db.models import Q
from adminsys.views import funcando
from client.views import decorator,clientindex
from adminsys.views import add_record

logger = logging.getLogger('mysite.log')
def mgroutline(request):
        outselect=''
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        outs = Outline.objects.order_by('-id')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                outs=outs.filter(Q(onname__icontains=querytext))
                outselect=querytext
        if 'outlineselect' in request.GET:
                outs= Outline.objects.order_by('-id')
                querytext = request.GET.get("outlineselect")
                outs=outs.filter(Q(onname__icontains=querytext))
                outselect=querytext
        after_range_num=10
        befor_range_num=4
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(outs,10)
        try:
                outs_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                outs_list = paginator.page(paginator.num_pages)
        if page >= after_range_num:
                page_range = paginator.page_range[page-after_range_num:page+befor_range_num]
        else:
                page_range = paginator.page_range[0:int(page)+befor_range_num]
        add_record(request.session['useraccount'], u"访问实验大纲", 1)
        return render_to_response('templates/outline.html',{'outselect':outselect,'outs':outs,'outlines':outs_list,'page_range':page_range,'page':page}, context_instance=RequestContext(request))
			
def addoutline(request): 
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        outs = Outline.objects.order_by('-id')
        outlineinformation=[]
        outDetails=[]
        outl=[]
        if request.method == 'POST':
                if not request.POST.get('outlinestring',''):
                        errors.append('outlinestring')
                outlinestring = request.POST['outlinestring']
                if(outlinestring == 'null'):                      
                        ou = Outline(onid=request.POST['txtBH'],onname=request.POST['txtName'],remark=request.POST['txtremark'],teacherid_id =  request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
                        ou.save()
                else:
                        ou = Outline(onid=request.POST['txtBH'],onname=request.POST['txtName'],remark=request.POST['txtremark'],teacherid_id=  request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now())
                        ou.save()   
                        outlineinformation = outlinestring.split('@@') 
                        outlinelong = len(outlineinformation)
                        for outinfor in outlineinformation:
                                outDetails = outinfor.split('$$')

                                if(outDetails[1] == '0'):
                                        chs = Chapter(capname = outDetails[2])
                                        chs.save() 
                                        outDetails.append(chs)
                                        if(outDetails[3] == '0'):
                                                out =  Outlinerelation(outlineid_id=ou.id,chapterid_id=chs.id)
                                                out.save()
                                        else:
                                                for  outfor in outl:
                                                        if(outfor[0] == outDetails[3]):
                                                                par = outfor[4].id
                                                                break
                                                out = Outlinerelation(outlineid_id=ou.id,chapterid_id=chs.id,parentid_id=par)
                                                out.save()



                                else:
                                        exp =Exprelation(exp_id=int(outDetails[1]),expname = outDetails[2])
                                        exp.save() 
                                        outDetails.append(exp)
                                        if(outDetails[3] == '0'):
                                                out =  Outlinerelation(outlineid_id=ou.id,expid_id=exp.id)
                                                out.save()
                                        else:
                                                for  outfor in outl:
                                                        if(outfor[0] == outDetails[3]):
                                                                par = outfor[4].id
                                                                break
                                                out = Outlinerelation(outlineid_id=ou.id,expid_id=exp.id,parentid_id=par)
                                                out.save()


                                
                                outl.append(outDetails)
                        add_record(request.session['useraccount'], u"添加实验大纲："+request.POST['txtBH'], 1)
          
        return HttpResponseRedirect('/outlines/')

def editoutline(request,did): 
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                ou = Outline.objects.get(id=did)
        except ValueError:
                logger.error("outlines")
                raise Http404()
        if(did != 0):               
                outr = Outlinerelation.objects.order_by('-id')
                chap = Chapter.objects.order_by('-id')
                exp = Exprelation.objects.order_by('-id')
                for otr in outr:
                        if (otr.outlineid_id == ou.id):
                                if (otr.expid_id==None):
                                        for ch in chap:
                                                if (ch.id == otr.chapterid_id):
                                                        ch.delete()
                                else:
                                        for ex in exp:
                                                if(ex.id == otr.expid_id):
                                                        ex.delete()
                                otr.delete()           
        outs = Outline.objects.order_by('-id')
        outlineinformation=[]
        outDetails=[]
        outl=[]
        if request.method == 'POST':
                if not request.POST.get('outlinestring',''):
                        errors.append('outlinestring')
                outlinestring = request.POST['outlinestring']
                if(outlinestring == 'null'):
                        ou.onid = request.POST['txtBH']
                        ou.onname =   request.POST['txtName']  
                        ou.remark =   request.POST['txtremark']  
                        ou.edittime=datetime.datetime.now()
                        ou.save()                 
                else:
                        ou.onid = request.POST['txtBH']
                        ou.onname=   request.POST['txtName']  
                        ou.remark =   request.POST['txtremark']  
                        ou.edittime=datetime.datetime.now()
                        ou.save()                 
                        outlineinformation = outlinestring.split('@@') 
                        outlinelong = len(outlineinformation)
                        for outinfor in outlineinformation:
                                outDetails = outinfor.split('$$')
                                if(outDetails[1] == '0'):
                                        chs = Chapter(capname = outDetails[2])
                                        chs.save() 
                                        outDetails.append(chs)
                                        if(outDetails[3] == '0'):
                                                out =  Outlinerelation(outlineid_id=ou.id,chapterid_id=chs.id)
                                                out.save()
                                        else:
                                                for  outfor in outl:
                                                        if(outfor[0] == outDetails[3]):
                                                                par = outfor[4].id
                                                                break
                                                out = Outlinerelation(outlineid_id=ou.id,chapterid_id=chs.id,parentid_id=par)
                                                out.save()
                                else:
                                        exp =Exprelation(exp_id=outDetails[1],expname = outDetails[2])
                                        exp.save() 
                                        outDetails.append(exp)
                                        if(outDetails[3] == '0'):
                                                out =  Outlinerelation(outlineid_id=ou.id,expid_id=exp.id)
                                                out.save()
                                        else:
                                                for  outfor in outl:
                                                        if(outfor[0] == outDetails[3]):
                                                                par = outfor[4].id
                                                                break
                                                out = Outlinerelation(outlineid_id=ou.id,expid_id=exp.id,parentid_id=par)
                                                out.save()                              
                                outl.append(outDetails)
        add_record(request.session['useraccount'], u"编辑实验大纲："+ou.onid, 1)
        return HttpResponseRedirect('/outlines/')
def candeloutline(request, did):
       data={}
       data['cando'] = "true"

       try:
                did = int(did)
                out = Outline.objects.get(id=did)
       except ValueError:
                logger.error("outlines")
                raise Http404()
       cando = funcando(request,out.teacherid)
       if cando == "false":
            data['cando'] = "false"
       return HttpResponse(json.dumps(data))

def selectoutline(request,did):
    data={}
    data['select'] = "false"
    try:
        did = int(did)
        cour=Course.objects.filter(outlineid_id = did)
        if cour:
            data['select'] = "true"
        else:
            pass
    except ValueError:
                logger.error("outlines")
                raise Http404()
    return HttpResponse(json.dumps(data))


@decorator('outline')
def deloutline(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                out = Outline.objects.get(id=did)
        except ValueError:
                logger.error("outlines")
                raise Http404()                
        if(did != 0):                
                outr = Outlinerelation.objects.order_by('-id')
                chap = Chapter.objects.order_by('-id')
                exp = Exprelation.objects.order_by('-id')
                for otr in outr:
                        if (otr.outlineid_id == out.id):
                                if (otr.expid_id==None):
                                        for ch in chap:
                                                if (ch.id == otr.chapterid_id):
                                                        ch.delete()
                                else:
                                        for ex in exp:
                                                if(ex.id == otr.expid_id):
                                                        ex.delete()
                                otr.delete()

                out.delete()
                add_record(request.session['useraccount'], u"删除实验大纲："+out.onid, 1)
        outs = Outline.objects.order_by('-id')

        return HttpResponseRedirect('/outlines/')   

def outlineinfo(request):
        global logger
        data = {}
        data['cando'] = "true"

        out = ''
        if request.method == 'POST':
                try:
                        outid = request.POST['outid']
                        out = Outline.objects.get(id=outid)
                        cando = funcando(request,out.teacherid)
                        if cando == "false":
                            data['cando'] = "false"
                            return HttpResponse(json.dumps(data))
                except ValueError:
                        logger.error("outlines")
                        raise Http404()               
             
        data["outid"] = out.onid
        data["onname"] = out.onname
   #     data["teacher"] = out.teacherid.teaname
        data["isdefaultoutline"] = out.isdefaultoutline
        data["remark"] = out.remark

        return HttpResponse(json.dumps(data))

def outlineinfoDetails(request):
        global logger
        outlinerelation = Outlinerelation.objects.order_by('id')
        out = ''
        if request.method == 'POST':
                try:
                        outid = request.POST['outidDetail']
                        out = Outline.objects.get(id=outid)
                except ValueError:
                        logger.error("outlines")
                        raise Http404()                        
        treedetail = {}
        tree = []
        detail=[]
        for  outrela in outlinerelation:
                if (outrela.outlineid_id == out.id):
                        if(outrela.expid_id == None):
                                detail=[str(outrela.chapterid_id),outrela.chapterid.capname,str(outrela.parentid_id),0]
                                tree.append(detail)
                        else:
                                detail=[0,outrela.expid.expname,str(outrela.parentid_id),str(outrela.expid.exp_id)]
                                tree.append(detail)
        treedetail["key"] = tree

        return HttpResponse(json.dumps(treedetail))

#question about course tree doesn't exist
def outtreeDetails(request):
        global logger
        outlinerelation = Outlinerelation.objects.order_by('id')
        out = ''
        if request.method == 'POST':
                try:
                        outid = request.POST['selcourse']
                        out = Outline.objects.get(id=outid)
                except ValueError:
                        logger.exception("outlines")
                        raise Http404()                             
        treedetail = {}
        tree = []
        detail=[]
        for  outrela in outlinerelation:
                if (outrela.outlineid_id == out.id):
                        # print ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
                        if(outrela.expid_id == None):
                                # print "00000000000000000000000000000000000"
                                detail=[str(outrela.chapterid_id),outrela.chapterid.capname,str(outrela.parentid_id),0,0,'0','0','0','0']
                                tree.append(detail)
                        else:
                                # print outrela.expid_id
                                # print outrela.expid.exp
                                # print outrela.expid.exp.elements
                                # if 'cuserid' in request.session:
                                #     try:
                                #         client = Client.objects.get(studentid=request.session['cuserid'])
                                #         if client.copytopo and client.expid_id ==outrela.expid_id:
                                #             tp = client.copytopo
                                #         else:
                                #             tp = outrela.expid.exp.topo
                                #     except:
                                #         tp = outrela.expid.exp.topo
                                # else:
                                tp = outrela.expid.exp.topo

                                detail=[0,outrela.expid.expname,str(outrela.parentid_id),str(outrela.expid.exp_id),str(outrela.expid_id),outrela.expid.exp.elements,outrela.expid.exp.step,outrela.expid.exp.tool,outrela.expid.exp.video,tp]
                                tree.append(detail)
        treedetail["key"] = tree
        return HttpResponse(json.dumps(treedetail))


def outlineExp(request):
        treedetail = {}
        tree = []
        detail=[]
        experiments = Experiment.objects.order_by('id')
        for  exp in experiments:
                detail = [str(exp.id),exp.name,str(exp.parent_id),exp.isFolder]
                tree.append(detail)
        treedetail["key"] = tree
        return HttpResponse(json.dumps(treedetail))

def outlineOnname(request):
        global logger
        outlines = Outline.objects.order_by('-id')
        judgeonname = 0
        if request.method == 'POST':
                try:
                        outonname=request.POST['txtName']                       
                except ValueError:
                        logger.error("outlines")
                        raise Http404()                             
                for out in outlines:
                        if (out.onname == outonname):
                                judgeonname = 1
                                break
        data={}
        data["judgeonname"]=judgeonname
        return HttpResponse(json.dumps(data))

def outlineOnid(request):
        global logger
        outlines = Outline.objects.order_by('-id')
        judgeonid = 0
        if request.method == 'POST':
                try:
                        outonid=request.POST['txtBH']
                except ValueError:
                        logger.error("outlines")
                        raise Http404()                             
                for out in outlines:
                        if (out.onid == outonid):
                                judgeonid = 1
                                break
        data={}
        data["judgeonid"]=judgeonid
        return HttpResponse(json.dumps(data))

def teacheridcheck(request):
        global logger
        if request.method == 'POST':
                try:
                        outid=request.POST['outid']
                        out = Outline.objects.get(id=outid)
                except ValueError:
                        logger.error("outlines")
                        raise Http404()                                               
        data={}
        data["teacherid"]=out.teacherid_id
        return HttpResponse(json.dumps(data))

