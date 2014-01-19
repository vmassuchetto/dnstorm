from django.conf.urls import patterns, include, url

from dnstorm import settings
from dnstorm.app.views import base, ajax, problem, criteria, message, idea, table

from haystack.views import search_view_factory

js_info_dict = {
    'packages': ('dnstorm',),
}

urlpatterns = patterns('',

    # DNStorm

    (r'^$', base.HomeView.as_view(), {}, 'home'),
    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),
    (r'^options/$', base.OptionsView.as_view(), {}, 'options'),
    (r'^p/(?P<pk>[^/]+)/$', problem.ProblemShortView.as_view(), {}, 'problem_short'),
    (r'^problem/new/$', problem.ProblemCreateView.as_view(), {}, 'problem_new'),
    (r'^problem/search/$', problem.ProblemSearchView.as_view(), {}, 'problem_search'),
    (r'^problem/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problem/(?P<slug>[^/]+)/edit/$', problem.ProblemUpdateView.as_view(), {}, 'problem_edit'),
    (r'^problem/(?P<slug>[^/]+)/#ideas$', problem.ProblemUpdateView.as_view(), {}, 'problem_ideas'),
    (r'^problem/(?P<slug>[^/]+)/revisions/$', problem.ProblemRevisionView.as_view(), {}, 'problem_revision'),
    (r'^problem/(?P<slug>[^/]+)/revisions/#revision-(?P<revision_id>[^/]+)$', problem.ProblemRevisionItemView.as_view(), {}, 'problem_revision_item'),
    (r'^problem/(?P<slug>[^/]+)/#idea-(?P<pk>[^/]+)$', idea.IdeaView.as_view(), {}, 'idea'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/edit/$', idea.IdeaUpdateView.as_view(), {}, 'idea_edit'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/revisions/$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/revisions/#revision-(?P<revision_id>[^/]+)$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision_item'),
    (r'^problem/(?P<slug>[^/]+)/message/new/$', message.MessageCreateView.as_view(), {}, 'message_new'),
    (r'^problem/(?P<slug>[^/]+)/message/(?P<pk>[^/]+)/$', message.MessageView.as_view(), {}, 'message'),
    (r'^problem/(?P<slug>[^/]+)/messages/$', message.MessageProblemListView.as_view(), {}, 'messages'),
    (r'^problem/(?P<slug>[^/]+)/table/$', table.TableView.as_view(), {}, 'table'),
    (r'^problem/(?P<slug>[^/]+)/#comment-(?P<pk>[^/]+)$', base.CommentView.as_view(), {}, 'comment'),
    (r'^criteria/new/$', criteria.CriteriaCreateView.as_view(), {}, 'criteria_new'),
    (r'^criteria/$', criteria.CriteriaListView.as_view(), {}, 'criteria_list'),
    (r'^criteria/(?P<slug>[^/]+)/$', criteria.CriteriaProblemView.as_view(), {}, 'criteria'),
    (r'^criteria/(?P<slug>[^/]+)/edit/$', criteria.CriteriaUpdateView.as_view(), {}, 'criteria_edit'),
    (r'^users/(?P<username>[^/]+)/$', base.UserView.as_view(), {}, 'user'),
    (r'^activity/$', base.ActivityView.as_view(), {}, 'activity'),

    # Other apps

    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^accounts/', include('registration.backends.simple.urls')),
    (r'search/', search_view_factory(view_class=base.SearchView), {}, 'search'),

)

# Static files

if not settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),
    )
