#-*- coding: utf-8 -*- 

'''
文件实现的功能，以及实现的方法如下：
显示界面：
    基础题：调用mgrchoose方法，返回基础题html界面
    简答题：调用mgrask方法，返回简答题html界面
    技能题：调用mgrskill方法，返回技能题html界面
    渗透题：调用mgrinfiltration方法，返回渗透题html界面

添加：
    基础题：调用addchoose方法
    简答题：调用askadd方法
    技能题：调用addskill方法
    渗透题：调用addinfiltration方法

编辑：
    基础题：调用editchoose方法
    简答题：调用askedit方法
    技能题：调用editskill方法
    渗透题：调用editinfiltration方法
    
详情：
    基础题：调用chooseinfo方法
    简答题：调用askinfo方法
    技能题：调用skillinfo方法
    渗透题：调用infiltrationinfo方法
    
删除：
    基础题：调用delchoose方法
    简答题：调用askdel方法
    技能题：调用delskill方法
    渗透题：调用delinfiltration方法
'''

from django.shortcuts import render_to_response
from teachers.models import Teacher
from client.models import *
from questions.models import *

from papers.models import PaperQuestion
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import PageNotAnInteger, Paginator, InvalidPage, EmptyPage
import datetime
import json,os
import logging
from django.db.models import Q
from tsssite.settings import HERE

from adminsys.views import funcando

logger = logging.getLogger('mysite.log')

