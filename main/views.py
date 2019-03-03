from django.shortcuts import render
from django.shortcuts import redirect
from .models import Student
from .forms import LoginForm

# Create your views here.


def index(request):

    message = '欢迎'
    if request.session.get('is_login', None):
        message = message + str(request.session['studentID'])
    return render(request, 'main/index.html', locals())


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index/')

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        message = ""
        if login_form.is_valid():
            studentID = login_form.cleaned_data['studentID']
            password = login_form.cleaned_data['password']
            try:
                student = Student.objects.get(studentID=studentID)
                if password == student.password:
                    request.session['studentID'] = student.studentID
                    request.session['id'] = student.id
                    request.session['name'] = student.name
                    request.session['is_login'] = True
                    return redirect('/index/')
                else:
                    message = "密码错误！"
            except:
                message = "学号错误！"
    login_form = LoginForm(request.POST)
    return render(request, 'main/login.html', locals())


def register(request):
    return render(request, 'main/register.html')


def logout(request):
    if request.session.get('is_login', None):
        return redirect('/index')
    request.session.flush()
    return redirect("/index/")
