from django.shortcuts import render

def mymodule_list(request):
    return render(request, 'bhtom_mymodule/list.html')

def mymodule_details(request):
    return render(request, 'bhtom_mymodule/details.html')
