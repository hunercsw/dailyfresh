from django.shortcuts import render
from django.shortcuts import redirect
# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.views.generic import View
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)


from django.conf import settings
from apps.user import models
from celery_tasks.tasks import *

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail
import re


class RegisterView(View):
    """display register page and realize user refister"""

    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        user_name = request.POST.get("user_name")
        user_password = request.POST.get("pwd")
        user_password_confirm = request.POST.get("cpwd")
        user_email = request.POST.get("email")
        agreement = request.POST.get("allow")
        # check protocol agreement
        if not all([user_name, user_password, user_password_confirm, user_email]):
            return render(request, "register.html", {"error_message": "missing register information"})
        if agreement != "on":
            return render(request, "register.html", {"error_message": "not allow protocol"})
        # check user name is exist
        try:
            models.User.objects.get(username=user_name)
        except models.User.DoesNotExist:
            # check password
            if user_password != user_password_confirm:
                return render(request, "register.html", {"error_message": "inconsistent password"})
            # check email is legal
            if not re.match(r'^[0-9a-z][\w.\-]*@[0-9a-z]+(\.[a-z]{2,5}){1,2}$', user_email):
                return render(request, "register.html", {"error_message": "email illegal"})
            # register succeed
            user = models.User.objects.create_user(user_name, user_email, user_password)
            print(user_name, user_password)
            print(user.password)
            print(check_password(user_password, user.password))
            user.is_active = 0
            user.save()

            # create activate code  （settings.SECRET_KRY 是django的settings文件中自带的秘钥）
            serializer = Serializer(settings.SECRET_KEY, 3600)  # 数字是有效期
            secret_info = {"confirm": user.id}
            token = serializer.dumps(secret_info).decode("utf-8")

            # send email
            send_register_active_email.delay(user_email, user_name, token)

            # return index.html
            return redirect(reverse("user:register_succeed"))
        else:
            return render(request, "register.html", {"error_message": "user name has registered"})


class RegisterSucceedView(View):
    def get(self, request):
        return render(request, "register_succeed.html")


class ActiveView(View):
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            secret_info = serializer.loads(token)
        except SignatureExpired as res:
            secret_info = serializer.loads(token)
            secret_info = {"confirm": secret_info["confirm"]}
            token = serializer.dumps(secret_info).decode("utf-8")
            centent = "<h1>activate code is out of date, please click the link to active your account again</h1>" \
                      "<a href='href='http://192.168.6.15:8000/user/active/%s'>" \
                      "href='http://192.168.6.15:8000/user/active/%s</a>" \
                      % (token, token)
            return HttpResponse(centent)
        else:
            user = models.User.objects.get(id=secret_info["confirm"])
            if user.is_active == 1:
                return HttpResponse("your account is active")
            else:
                user.is_active = 1
                user.save()
                return redirect(reverse("user:login"))


class LoginView(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        user_name = request.POST.get("username")
        user_password = request.POST.get("pwd")

        # check user login infomation
        user = authenticate(username=user_name, password=user_password)
        # try:
        #     user = models.User.objects.get(username=user_name)
        # except:
        #     print("1")
        # else:

        # if check_password(user_password, user.password):
        print(user)
        if user:
            if user.is_active:
                # remember user status
                login(request, user)
                return redirect(reverse("goods:index"))
            else:
                return render(request, "login.html", {"error_message": "account is disabled"})
        else:
            return render(request, "login.html", {"error_message": "username or password is incorrect"})


