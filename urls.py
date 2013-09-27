from django.conf.urls import patterns, include
from dnstorm.views import base, ajax, problem, idea, table, user

urlpatterns = patterns('',
    (r'^$', base.HomeView.as_view(), {}, 'home'),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^profile/(?P<username>[^/]+)/$', base.ProfileView.as_view(), {}, 'profile'),
    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),
    (r'^options/$', base.OptionsView.as_view(), {}, 'options'),
    (r'^problem/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^p/(?P<pk>[^/]+)/$', problem.ProblemShortView.as_view(), {}, 'problem_short'),
    (r'^problem/new/$', problem.ProblemCreateView.as_view(), {}, 'problem_new'),
    (r'^problem/edit/(?P<pk>[^/]+)/$', problem.ProblemUpdateView.as_view(), {}, 'problem_edit'),
    (r'^problem/revisions/(?P<pk>[^/]+)/$', problem.ProblemRevisionView.as_view(), {}, 'problem_revision'),
    (r'^idea/edit/(?P<pk>[^/]+)/$', idea.IdeaUpdateView.as_view(), {}, 'idea_edit'),
    (r'^idea/revisions/(?P<pk>[^/]+)/$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision'),
    (r'^table/(?P<problem>[^/]+)/$', table.TableView.as_view(), {}, 'table'),
    (r'^user/(?P<username>[^/]+)/$', user.UserDetailView.as_view(), {}, 'user'),
)
