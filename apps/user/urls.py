from django.conf.urls import url
from apps.user import views

urlpatterns = [
    url(r'^register.html/$', views.RegisterView.as_view(), name="register"),
    url(r'^register_succeed.html$', views.RegisterSucceedView.as_view(), name="register_succeed"),
    url(r'^login.html$', views.LoginView.as_view(), name="login"),
    url(r'^active/(?P<token>.*)$', views.ActiveView.as_view(), name="active"),
]