def mgrchoose(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        queselect=''
        querytext = ''
        questions = Question.objects.order_by('-id').filter(qtype='1')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        if 'questionselect' in request.GET:
                questions= Question.objects.order_by('-id').filter(qtype='1')
                querytext = request.GET.get("questionselect")
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(questions,10)
        try:
                questions_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                questions_list = paginator.page(paginator.num_pages)

        page_long = len(paginator.page_range)
        if page_long<=5:
                page_range = paginator.page_range[0:page_long]    
        else:
                if page<=3:
                    page_range = paginator.page_range[0:5]
                else:
                    if (page_long-page) >= 2:   
                        page_range = paginator.page_range[page-3:page+2]
                    else:
                        page_range = paginator.page_range[page_long-5:page_long] 

        return render_to_response('templates/questionchoose.html',{'page':page,'querytext':querytext,'page_long':page_long,'queselect':queselect,'questionls':questions_list,'questions':questions,'page_range':page_range},context_instance=RequestContext(request))

def mgrask(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        queselect=''
        querytext=''
        questions = Question.objects.order_by('-id').filter(qtype='4')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        if 'questionselect' in request.GET:
                questions= Question.objects.order_by('-id').filter(qtype='4')
                querytext = request.GET.get("questionselect")
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(questions,10)
        try:
                questions_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                questions_list = paginator.page(paginator.num_pages)
        
        page_long = len(paginator.page_range)
        if page_long<=5:
                page_range = paginator.page_range[0:page_long]    
        else:
                if page<=3:
                    page_range = paginator.page_range[0:5]
                else:
                    if (page_long-page) >= 2:   
                        page_range = paginator.page_range[page-3:page+2]
                    else:
                        page_range = paginator.page_range[page_long-5:page_long] 

        return render_to_response('templates/questionask.html',{'page':page,'querytext':querytext,'page_long':page_long,'queselect':queselect,'questionls':questions_list,'questions':questions,'page_range':page_range},context_instance=RequestContext(request))

def mgrskill(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        queselect=''
        querytext=''
        questions = Question.objects.order_by('-id').filter(qtype='2')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        if 'questionselect' in request.GET:
                questions= Question.objects.order_by('-id').filter(qtype='2')
                querytext = request.GET.get("questionselect")
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(questions,10)
        try:
                questions_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                questions_list = paginator.page(paginator.num_pages)
        
        page_long = len(paginator.page_range)
        if page_long<=5:
                page_range = paginator.page_range[0:page_long]    
        else:
                if page<=3:
                    page_range = paginator.page_range[0:5]
                else:
                    if (page_long-page) >= 2:   
                        page_range = paginator.page_range[page-3:page+2]
                    else:
                        page_range = paginator.page_range[page_long-5:page_long] 

        return render_to_response('templates/questionskill.html',{'page':page,'querytext':querytext,'page_long':page_long,'queselect':queselect,'questionls':questions_list,'questions':questions,'page_range':page_range},context_instance=RequestContext(request))

def mgrinfiltration(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        queselect=''
        querytext=''
        questions = Question.objects.order_by('-id').filter(qtype='3')
        if 'querytext' in request.GET and request.GET['querytext']:
                querytext = request.GET['querytext']
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext
        if 'questionselect' in request.GET:
                questions= Question.objects.order_by('-id').filter(qtype='3')
                querytext = request.GET.get("questionselect")
                questions=questions.filter(Q(qid__icontains=querytext)|Q(qtitle__icontains=querytext))
                queselect=querytext

        try:
                page = int(request.GET.get("page",1))
                if page < 1:
                        page = 1
        except ValueError:
                page = 1
        paginator = Paginator(questions,10)
        try:
                questions_list = paginator.page(page)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
                questions_list = paginator.page(paginator.num_pages)
        
        page_long = len(paginator.page_range)
        if page_long<=5:
                page_range = paginator.page_range[0:page_long]    
        else:
                if page<=3:
                    page_range = paginator.page_range[0:5]
                else:
                    if (page_long-page) >= 2:   
                        page_range = paginator.page_range[page-3:page+2]
                    else:
                        page_range = paginator.page_range[page_long-5:page_long] 

        return render_to_response('templates/questioninfiltration.html',{'page':page,'querytext':querytext,'page_long':page_long,'queselect':queselect,'questionls':questions_list,'questions':questions,'page_range':page_range},context_instance=RequestContext(request)) 

def addskill(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')      
        questions = Question.objects.order_by('-id')
        judgeadd=0
        errors = []
        if request.method == 'POST':
                if not request.POST.get('qid',''):
                        errors.append('qid')
                for que in questions:
                        if que.qid==request.POST['qid']:
                                judgeadd=1
                                break;
                if(judgeadd==0):
                        que1 = Question(qid=request.POST['qid'], qtype='2', qtitle=request.POST['qtitle'], qscore=request.POST['qscore'],isfactory='1',teacherid_id=request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),times=0)
                        que1.save()
                        ski1 = Skill(link=request.POST['link'],result=request.POST['result'],queid_id=que1.id,topo=request.POST['hidTopo'])
                        ski1.save()

        questions = Question.objects.order_by('-id').filter(qtype='2')

        return HttpResponseRedirect('/questions/skill/')   

def editskill(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        questions= Question.objects.order_by('-id')
        judgeadd=0
        errors = ''
        try:
                did = int(did)
                que = Question.objects.get(id=did)   
                ski = Skill.objects.get(queid_id=que.id)
        except ValueError:
                logger.error("questions")
                raise Http404()                                     
        if request.method == 'POST':
                if not request.POST.get('qid',''):
                        errors.append('qid')
                for ques in questions:
                        if(ques.qid==request.POST['qid']):
                                if(ques.qid!=que.qid):
                                        judgeadd=1
                                        break;
                if(judgeadd==0):
                        que.qid=request.POST['qid']
                        que.qtitle=request.POST['qtitleedit']
                        que.qscore=request.POST['qscoreedit']
                        que.teacherid_id=request.session['userid']
                        que.edittime=datetime.datetime.now()
                        que.save()
                        ski.link=request.POST['linkedit']
                        ski.result=request.POST['resultedit']
                        ski.queid_id=que.id
                        ski.topo=request.POST['hidTopoedit']
                        ski.save()
        questions = Question.objects.order_by('-id').filter(qtype='2')
        return HttpResponseRedirect('/questions/skill/')
def checkquedel(request, did):
        global logger
        data={}
        result = 0
        data['cando'] = "true"

        try:
                q = Question.objects.get(id=did)

                cando = funcando(request,q.teacherid)
                if cando == "false":
                      data['cando'] = "false"
                      return HttpResponse(json.dumps(data))
                result = q.paperquestion_set.count()
        except:
                logger.error("get question failed")

        data["result"] = result
        return HttpResponse(json.dumps(data))

def instartexam(request):
        global logger
        result = 0
        data={}
        data['cando'] = "true"
        if request.method == 'POST':
                try:
                        queid = request.POST['queid']
                        q=Question.objects.get(id=queid)

                        cando = funcando(request,q.teacherid)
                        if cando == "false":
                                data['cando'] = "false"
                                return HttpResponse(json.dumps(data))

                        papers=q.paperquestion_set.all()
                        for p in papers:
                                exams=p.paperid.examinations_set.all()
                                for e in exams:
                                        if e.examStatus==1 or e.examStatus==2:
                                                result = 1
                                                data["result"] = result
                                                return HttpResponse(json.dumps(data))
                                atks= p.paperid.atkdfs_set.all()
                                for a in atks:
                                        if a.atkdfsStatus==1 or a.atkdfsStatus==2:
                                                result = 2
                                                data["result"] = result
                                                return HttpResponse(json.dumps(data))               
                except:
                        logger.error("get questionpaper in started examinations failed")
                data["result"] = result
                return HttpResponse(json.dumps(data))


def delskill(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                que = Question.objects.get(id=did)
        except ValueError:
                logger.error("questions")
                raise Http404()                
        if(did != 0):                
                ski = Skill.objects.get(queid_id=que.id)
                ski.delete()
                que.delete()
        questions = Question.objects.order_by('-id').filter(qtype='2')

        return HttpResponseRedirect('/questions/skill/')   

def skilllinkcheck(request):
        global logger

        questions = Question.objects.order_by('-id')
        if request.method == 'POST':
                try:
                        queid=request.POST['skiiddetail']


                except ValueError:
                        logger.error("questions")
                        raise Http404()
                que = Question.objects.get(id=queid)      
                skilllink = Skill.objects.get(queid_id=queid)
                
        data={}
        
        data["qid"] = que.qid
        data["qtitle"] = que.qtitle
        data["qscore"] = que.qscore
        data["result"] = skilllink.result
        data["link"] = skilllink.link

        data["topo"] = skilllink.topo


        return HttpResponse(json.dumps(data))

def getqtioninfo(request):
        qtinfo = None
        qtion = None
        ops = []
        data = {} 
        if request.method == 'POST':
                try:
                        queid = int(request.POST['qtionid'])/10
                        que = PaperQuestion.objects.get(id=queid)
                        que = Question.objects.get(id=que.questionid_id)
                        if que.qtype == '1':
                                qtinfo = Choose.objects.get(queid_id=que.id)
                                options = Option.objects.order_by('id').filter(choid_id=qtinfo.id)
                                if  options:
                                        for op in options:
                                                ops.append([op.content])
                                data["qtype"] = que.qtype
                                data["content"] = qtinfo.content
                                data['picdir'] = qtinfo.picturedir
                                data["options"] = ops
                        elif que.qtype == '2':
                                qtinfo = Skill.objects.get(queid_id=que.id)
                                data["qtype"] = que.qtype
                                data["qtitle"] = que.qtitle
                                data["link"] = qtinfo.link

                        elif que.qtype == '3':
                                qtinfo = Infiltration.objects.get(queid_id=que.id)
                                data["qtype"] = que.qtype                                
                                data["qtitle"] = que.qtitle
                                data["link"] = qtinfo.link
                        elif que.qtype == '4':
                                qtinfo = Ask.objects.get(queid_id=que.id)
                                data["qtype"] = que.qtype                                
                                data["qtitle"] = que.qtitle
                                data["content"] = qtinfo.content
                                data["conpic"] = qtinfo.contentpic

                                
                except ValueError:
                        logger.error("questions")
                        raise Http404()
        
        return HttpResponse(json.dumps(data))

def skillinfo(request):
        global logger
        que = ''
        if request.method == 'POST':
                try:
                        queid = request.POST['queid']
                        que = Question.objects.get(id=queid)
                        ski = Skill.objects.get(queid_id=que.id)
                except ValueError:
                        logger.error("questions")
                        raise Http404()                                
        data = {}
        data["qid"] = que.qid
        data["qtitle"] = que.qtitle
        data["qscore"] = que.qscore
        data["result"] = ski.result
        data["link"] = ski.link
        data["topo"] = ski.topo

        return HttpResponse(json.dumps(data))

def chooseinfo(request):
        global logger
        que = ''
        ops=[]
        if request.method == 'POST':
                try:
                        queid = request.POST['queid']
                        que = Question.objects.get(id=queid)
                        cho = Choose.objects.get(queid_id=que.id)
                        options = Option.objects.order_by('id').filter(choid_id=cho.id)
                except ValueError:
                        logger.error("questions")
                        raise Http404()       
                for op in options:
                        ops.append([op.content,op.isresult])

        data = {}
        data["qid"] = que.qid
        data["qtitle"] = que.qtitle
        data["qscore"] = que.qscore
        data["content"] = cho.content
        data['picdir'] = cho.picturedir
        data["options"] = ops
        
        return HttpResponse(json.dumps(data))

def addinfiltration(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')      
        questions = Question.objects.order_by('-id')
        judgeadd=0
        errors = []
        if request.method == 'POST':
                if not request.POST.get('qid',''):
                        errors.append('qid')
                for que in questions:
                        if que.qid==request.POST['qid']:
                                judgeadd=1
                                break;
                if(judgeadd==0):
                        que1 = Question(qid=request.POST['qid'], qtype='3', qtitle=request.POST['qtitle'], qscore=request.POST['qscore'],isfactory='1',teacherid_id=request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),times=0)
                        que1.save()
                        ski1 = Infiltration(link=request.POST['link'],result=request.POST['result'],queid_id=que1.id,topo=request.POST['hidTopo'])
                        ski1.save()

        questions = Question.objects.order_by('-id').filter(qtype='3')

        return HttpResponseRedirect('/questions/infiltration/')   

def editinfiltration(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        questions= Question.objects.order_by('-id')
        judgeadd=0
        errors = ''
        try:
                did = int(did)
                que = Question.objects.get(id=did)   
                ski = Infiltration.objects.get(queid_id=que.id)
        except ValueError:
                logger.error("questions")
                raise Http404()                                     
        if request.method == 'POST':
                if not request.POST.get('qid',''):
                        errors.append('qid')
                for ques in questions:
                        if(ques.qid==request.POST['qid']):
                                if(ques.qid!=que.qid):
                                        judgeadd=1
                                        break;
                if(judgeadd==0):
                        que.qid=request.POST['qid']
                        que.qtitle=request.POST['qtitleedit']
                        que.qscore=request.POST['qscoreedit']
                        que.teacherid_id=request.session['userid']
                        que.edittime=datetime.datetime.now()
                        que.save()
                        ski.link=request.POST['linkedit']
                        ski.result=request.POST['resultedit']
                        ski.queid_id=que.id
                        ski.topo=request.POST['hidTopoedit']
                        ski.save()
        questions = Question.objects.order_by('-id').filter(qtype='3')
        return HttpResponseRedirect('/questions/infiltration/')

def delinfiltration(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        try:
                did = int(did)
                que = Question.objects.get(id=did)
                
        except ValueError:
                logger.error("questions")
                raise Http404()                
        if(did != 0):                
                ski = Infiltration.objects.get(queid_id=que.id)
                ski.delete()
                que.delete()
        questions = Question.objects.order_by('-id').filter(qtype='3')

        return HttpResponseRedirect('/questions/infiltration/')   

def infiltrationlinkcheck(request):
        global logger
        
        questions = Question.objects.order_by('-id')
        
        if request.method == 'POST':
                try:
                        queid=request.POST['queid']
                        que = Question.objects.get(id=queid)

                        ski = Infiltration.objects.get(queid_id=que.id)
                except ValueError:
                        logger.error("questions")
                        raise Http404()      
        data={}

        data["qid"] = que.qid
        data["qtitle"] = que.qtitle
        data["qscore"] = que.qscore
        data["result"] = ski.result
        data["link"] = ski.link
        data["topo"] = ski.topo
        return HttpResponse(json.dumps(data))

def infiltrationinfo(request):
        global logger
        que = ''
        if request.method == 'POST':
                try:
                        queid = request.POST['queid']
                        que = Question.objects.get(id=queid)
                        ski = Infiltration.objects.get(queid_id=que.id)
                except ValueError:
                        logger.error("questions")
                        raise Http404()                                
        data = {}
        data["qid"] = que.qid
        data["qtitle"] = que.qtitle
        data["qscore"] = que.qscore
        data["result"] = ski.result
        data["link"] = ski.link
        data["topo"] = ski.topo
        return HttpResponse(json.dumps(data))

def addchoose(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')      
        questions = Question.objects.order_by('-id')
        judgeadd=0
        errors = []
        opt=[]
        if request.method == 'POST':
                if not request.POST.get('qid',''):
                        errors.append('qid')
                for que in questions:
                        if que.qid==request.POST['qid']:
                                judgeadd=1
                                que1 = que
                                break;
                if(judgeadd==0):
                        que1 = Question(qid=request.POST['qid'], qtype='1', qtitle=request.POST['qtitle'], qscore=request.POST['qscore'],isfactory='1',teacherid_id=request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),times=0)
                        que1.save()

                        mfile = None
                        filep = None
                        if 'addpic' in request.FILES:
                                path =os.path.join( HERE , 'document/choosepic/')
                                if not os.path.exists(path):
                                    os.makedirs(path)
                                mfile = request.FILES['addpic']
                                filepath = path+str(que1.id)+'_'+str(mfile)
                                f = handle_uploaded_file(mfile,filepath)
                        if mfile:
                            filep= 'document/choosepic/'+str(que1.id)+'_'+str(mfile)

                        cho = Choose(content=request.POST['choosecontent'],picturedir=filep,queid_id=que1.id)
                        cho.save()
                        optionnumber= int(request.POST['itemnumber'])

                        
                        for var in range(1,optionnumber+1):
                                opt1 = Option(oid=str(var),content=request.POST['item'+str(var)],isresult='0',choid_id=cho.id)
                                opt1.save()
                                opt.append(opt1)

                        choresult=request.REQUEST.getlist('resultcheck')
                        for chor in choresult:
                                opt[int(chor)-1].isresult='1'
                                opt[int(chor)-1].save()

        questions = Question.objects.order_by('-id').filter(qtype='1')

        return HttpResponseRedirect('/questions/choose/')   
def handle_uploaded_file(f,path):
  with open(path, 'wb+') as info:
    for chunk in f.chunks():
      info.write(chunk)
  return f
def delchoose(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        options=[]
        try:
                did = int(did)
                que = Question.objects.get(id=did)
        except ValueError:
                logger.error("questions")
                raise Http404()                
        if(did != 0):                
                cho = Choose.objects.get(queid_id=que.id)
                options= Option.objects.order_by('id').filter(choid_id=cho.id)
                for op in options:
                        op.delete()
                picdir = cho.picturedir
                if picdir:
                        cmd="rm -rf "+os.path.join( HERE , picdir.encode("utf8"))
                        os.system(cmd)
                cho.delete()
                que.delete()
        questions = Question.objects.order_by('-id').filter(qtype='1')

        return HttpResponseRedirect('/questions/choose/')   

def editchoose(request, did):
        global logger
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        error = ''
        options=[]
        opt=[]
        try:
                did = int(did)
                que = Question.objects.get(id=did)
        except ValueError:
                logger.error("questions")
                raise Http404()                
        if(did != 0):                
                cho = Choose.objects.get(queid_id=que.id)
                options= Option.objects.order_by('id').filter(choid_id=cho.id)
                for op in options:
                        op.delete()
                que.qid=request.POST['qid']
                que.qtitle=request.POST['qtitle']
                que.qscore=request.POST['qscore']
                que.edittime=datetime.datetime.now()
                que.save()

                if 'editpic' in request.FILES:
                    mfile=None
                    filep=None
                    cp = cho.picturedir
                    if cp:
                        cmd="rm -rf "+os.path.join( HERE , cp.encode('utf8'))
                        os.system(cmd)
                    if not os.path.isdir("document/choosepic"):
                        comd = "mkdir document/choosepic"
                        os.system(comd)
                    path =os.path.join( HERE , 'document/choosepic/')
                    mfile = request.FILES['editpic']
                    filepath = path+str(que.id)+'_'+str(mfile)
                    f = handle_uploaded_file(mfile,filepath)
                    if mfile:
                        filep= 'document/choosepic/'+str(que.id)+'_'+str(mfile)
                    cho.picturedir = filep

                cho.content=request.POST['choosecontent']
                cho.save()
                optionnumber= int(request.POST['itemnumber'])
                for var in range(1,optionnumber+1):
                       
                        opt1 = Option(oid=str(var),content=request.POST['item'+str(var)+'edit'],isresult='0',choid_id=cho.id)
                        opt1.save()
                        opt.append(opt1)
                choresult=request.REQUEST.getlist('resultcheck')
                for chor in choresult:
                        opt[int(chor)-1].isresult='1'
                        opt[int(chor)-1].save()
                
        questions = Question.objects.order_by('-id').filter(qtype='1')

        return HttpResponseRedirect('/questions/choose/')   

def qidcheck(request):
        global logger
        questions = Question.objects.order_by('-id')
        judgeqid = 0
        if request.method == 'POST':
                try:
                        queid=request.POST['qid']
                except ValueError:
                        logger.error("questions")
                        raise Http404()                                 
                for que in questions:
                        if (que.qid == queid):
                                judgeqid=1
                                break
        data={}
        data["judgeqid"]=judgeqid
        return HttpResponse(json.dumps(data))

def askadd(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    questions = Question.objects.order_by('-id')
    judgeadd=0
    errors = []
    if request.method == 'POST':
        if not request.POST.get('qid',''):
            errors.append('qid')
        for que in questions:
            if que.qid==request.POST['qid']:
                que1 = que
                judgeadd=1
                break;
        if(judgeadd==0):
                que1 = Question(qid=request.POST['qid'], qtype='4', qtitle=request.POST['qtitle'], qscore=request.POST['qscore'],isfactory='1',teacherid_id=request.session['userid'],createtime=datetime.datetime.now(),edittime=datetime.datetime.now(),times=0)
                que1.save()

                conmfile = None
                confilep = None
                remfile = None
                refilep = None
                if 'addconpic' in request.FILES:

                    path =os.path.join( HERE , 'document/askconpic/')
                    if not os.path.exists(path):
                        os.makedirs(path)
                    conmfile = request.FILES['addconpic']
                    filepath = path+str(que1.id)+'_'+str(conmfile)
                    f = handle_uploaded_file(conmfile,filepath)
                if conmfile:
                    confilep= 'document/askconpic/'+str(que1.id)+'_'+str(conmfile)

                if 'addrepic' in request.FILES:
                    path =os.path.join( HERE , 'document/askrepic/')
                    if not os.path.exists(path):
                        os.makedirs(path)
                    remfile = request.FILES['addrepic']
                    filepath = path+str(que1.id)+'_'+str(remfile)
                    f = handle_uploaded_file(remfile,filepath)
                if remfile:
                    refilep= 'document/askrepic/'+str(que1.id)+'_'+str(remfile)

                ask = Ask(content=request.POST['addcontent'],contentpic=confilep,result=request.POST['addresult'],resultpic=refilep,queid_id=que1.id)
                ask.save()

    questions = Question.objects.order_by('-id').filter(qtype='4')

    return HttpResponseRedirect('/questions/ask/')

def askdel(request,did):
    global logger
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    error = ''
    try:
        did = int(did)
        que = Question.objects.get(id=did)
    except ValueError:
        logger.error("questions")
        raise Http404()                
    if(did != 0):                
        ask = Ask.objects.get(queid_id=que.id)
        cp = ask.contentpic
        rp = ask.resultpic
        if cp:
            cmd="rm -rf "+os.path.join( HERE , cp.encode('utf-8'))
            os.system(cmd)
        if rp:
            cmd="rm -rf "+os.path.join( HERE , rp)
            print cmd
            os.system(cmd)
        ask.delete()
        que.delete()

    questions = Question.objects.order_by('-id').filter(qtype='4')

    return HttpResponseRedirect('/questions/ask/')
def askinfo(request):
    global logger
    que = ''
    if request.method == 'POST':
        try:
            queid = request.POST['queid']
            que = Question.objects.get(id=queid)
            ask = Ask.objects.get(queid_id=que.id)
        except ValueError:
            logger.error("questions")
            raise Http404()                                
    data = {}
    data["qid"] = que.qid
    data["qtitle"] = que.qtitle
    data["qscore"] = que.qscore
    data["qcontent"] = ask.content
    data["qresult"] = ask.result
    data["contentpic"] = ask.contentpic
    data["resultpic"] = ask.resultpic

    return HttpResponse(json.dumps(data))
def askedit(request,did):
    global logger
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    try:
        did = int(did)
    except ValueError:
        logger.error("questions")
        raise Http404()
    que = Question.objects.get(id=did)
    # que.qid=request.POST['qidedit']
    que.qtitle=request.POST['qtitleedit']
    que.qscore=request.POST['qscoreedit']
    que.edittime=datetime.datetime.now()
    que.save()           
    if did != 0:
        ask = Ask.objects.get(queid_id=que.id)
        ask.content = request.POST['editcontent']
        ask.result = request.POST['editresult']

        conmfile = None
        confilep = None
        remfile = None
        refilep = None
        print "eeeeeeeeeeeeeeeeeeeeeee"
        print request.FILES
        if 'editconpic' in request.FILES:
            cp = ask.contentpic
            if cp:
                cmd="rm -rf "+os.path.join( HERE , cp.encode('utf8'))
                os.system(cmd)

            path =os.path.join( HERE , 'document/askconpic/')
            if not os.path.exists(path):
                os.makedirs(path)
            conmfile = request.FILES['editconpic']
            filepath = path+str(que.id)+'_'+str(conmfile)
            f = handle_uploaded_file(conmfile,filepath)
            if conmfile:
                confilep= 'document/askconpic/'+str(que.id)+'_'+str(conmfile)
            ask.contentpic = confilep

        if 'editrepic' in request.FILES:
            re = ask.resultpic
            if re:
                cmd="rm -rf "+os.path.join( HERE , re)
                os.system(cmd)


            path =os.path.join( HERE , 'document/askrepic/')
            if not os.path.exists(path):
                os.makedirs(path)
            remfile = request.FILES['editrepic']
            filepath = path+str(que.id)+'_'+str(remfile)
            f = handle_uploaded_file(remfile,filepath)
            if remfile:
                refilep= 'document/askrepic/'+str(que.id)+'_'+str(remfile)
            ask.resultpic = refilep

        ask.save()
    questions = Question.objects.order_by('-id').filter(qtype='4')

    return HttpResponseRedirect('/questions/ask/')   
