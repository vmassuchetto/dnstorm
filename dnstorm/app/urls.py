from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
from django.utils.functional import curry
from django.views.defaults import *

from dnstorm import settings
from dnstorm.app.forms import RegistrationForm
from dnstorm.app import views

js_info_dict = {'packages': ('app',)}
handler500 = curry(server_error, template_name='_500.html')
handler404 = curry(page_not_found, template_name='_404.html')
handler403 = curry(permission_denied, template_name='_403.html')

urlpatterns = patterns('',

    # Home
    (r'^$', views.HomeView.as_view(), {}, 'home'),

    # Problems
    (r'^problems/collaborating/$', views.HomeView.as_view(), {}, 'problems_collaborating'),
    (r'^problems/drafts/$', views.HomeView.as_view(), {}, 'problems_drafts'),

    # Problem
    (r'^problems/create/$', views.ProblemCreateView.as_view(), {}, 'problem_create'),
    (r'^problems/update/(?P<pk>\d+)/$', views.ProblemUpdateView.as_view(), {}, 'problem_update'),
    (r'^problems/delete/(?P<pk>\d+)/$', views.ProblemDeleteView.as_view(), {}, 'problem_delete'),
    (r'^problems/collaborators/(?P<pk>\d+)/$', views.ProblemCollaboratorsView.as_view(), {}, 'problem_collaborators'),
    (r'^problems/(?P<pk>\d+)/#ideas$', views.ProblemUpdateView.as_view(), {}, 'problem_ideas'),
    (r'^problems/(?P<pk>\d+)/$', views.ProblemView.as_view(), {}, 'problem_short'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/$', views.ProblemView.as_view(), {}, 'problem'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#description$', views.ProblemView.as_view(), {}, 'problem_tab_problem'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#criteria$', views.ProblemView.as_view(), {}, 'problem_tab_criteria'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#ideas$', views.ProblemView.as_view(), {}, 'problem_tab_idea'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#alternatives$', views.ProblemView.as_view(), {}, 'problem_tab_alternative'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#results$', views.ProblemView.as_view(), {}, 'problem_tab_results'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#idea-(?P<idea>\d+)$', views.ProblemView.as_view(), {}, 'problem_idea'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#alternative-(?P<alternative>\d+)$', views.ProblemView.as_view(), {}, 'problem_alternative'),

    # Criteria
    (r'^criteria/create/(?P<problem>\d+)/$', views.CriteriaCreateView.as_view(), {}, 'criteria_create'),
    (r'^criteria/(?P<pk>\d+)/update/$', views.CriteriaUpdateView.as_view(), {}, 'criteria_update'),
    (r'^criteria/(?P<pk>\d+)/delete/$', views.CriteriaDeleteView.as_view(), {}, 'criteria_delete'),

    # Ideas
    (r'^ideas/create/(?P<problem>\d+)/$', views.IdeaCreateView.as_view(), {}, 'idea_create'),
    (r'^ideas/(?P<pk>\d+)/update/$', views.IdeaUpdateView.as_view(), {}, 'idea_update'),
    (r'^ideas/(?P<pk>\d+)/delete/$', views.IdeaDeleteView.as_view(), {}, 'idea_delete'),
    (r'^ideas/(?P<pk>\d+)/$', views.IdeaView.as_view(), {}, 'idea'),

    # Alternatives
    (r'^alternative/create/(?P<problem>\d+)/$', views.AlternativeCreateView.as_view(), {}, 'alternative_create'),
    (r'^alternative/(?P<pk>\d+)/update/$', views.AlternativeUpdateView.as_view(), {}, 'alternative_update'),
    (r'^alternative/(?P<pk>\d+)/delete/$', views.AlternativeDeleteView.as_view(), {}, 'alternative_delete'),

    # Comments
    (r'^comments/(?P<pk>\d+)/$', views.CommentView.as_view(), {}, 'comment'),

    # Users
    (r'^users/$', views.UsersView.as_view(), {}, 'users'),
    (r'^users/(?P<user_type>invitations|inactive)/$', views.UsersView.as_view(), {}, 'users_filter'),
    (r'^users/(?P<username>[^/]+)/$', views.UserView.as_view(), {}, 'user'),
    (r'^users/(?P<username>[^/]+)/activate/$', views.UserActivateView.as_view(), {}, 'user_activate'),
    (r'^users/(?P<username>[^/]+)/inactivate/$', views.UserInactivateView.as_view(), {}, 'user_inactivate'),
    (r'^users/(?P<username>[^/]+)/update/$', views.UserUpdateView.as_view(), {}, 'user_update'),
    (r'^users/(?P<username>[^/]+)/update/password/$', views.UserPasswordUpdateView.as_view(), {}, 'user_password_update'),

    # Activity
    (r'^activity/$', views.ActivityView.as_view(), {}, 'activity'),
    (r'^activity/(?P<content_type>problems|criteria|ideas|alternatives|comments)/$', views.ActivityView.as_view(), {}, 'activity_objects'),
    (r'^activity/problem/(?P<pk>\d+)/$', views.ActivityView.as_view(), {}, 'activity_problem'),
    (r'^activity/problem/(?P<pk>\d+)/(?P<content_type>description|criteria|ideas|alternatives|comments)/$', views.ActivityView.as_view(), {}, 'activity_problem_objects'),

    # Options
    (r'^options/$', views.OptionsView.as_view(), {}, 'options'),

    # Ajax
    (r'^ajax/$', views.AjaxView.as_view(), {}, 'ajax'),

    # Other apps
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/register/$', views.RegistrationView.as_view(), {}, 'registration_register'),
    (r'^accounts/', include('django.contrib.auth.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^stream/', include('actstream.urls')),

    # Static files
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),

)
