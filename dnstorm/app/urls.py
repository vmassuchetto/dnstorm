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
    (r'^problems/collaborating/$', base.HomeView.as_view(), {}, 'problems_collaborating'),
    (r'^problems/drafts/$', base.HomeView.as_view(), {}, 'problems_drafts'),

    # Problem
    (r'^problems/create/$', problem.ProblemCreateView.as_view(), {}, 'problem_create'),
    (r'^problems/update/(?P<pk>\d+)/$', problem.ProblemUpdateView.as_view(), {}, 'problem_update'),
    (r'^problems/collaborators/(?P<pk>\d+)/$', problem.ProblemCollaboratorsView.as_view(), {}, 'problem_collaborators'),
    (r'^problems/(?P<pk>\d+)/#ideas$', problem.ProblemUpdateView.as_view(), {}, 'problem_ideas'),
    (r'^problems/(?P<pk>\d+)/$', problem.ProblemView.as_view(), {}, 'problem_short'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#description$', problem.ProblemView.as_view(), {}, 'problem_tab_description'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#criteria$', problem.ProblemView.as_view(), {}, 'problem_tab_criteria'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#ideas$', problem.ProblemView.as_view(), {}, 'problem_tab_ideas'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#alternatives$', problem.ProblemView.as_view(), {}, 'problem_tab_alternatives'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#idea-(?P<idea>\d+)$', problem.ProblemView.as_view(), {}, 'problem_idea'),
    (r'^problems/(?P<pk>\d+)/(?P<slug>[^/]+)/#alternative-(?P<alternative>\d+)$', problem.ProblemView.as_view(), {}, 'problem_alternative'),

    # Criteria
    (r'^criteria/create/(?P<problem>\d+)/$', criteria.CriteriaCreateView.as_view(), {}, 'criteria_create'),
    (r'^criteria/(?P<pk>\d+)/update/$', criteria.CriteriaUpdateView.as_view(), {}, 'criteria_update'),
    (r'^criteria/(?P<pk>\d+)/delete/$', criteria.CriteriaDeleteView.as_view(), {}, 'criteria_delete'),

    # Ideas
    (r'^ideas/create/(?P<problem>\d+)/$', idea.IdeaCreateView.as_view(), {}, 'idea_create'),
    (r'^ideas/(?P<pk>\d+)/update/$', idea.IdeaUpdateView.as_view(), {}, 'idea_update'),
    (r'^ideas/(?P<pk>\d+)/delete/$', idea.IdeaDeleteView.as_view(), {}, 'idea_delete'),
    (r'^ideas/(?P<pk>\d+)/$', idea.IdeaView.as_view(), {}, 'idea'),

    # Alternatives
    (r'^alternative/create/(?P<problem>\d+)/$', alternative.AlternativeCreateView.as_view(), {}, 'alternative_create'),
    (r'^alternative/(?P<pk>\d+)/update/$', alternative.AlternativeUpdateView.as_view(), {}, 'alternative_update'),
    (r'^alternative/(?P<pk>\d+)/delete/$', alternative.AlternativeDeleteView.as_view(), {}, 'alternative_delete'),

    # Comments
    (r'^comments/(?P<pk>\d+)/$', base.CommentView.as_view(), {}, 'comment'),

    # Users
    (r'^users/$', user.UsersView.as_view(), {}, 'users'),
    (r'^users/(?P<user_type>invitations|inactive)/$', user.UsersView.as_view(), {}, 'users_filter'),
    (r'^users/(?P<username>[^/]+)/$', user.UserView.as_view(), {}, 'user'),
    (r'^users/(?P<username>[^/]+)/activate/$', user.UserActivateView.as_view(), {}, 'user_activate'),
    (r'^users/(?P<username>[^/]+)/inactivate/$', user.UserInactivateView.as_view(), {}, 'user_inactivate'),
    (r'^users/(?P<username>[^/]+)/update/$', user.UserUpdateView.as_view(), {}, 'user_update'),
    (r'^users/(?P<username>[^/]+)/update/password/$', user.UserPasswordUpdateView.as_view(), {}, 'user_password_update'),

    # Activity
    (r'^activity/$', base.ActivityView.as_view(), {}, 'activity'),
    (r'^activity/(?P<content_type>problems|criteria|ideas|alternatives|comments)/$', base.ActivityView.as_view(), {}, 'activity_objects'),
    (r'^activity/problem/(?P<pk>\d+)/$', base.ActivityView.as_view(), {}, 'activity_problem'),
    (r'^activity/problem/(?P<pk>\d+)/(?P<content_type>description|criteria|ideas|alternatives|comments)/$', base.ActivityView.as_view(), {}, 'activity_problem_objects'),

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
    (r'^stream/', include('actstream.urls')),

    # Static files
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),

)
