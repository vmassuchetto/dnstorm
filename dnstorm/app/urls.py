from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
from django.utils.functional import curry
from django.views.defaults import *

from ajax_select import urls as ajax_select_urls

from dnstorm import settings
from dnstorm.app.forms import RegistrationForm
from dnstorm.app.views import *

js_info_dict = {'packages': ('app',)}
handler500 = curry(server_error, template_name='500.html')
handler404 = curry(page_not_found, template_name='404.html')
handler403 = curry(permission_denied, template_name='403.html')

urlpatterns = patterns('',

    # DNStorm

    (r'^$', base.HomeView.as_view(), {}, 'home'),
    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),

    # Problems

    (r'^problem/new/$', problem.ProblemCreateView.as_view(), {}, 'problem_new'),
    (r'^problem/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problem/(?P<slug>[^/]+)/edit/$', problem.ProblemUpdateView.as_view(), {}, 'problem_edit'),
    (r'^problem/(?P<slug>[^/]+)/delete/$', problem.ProblemDeleteView.as_view(), {}, 'problem_delete'),
    (r'^problem/(?P<slug>[^/]+)/#ideas$', problem.ProblemUpdateView.as_view(), {}, 'problem_ideas'),

    # Ideas

    (r'^problem/(?P<slug>[^/]+)/#idea-(?P<pk>[^/]+)$', idea.IdeaView.as_view(), {}, 'idea'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/edit/$', idea.IdeaUpdateView.as_view(), {}, 'idea_edit'),

    # Comments

    (r'^problem/(?P<slug>[^/]+)/#comment-(?P<pk>[^/]+)$', base.CommentView.as_view(), {}, 'comment'),

    # Users

    (r'^users/(?P<username>[^/]+)/$', user.UserView.as_view(), {}, 'user'),

    # Activity

    (r'^activity/$', base.ActivityView.as_view(), {}, 'activity'),
    (r'^problem/(?P<slug>[^/]+)/activity/$', problem.ProblemActivityView.as_view(), {}, 'problem_activity'),

    # DNStorm admin

    (r'^admin/options/$', base.AdminOptionsView.as_view(), {}, 'admin_options'),
    (r'^admin/users/$', user.AdminUserListView.as_view(), {}, 'admin_user'),
    (r'^admin/users/(?P<user_id>[^/]+)/$', user.AdminUserUpdateView.as_view(), {}, 'admin_user_edit'),
    (r'^admin/users/(?P<user_id>[^/]+)/activate/$', user.AdminUserActivateView.as_view(), {}, 'admin_user_activate'),
    (r'^admin/users/(?P<user_id>[^/]+)/deactivate/$', user.AdminUserDeactivateView.as_view(), {}, 'admin_user_deactivate'),

    # Other apps

    ('^activity/', include('actstream.urls')),
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/login/$', base.LoginView.as_view(), {}, 'login_redirect'),
    (r'^accounts/register/$', base.RegistrationView.as_view(), {}, 'registration_register'),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, name='auth_password_reset_confirm'),
    (r'^accounts/', include('django.contrib.auth.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^lookups/', include(ajax_select_urls)),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),

    # Static files

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),

)
