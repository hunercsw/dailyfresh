import time

from django.conf import settings
from django.core.mail import *

from celery import Celery


# django environment initialization
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()

# create tasks array
task_array = Celery("celery_tasks.tasks", broker="redis://192.168.6.15:6379/1")


# define task functions
@task_array.task
def send_register_active_email(user_email, user_name, token):
    # send activate email
    email_subject = "confirm email"
    email_message = ""
    sender = settings.EMAIL_FROM
    receiver = [user_email]
    email_html_message = "<h1>Dear %s welcome to be a member of dailyfresh</h1>" \
                         "please click the link to active your account<br/>" \
                         "<a href='http://192.168.6.15:8000/user/active/%s'>" \
                         "http://192.168.6.15:8000/user/active/%s</a>" \
                         % (user_name, token, token)
    time.sleep(15)
    send_mail(email_subject, email_message, sender, receiver, html_message=email_html_message)
