# reddit_accounts/views.py
from django.http import HttpResponse

def reddit_accounts_list(request):
    return HttpResponse("Reddit accounts list - placeholder")

def connect_reddit(request):
    return HttpResponse("Connect Reddit - placeholder")

def reddit_callback(request):
    return HttpResponse("Reddit callback - placeholder")

def disconnect_reddit(request, pk):
    return HttpResponse("Disconnect Reddit - placeholder")