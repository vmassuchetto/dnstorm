from django.conf.urls import patterns, include, url

from dnstorm import settings
from dnstorm.app.views import *

from ajax_select import urls as ajax_select_urls
from haystack.views import search_view_factory

from django.contrib.auth import views as auth_views

js_info_dict = {
    'packages': ('app',),
}

urlpatterns = patterns('',

    # DNStorm

    (r'^$', base.HomeView.as_view(), {}, 'home'),
    (r'^ajax/$', ajax.AjaxView.as_view(), {}, 'ajax'),

    # Problems

    (r'^problem/new/$', problem.ProblemCreateView.as_view(), {}, 'problem_new'),
    (r'^problem/(?P<slug>[^/]+)/$', problem.ProblemView.as_view(), {}, 'problem'),
    (r'^problem/(?P<slug>[^/]+)/edit/$', problem.ProblemUpdateView.as_view(), {}, 'problem_edit'),
    (r'^problem/(?P<slug>[^/]+)/delete/$', problem.ProblemDeleteView.as_view(), {}, 'problem_delete'),
    (r'^problem/(?P<slug>[^/]+)/revisions/$', problem.ProblemRevisionView.as_view(), {}, 'problem_revision'),
    (r'^problem/(?P<slug>[^/]+)/revisions/#revision-(?P<revision_id>[^/]+)$', problem.ProblemRevisionItemView.as_view(), {}, 'problem_revision_item'),
    (r'^problem/(?P<slug>[^/]+)/#ideas$', problem.ProblemUpdateView.as_view(), {}, 'problem_ideas'),

    # Ideas

    (r'^problem/(?P<slug>[^/]+)/#idea-(?P<pk>[^/]+)$', idea.IdeaView.as_view(), {}, 'idea'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/edit/$', idea.IdeaUpdateView.as_view(), {}, 'idea_edit'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/revisions/$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision'),
    (r'^problem/(?P<slug>[^/]+)/idea/(?P<pk>[^/]+)/revisions/#revision-(?P<revision_id>[^/]+)$', idea.IdeaRevisionView.as_view(), {}, 'idea_revision_item'),

    # Messages

    (r'^problem/(?P<slug>[^/]+)/message/new/$', message.MessageCreateView.as_view(), {}, 'message_new'),
    (r'^problem/(?P<slug>[^/]+)/message/(?P<pk>[^/]+)/$', message.MessageView.as_view(), {}, 'message'),
    (r'^problem/(?P<slug>[^/]+)/messages/$', message.MessageProblemListView.as_view(), {}, 'messages'),

    # Comments

    (r'^problem/(?P<slug>[^/]+)/#comment-(?P<pk>[^/]+)$', base.CommentView.as_view(), {}, 'comment'),

    # Criterias

    (r'^criteria/$', criteria.CriteriaListView.as_view(), {}, 'criteria_list'),
    (r'^criteria/new/$', criteria.CriteriaCreateView.as_view(), {}, 'criteria_new'),
    (r'^criteria/(?P<slug>[^/]+)/$', criteria.CriteriaView.as_view(), {}, 'criteria'),
    (r'^criteria/(?P<slug>[^/]+)/edit/$', criteria.CriteriaUpdateView.as_view(), {}, 'criteria_edit'),
    (r'^users/(?P<username>[^/]+)/$', user.UserView.as_view(), {}, 'user'),
    (r'^activity/$', base.ActivityView.as_view(), {}, 'activity'),

    # DNStorm admin

    (r'^admin/options/$', base.AdminOptionsView.as_view(), {}, 'admin_options'),
    (r'^admin/users/$', user.AdminUserListView.as_view(), {}, 'admin_user'),
    (r'^admin/users/(?P<user_id>[^/]+)/$', user.AdminUserUpdateView.as_view(), {}, 'admin_user_edit'),
    (r'^admin/users/(?P<user_id>[^/]+)/activate/$', user.AdminUserActivateView.as_view(), {}, 'admin_user_activate'),
    (r'^admin/users/(?P<user_id>[^/]+)/deactivate/$', user.AdminUserDeactivateView.as_view(), {}, 'admin_user_deactivate'),

    # Other apps

    (r'^search/', search_view_factory(view_class=base.SearchView), {}, 'search'),
    (r'^avatar/', include('avatar.urls')),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, name='auth_password_reset_confirm'),
    (r'^accounts/', include('django.contrib.auth.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^lookups/', include(ajax_select_urls)),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'jsi18n'),
    (r'^ckeditor/', include('ckeditor.urls')),

    # Static files

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),

)
