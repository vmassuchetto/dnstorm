from django.conf.urls import patterns, include
from dnstorm.views import base, ajax, problem, criteria, idea, table

js_info_dict = {
    'packages': ('dnstorm',),
}

urlpatterns = patterns('',
    (r'^$', base.HomeView.as_view(), {}, 'home'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^accounts/', include('registration.backends.simple.urls')),
    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),
    (r'^options/$', base.OptionsView.as_view(), {}, 'options'),
    (r'^problem/new/$', problem.ProblemCreateView.as_view(), {}, 'problem_new'),
    (r'^problem/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^p/(?P<pk>[^/]+)/$', problem.ProblemShortView.as_view(), {}, 'problem_short'),
    (r'^problem/edit/(?P<pk>[^/]+)/$', problem.ProblemUpdateView.as_view(), {}, 'problem_edit'),
    (r'^problem/revisions/(?P<pk>[^/]+)/$', problem.ProblemRevisionView.as_view(), {}, 'problem_revision'),
    (r'^idea/edit/(?P<pk>[^/]+)/$', idea.IdeaUpdateView.as_view(), {}, 'idea_edit'),
    (r'^idea/revisions/(?P<pk>[^/]+)/$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision'),
    (r'^criteria/$', criteria.CriteriaView.as_view(), {}, 'criteria'),
    (r'^table/(?P<problem>[^/]+)/$', table.TableView.as_view(), {}, 'table'),
    (r'^users/(?P<username>[^/]+)/$', base.UserView.as_view(), {}, 'user'),
)
