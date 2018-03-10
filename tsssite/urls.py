#-*- coding: utf-8 -*- 
'''django框架中用于指定url与相应的处理函数'''

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tsssite.views.home', name='home'),
    # url(r'^tsssite/', include('tsssite.foo.urls')),

    url(r'^tools/', include('Tools.urls')),
    url(r'^showstate/', include('atkdfsshow.urls')),
    url(r'^experiment/', include('experiments.urls')),
    url(r'^questions/', include('questions.urls')),
    url(r'^notice/', include('notice.urls')),

    # url(r'^adminsys/', include('adminsys.urls')),

    #************************************************************************************
    # ================================================== --


    url(r'^$', 'tsssite.views.home'),
    url(r'^Login/','ulogin.views.loginIni'),
    url(r'^index/','ulogin.views.index'),

    url(r'^shutdown/','ulogin.views.shutdown'),
    url(r'^logout/','ulogin.views.logout'),
    url(r'^admin/','adminsys.views.sysadmin'),
    url(r'^seesight/','adminsys.views.seesight'),
    url(r'^realtimeinfor/','adminsys.views.realtimeinfor'),

    url(r'^devices/','devices.views.mgrdevice'),
    url(r'^devicenamecheck/','devices.views.devicenamecheck'),
    url(r'^deviceinfo/','devices.views.deviceinfo'),
    url(r'^devicedel/(\d+)/$','devices.views.deldevice'),
    url(r'^deviceadd/','devices.views.adddevice'),
    url(r'^deviceedit/','devices.views.editdevice'),


    url(r'^vms/','vms.views.mgrvm'),
    url(r'^vmnamecheck/','vms.views.vmnamecheck'),
    url(r'^vgavmnamecheckt/','vms.views.vgavmnamecheckt'), 
    url(r'^vmipnamecheck/','vms.views.vmipnamecheck'),
    url(r'^vmipnamecheckedit/','vms.views.vmipnamecheckedit'),
    url(r'^vminfo/','vms.views.vminfo'),
    url(r'^vmdel/(\d+)/$','vms.views.selectServerDelVM'),
    url(r'^vmedit/','vms.views.editvm'),
    url(r'^resetvm/','vms.views.resetvm'),

    url(r'^vmdetail/(\d+)/$','vms.views.instance'),
    url(r'^resdetail/(\d+)/$','vms.views.restance'),

    url(r'^info/vds/cpu/([\w\-\.]+)/$', 'vms.views.cpuusage', name='vdscpuusage'),
    url(r'^info/vds/memory/([\w\-\.]+)/$', 'vms.views.memusage', name='vdsmemusage'),
    url(r'^vmstart/(\d+)/$','vms.views.vmstart'),
    url(r'^vmstop/(\d+)/$','vms.views.vmstop'),
    url(r'^console/(\d+)/([\w\-\.]+)/$', 'vms.views.console', name='console'),
    url(r'^createvm/','vms.views.createvm'),
    url(r'^imgdel/(\d+)/$','vms.views.delimgall'),
    url(r'^imgdelall/(\d+)/$','vms.views.delimg'),
    url(r'^imgupload/','vms.views.uploadimg'),
    url(r'^imgadd/','vms.views.addimg'),
    url(r'^imginfo/','vms.views.imginfo'),
    url(r'^imgedit/','vms.views.editimg'),
    url(r'^deletefile/','vms.views.deletefile'),

    url(r'^vgates/','vgates.views.mgrvgates'),
    url(r'^vgtinfo/','vgates.views.vgtinfo'),
    url(r'^vgtdel/(\d+)/$','vgates.views.selectServerDelVgt'),
    url(r'^vgtedit/','vgates.views.editvgt'),
    url(r'^vgtdetail/(\d+)/$','vgates.views.instance'),
    url(r'^vgtstart/(\d+)/$','vgates.views.vmstart'),
    url(r'^vgtstop/(\d+)/$','vgates.views.vmstop'),
    url(r'^vganamecheck/','vgates.views.vganamecheck'),
    url(r'^vgavmnamecheck/','vgates.views.vgavmnamecheck'),
    url(r'^vgaipnamecheck/','vgates.views.vgaipnamecheck'),
    url(r'^vgaipnamecheckedit/','vgates.views.vgaipnamecheckedit'),
    url(r'^createvgt/','vgates.views.createvm'),
    url(r'^imgvgtdel/(\d+)/$','vgates.views.delimgvgtall'),
    url(r'^imgvgtdelall/(\d+)/$','vgates.views.delimgvgt'),
    url(r'^imgvgtadd/','vgates.views.addimgvgt'),
    url(r'^imgvgtinfo/','vgates.views.imgvgtinfo'),
    url(r'^imgvgtedit/','vgates.views.editimgvgt'),

    url(r'^vswitches/','vswitches.views.mgrvswitches'),
    url(r'^vshinfo/','vswitches.views.vshinfo'),
    url(r'^vshdel/(\d+)/$','vswitches.views.delvsh'),
    url(r'^vshedit/','vswitches.views.editvsh'),
    url(r'^vshdetail/(\d+)/$','vswitches.views.instance'),
    url(r'^vshstart/(\d+)/$','vswitches.views.vmstart'),
    url(r'^vshstop/(\d+)/$','vswitches.views.vmstop'),
    url(r'^imgvshdel/(\d+)/$','vswitches.views.delimgvsh'),
    url(r'^imgvshadd/','vswitches.views.addimgvsh'),
    url(r'^imgvshinfo/','vswitches.views.imgvshinfo'),
    url(r'^imgvshedit/','vswitches.views.editimgvsh'),
    
    url(r'^experiments/','experiments.views.mgrexperiment'),
    url(r'^experimentadd/','experiments.views.addexperment'),
    
    url(r'^resetexp/','experiments.views.resetexp'),
    url(r'^saveexperiment/','experiments.views.saveexperiment'),
    url(r'^savenode/','experiments.views.savenode'),
    url(r'^delnodecando/(\d+)/$','experiments.views.delnodecando'),
    url(r'^getchildnode/(\d+)/$','experiments.views.getchildnode'),
    
    url(r'^delnode/(\d+)/$','experiments.views.delnode'),
    url(r'^testdel/(\d+)/$','experiments.views.testdel'),
    url(r'^elesinfo/(\d+)/$','experiments.views.elesinfo'),
    url(r'^stepsinfo/(\d+)/$','experiments.views.stepsinfo'),
    url(r'^toolsinfo/(\d+)/$','experiments.views.toolsinfo'),
    url(r'^videosinfo/(\d+)/$','experiments.views.videosinfo'),
    url(r'^viewpdf/$','experiments.views.viewpdf'),

    # url(r'^elesdel/(\d+)/$','experiments.views.elesdel'),
    # url(r'^stepsdel/(\d+)/$','experiments.views.stepsdel'),
    # url(r'^toolsdel/(\d+)/$','experiments.views.toolsdel'),
    # url(r'^videodel/(\d+)/$','experiments.views.videosdel'),

    url(r'^experimentinfo/(\d+)/$','experiments.views.experimentinfo'),
    url(r'^savetool/','experiments.views.savetool'),
    url(r'^savefile/','experiments.views.savefile'),
    
    url(r'^initmyflowtools/(\d+)/$','experiments.views.initmyflowtools'),
    url(r'^savetopo/(\d+)/$','experiments.views.savetopo'),
    
    url(r'^outlines/','outlines.views.mgroutline'),
    url(r'^outlineinfo/','outlines.views.outlineinfo'),
    url(r'^teacheridcheck/','outlines.views.teacheridcheck'),
    url(r'^outlineOnname/','outlines.views.outlineOnname'),
    url(r'^outlineOnid/','outlines.views.outlineOnid'),
    url(r'^outtreeDetails/','outlines.views.outtreeDetails'),
    url(r'^outlineinfoDetails/','outlines.views.outlineinfoDetails'),
    url(r'^outlineadd/','outlines.views.addoutline'),
    url(r'^outlineedit/(\d+)/$','outlines.views.editoutline'),
    
    url(r'^candeloutline/(\d+)/$','outlines.views.candeloutline'),
    url(r'^selectoutline/(\d+)/$','outlines.views.selectoutline'),
    url(r'^outlinedel/(\d+)/$','outlines.views.deloutline'),
    url(r'^outlineExp/','outlines.views.outlineExp'),

    url(r'^courses/','courses.views.mgrcourse'),
    url(r'^selectcourse/','courses.views.selectcourse'),
    
    url(r'^courseGetConfig/','courses.views.GetAddConfig'),
   # url(r'^RefreshCourse/','courses.views.RefreshCourse'),
    url(r'^AddNewCourses/','courses.views.AddNewCourses'),
    url(r'^UpdateCourses/','courses.views.UpdateCourses'),
    url(r'^RemoveCourses/','courses.views.RemoveCourses'),
    url(r'^GetEditConfig/','courses.views.GetEditConfig'),
    url(r'^GetViewConfig/','courses.views.GetViewConfig'),
    url(r'^UpdateStudents/','courses.views.UpdateStudents'),
    url(r'^RoleCheck/','courses.views.RoleCheck'),
    url(r'^fileCheck/','courses.views.fileCheck'),
    url(r'^fileDown/','courses.views.fileDown'),

    
    url(r'^CouresPageChage/','courses.views.CouresPageChage'),
    url(r'^CourseCheckCname/','courses.views.CourseCheckCname'),

    url(r'^client/','client.views.mgrclient'),
    url(r'^Getaddbutton/','client.views.Getaddbutton'),
    url(r'^clientindex/','client.views.clientindex'),
    url(r'^examgetinfo/','client.views.examgetinfo'),
    url(r'^hackgetinfo/','client.views.hackgetinfo'),
    url(r'^getgroups/','client.views.getgroups'),
    url(r'^expIsStart/','client.views.expIsStart'),
    url(r'^getOldTopo/','client.views.getOldTopo'),
    url(r'^getNewTopo/','client.views.getNewTopo'),
    url(r'^clientinfor/','client.views.clientinfor'),
    url(r'^startBench/','client.views.startBench'),
    url(r'^stopBench/','client.views.stopBench'),
    url(r'^lab/','client.views.lab'),
    url(r'^clogout/','client.views.clogout'),
    url(r'^modifypwd/','client.views.modifypwd'),
    url(r'^vmconfig/(\d+.\d+.\d+.\d+)/([\w\-\:]+)/$','client.views.vmHost', name='vmconfig'),
    url(r'^submitexamque/','client.views.submitexamque'),
    url(r'^submitflags/','client.views.submitflags'),
    
    url(r'^getVMId/','client.views.getVMId'),
    url(r'^submitans/','client.views.submitans'),
    
    url(r'^GetSETime/','client.views.GetSETime'),
    

    # url(r'^contesting/','competition.views.contesting'),
    url(r'^previewpapers/','competition.views.previewpapers'),
    url(r'^previewpapers1/','competition.views.previewpapers1'),

    url(r'^contesting/','competition.views.contest'),
    url(r'^infiltrationquestioninfo/$','competition.views.infiltration_question_info'),
    url(r'^getquestiontitle/$','competition.views.get_question_title'),
    url(r'^load-student-questions/','competition.views.load_student_questions'),
    url(r'^loadflags/','competition.views.loadflags'),

    url(r'^teaminfo/','competition.views.teaminfo'),
    #对抗的团队排名
    url(r'^teamrank/','competition.views.teamrank'),

    url(r'^getteaminfo/','competition.views.getteaminfo'),
    url(r'^getteamess/','competition.views.getteamess'),

    url(r'^competorder/','competition.views.competorder'),
    url(r'^downresource/','competition.views.downresource'),
    #url(r'^downresource1/','Tools.views.showtool'),

    url(r'^groupinfo/','competition.views.groupinfo'),

    url(r'^hacking/','hack.views.hacking'),
    url(r'^flags/','hack.views.flags'),
    url(r'^ranking/','hack.views.ranking'),
    url(r'^netsource/','hack.views.netsource'),

    url(r'^hackingorder/','hack.views.hackingorder'),
    url(r'^sysresource/','hack.views.sysresource'),
    url(r'^groupstate/','hack.views.groupstate'),
    url(r'^Getid/([\w\-\.]+)/([\w\-\.]+)/$','hack.views.Getid'),

    
    url(r'^departmentadd/','classes.views.adddepartment'),
    url(r'^classadd/','classes.views.addclass'),
    url(r'^classdel/(\d+)/$','classes.views.delclass'),
    url(r'^departmentdel/(\d+)/$','classes.views.deldepartment'),
    url(r'^classedit/(\d+)/$','classes.views.editclass'),
    url(r'^departmentedit/(\d+)/$','classes.views.editdepartment'),
    url(r'^deptnamecheck/','classes.views.deptnamecheck'),
    url(r'^clanamecheck/','classes.views.clanamecheck'),

    
    url(r'^teachers/','teachers.views.mgrteacher'),
    url(r'^teacheraccountcheck/','teachers.views.teacheraccountcheck'),
    url(r'^teacherinfo/','teachers.views.teacherinfo'),
    url(r'^teacheradd/','teachers.views.addteacher'),
    url(r'^teacheredit/(\d+)/$','teachers.views.editteacher'),
    url(r'^teacherdel/(\d+)/$','teachers.views.delteacher'),
    url(r'^roletypecheck/','teachers.views.roletypecheck'),
    url(r'^ExamcheckforTea/(\d+)/$','teachers.views.findTeacherbyExam'),
    url(r'^CoursecheckforTea/(\d+)/$','teachers.views.findTeacherbyCourse'),

                                                   
    url(r'^students/','students.views.mgrstudent'),
    url(r'^pageinfor/','students.views.pageinfor'),
    url(r'^stugracla/','students.views.stugracla'),
    url(r'^studentstunocheck/','students.views.studentstunocheck'),
    url(r'^deptinfo/','students.views.deptinfo'),
    url(r'^depteditinfo/','students.views.depteditinfo'),
    url(r'^claeditinfo/','students.views.claeditinfo'),
    url(r'^clainfo/','students.views.clainfo'),
    url(r'^studentinfo/','students.views.studentinfo'),
    url(r'^studentaddinfo/','students.views.studentaddinfo'),
    url(r'^download/', 'students.views.download_file'),
    url(r'^studentsadd/', 'students.views.addstudents'),
    url(r'^refreshstudent/', 'students.views.refreshstudent'),
    url(r'^studentadd/','students.views.addstudent'),
    url(r'^studentedit/(\d+)/$','students.views.editstudent'),
    url(r'^studentdel/(\d+)/$','students.views.delstudent'),
    url(r'^coursecheck/','students.views.coursecheck'),
    url(r'^GroupcheckforStu/(\d+)/$','students.views.findStubyGroup'),
    url(r'^CoursecheckforStu/(\d+)/$','students.views.findStubyCourse'),

    # url(r'^getqtioninfo/','questions.views.getqtioninfo'),
    # url(r'^choose/','questions.views.mgrchoose'),
    # url(r'^skill/','questions.views.mgrskill'),
    # url(r'^infiltration/','questions.views.mgrinfiltration'),
    # url(r'^skilladd/','questions.views.addskill'),
    # url(r'^checkquedel/(\d+)/$','questions.views.checkquedel'),
    # url(r'^skilldel/(\d+)/$','questions.views.delskill'),
    # url(r'^qidcheck/','questions.views.qidcheck'),
    # url(r'^skilllinkcheck/','questions.views.skilllinkcheck'),
    # url(r'^skillinfo/','questions.views.skillinfo'),
    # url(r'^skilledit/(\d+)/$','questions.views.editskill'),
    # url(r'^infiltrationadd/','questions.views.addinfiltration'),
    # url(r'^infiltrationdel/(\d+)/$','questions.views.delinfiltration'),
    # url(r'^infiltrationlinkcheck/','questions.views.infiltrationlinkcheck'),
    # url(r'^infiltrationinfo/','questions.views.infiltrationinfo'),
    # url(r'^infiltrationedit/(\d+)/$','questions.views.editinfiltration'),
    # url(r'^chooseadd/','questions.views.addchoose'),
    # url(r'^choosedel/(\d+)/$','questions.views.delchoose'),
    # url(r'^chooseinfo/','questions.views.chooseinfo'),
    # url(r'^instartexam/','questions.views.instartexam'),
    # url(r'^chooseedit/(\d+)/$','questions.views.editchoose'),

    url(r'^groups/','groups.views.mgrgroup'),
    url(r'^groupdel/(\d+)/$','groups.views.delgroup'),
    url(r'^Checkgruse/', 'groups.views.Checkgruse'),

    url(r'^groupadd/$','groups.views.addgroup'),
    url(r'^GetEditInfo/(\d+)/$','groups.views.GetEditInfo'),
    url(r'^Isinexam/','groups.views.Isinexam'),
    url(r'^Getgroupmembers/','groups.views.Getgroupmembers'),
    url(r'^groupdate/$','groups.views.updateproup'),
    url(r'^groupstudenttree/','groups.views.groupstudenttree'),
    url(r'^groupstudentinfo/(\d+)/$','groups.views.groupstudentinfo'),
    url(r'^checkgroname/$','groups.views.checkgroname'),


    url(r'^papers/$','papers.views.managePaper'),
    url(r'^GetAddPaperInfo/$','papers.views.GetAddPaperInfo'),
    url(r'^GetEditPaperInfo/$', 'papers.views.GetEditPaperInfo'),
    url(r'^GetDisplayPaperInfo/$', 'papers.views.GetPaperInfo'),
    url(r'^GetPapBaseInfo/$', 'papers.views.GetPapBaseInfo'),
    url(r'^SaveAddPap/$', 'papers.views.SaveAddPap'),
    #select questions
    url(r'^selectque/$', 'papers.views.selectque'),
    url(r'^UpdateEditPap/$', 'papers.views.UpdateEditPap'),
    url(r'^Checkuse/$', 'papers.views.Checkuse'),
    url(r'^RemovePap/$', 'papers.views.RemovePap'),
    url(r'^checkPapInfo/$', 'papers.views.checkPapInfo'),
    url(r'^SearchQue/$', 'papers.views.SearchQue'),

    url(r'^examinations/', include('examinations.urls')),
    url(r'^examinationshow/(\d+)$', 'examinations.views.examination_show'),
    url(r'^askActualGrade/(\d+)$', 'examinations.views.askActualGrade'),
    url(r'^gm/$', 'examinations.views.askActualGrade'),


    url(r'^examinationshow/getexaminfo/$', 'examinations.views.get_exam_info'),
    url(r'^examinationshow/getnewdatas/$', 'examinations.views.get_new_datas'),

    url(r'^atkdfs/', include('atkdfs.urls')),

    url(r'^sysinfo/','sysmgr.views.mgrsys'),
    url(r'^info/cpu/', 'sysmgr.views.cpuusage', name='cpuusage'),
    url(r'^info/memory/', 'sysmgr.views.memusage', name='memusage'),
    url(r'^info/disk/', 'sysmgr.views.diskusage', name='diskusage'),

    url(r'^sysmgr/', include('sysmgr.urls')),


     url(r'^myexp/','myexp.views.myexpinitial'),
     url(r'^GetEnumEditConfig/','myexp.views.GetEnumEditConfig'),
     url(r'^DeleteEnumSubmit/','myexp.views.DeleteEnumSubmit'),
     url(r'^AddEnumSubmit/','myexp.views.AddEnumSubmit'),
     url(r'^EditEnumSubmit/','myexp.views.EditEnumSubmit'),
     url(r'^GetContentEditConfig/','myexp.views.GetContentEditConfig'),
     url(r'^DeleteContentSubmit/','myexp.views.DeleteContentSubmit'),
     url(r'^AddContentSubmit/','myexp.views.AddContentSubmit'),
     url(r'^EditContentSubmit/','myexp.views.EditContentSubmit'),
     url(r'^EnumPageChange/','myexp.views.EnumPageChange'),
     url(r'^ContentPageChange/','myexp.views.ContentPageChange'),

     # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'^document/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_URL}),
    (r'^statics/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
)
