"""
URL Configuration for views dealing with account management

These are broken out into a separate URLconf as they are likely to be attached
at a different root than the other URL patterns.

"""

from django.conf import settings
from django.conf.urls import patterns, url
from django.views.generic.base import TemplateView

from storybase_user.auth.forms import (EmailAuthenticationForm,
                                       CustomContextPasswordResetForm,
                                       StrongSetPasswordForm)
from storybase_user.views import (AccountSummaryView, AccountStoriesView,
                                 AccountNotificationsView)
from storybase_user.social_auth.views import GetExtraAccountDetailsView

urlpatterns = patterns('',
    url(r'^$', AccountSummaryView.as_view(), name='account_summary'),
    url(r'^password/$', 'django.contrib.auth.views.password_change',
        {'template_name': 'storybase_user/password_change_form.html'},
        name='account_password'),
    url(r'^password/change/done/$', 'django.contrib.auth.views.password_change_done',
        {'template_name': 'storybase_user/password_change_done.html'},
        name='password_change_done'),
    url(r'^stories/$', AccountStoriesView.as_view(), name='account_stories'),
    url(r'^notifications/$', AccountNotificationsView.as_view(), name='account_notifications'),
    url(r'^extradetails/$', GetExtraAccountDetailsView.as_view(), name='account_extra_details'),
    url(r'^password/change/$', 'django.contrib.auth.views.password_change',
        {'password_change_form': StrongSetPasswordForm},
        name='auth_password_change'),
    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset',
        {'password_reset_form': CustomContextPasswordResetForm},
        name='password_reset'),
    url(r'^password/reset/done/$', TemplateView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\\-]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'set_password_form': StrongSetPasswordForm, 'post_reset_redirect': 'password_reset_done'},
        name='auth_password_reset_confirm'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'authentication_form': EmailAuthenticationForm}),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'next_page': settings.LOGOUT_URL}),
)
