from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
from django.utils.functional import curry
from django.views.defaults import *

from dnstorm import settings
from dnstorm.app.forms import RegistrationForm
from dnstorm.app.views import *

js_info_dict = {'packages': ('app',)}
handler500 = curry(server_error, template_name='_500.html')
handler404 = curry(page_not_found, template_name='_404.html')
handler403 = curry(permission_denied, template_name='_403.html')

urlpatterns = patterns('',

    # Home

    (r'^$', base.HomeView.as_view(), {}, 'home'),

    # Problems

    (r'^problems/my/$', base.HomeView.as_view(), {}, 'problems_my'),
    (r'^problems/contribute/$', base.HomeView.as_view(), {}, 'problems_contribute'),
    (r'^problems/drafts/$', base.HomeView.as_view(), {}, 'problems_drafts'),

    # Problem

    (r'^problems/create/$', problem.ProblemCreateView.as_view(), {}, 'problem_create'),
    (r'^problems/(?P<pk>\d+)/update/$', problem.ProblemUpdateView.as_view(), {}, 'problem_update'),
    (r'^problems/(?P<pk>\d+)/#ideas$', problem.ProblemUpdateView.as_view(), {}, 'problem_ideas'),
    (r'^problems/(?P<pk>\d+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#description$', problem.ProblemView.as_view(), {}, 'problem_tab_description'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#criteria$', problem.ProblemView.as_view(), {}, 'problem_tab_criteria'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#ideas$', problem.ProblemView.as_view(), {}, 'problem_tab_ideas'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#alternatives$', problem.ProblemView.as_view(), {}, 'problem_tab_alternatives'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#idea-(?P<idea>\d+)$', problem.ProblemView.as_view(), {}, 'problem_idea'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/activity/$', problem.ProblemActivityView.as_view(), {}, 'problem_activity'),

    # Ideas

    (r'^ideas/create/(?P<pk>\d+)/$', idea.IdeaCreateView.as_view(), {}, 'idea_create'),
    (r'^ideas/(?P<pk>\d+)/update/$', idea.IdeaUpdateView.as_view(), {}, 'idea_update'),
    (r'^ideas/(?P<pk>\d+)/$', idea.IdeaView.as_view(), {}, 'idea'),

    # Comments

    (r'^comments/(?P<pk>\d+)/$', base.CommentView.as_view(), {}, 'comment'),

    # Users

    (r'^users/$', user.UsersView.as_view(), {}, 'users'),
    (r'^users/invitations/$', user.UsersView.as_view(), {}, 'users_invitations'),
    (r'^users/inactive/$', user.UsersView.as_view(), {}, 'users_inactive'),
    (r'^users/(?P<username>[^/]+)/$', user.UserView.as_view(), {}, 'user'),
    (r'^users/(?P<username>[^/]+)/activate/$', user.UserActivateView.as_view(), {}, 'user_activate'),
    (r'^users/(?P<username>[^/]+)/inactivate/$', user.UserInactivateView.as_view(), {}, 'user_inactivate'),
    (r'^users/(?P<username>[^/]+)/update/$', user.UserUpdateView.as_view(), {}, 'user_update'),
    (r'^users/(?P<username>[^/]+)/update/password/$', user.UserPasswordUpdateView.as_view(), {}, 'user_password_update'),

    # Activity

    (r'^activity/$', base.ActivityView.as_view(), {}, 'activity'),

    # Options

    (r'^options/$', base.OptionsView.as_view(), {}, 'options'),

    # Ajax

    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),

    # Other apps

    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/register/$', base.RegistrationView.as_view(), {}, 'registration_register'),
    (r'^accounts/', include('django.contrib.auth.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),

    # Static files

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),

)
