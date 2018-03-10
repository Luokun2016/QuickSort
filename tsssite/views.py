# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage

def home(request):
		return HttpResponseRedirect('/Login/')
