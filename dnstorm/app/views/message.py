import time

from django.views.generic.edit import CreateView
from django.views.generic import DetailView, ListView
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

from dnstorm import settings

from dnstorm.app.models import Problem, Message
from dnstorm.app.forms import MessageForm

class MessageCreateView(CreateView):
    model = Message
    template_name = 'message_edit.html'
    form_class = MessageForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.problem = get_object_or_404(Problem, id=self.kwargs['problem_id'])
        return super(MessageCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(MessageCreateView, self).get_context_data(*args, **kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['title'] = mark_safe(_('Compose new message for problem <a href="%(url)s">#%(id)d</a>' % { 'url': reverse('problem', args=[self.problem.slug]), 'id': self.problem.id}))
        context['problem'] = self.problem
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problem'), 'url': self.problem.get_absolute_url() },
            { 'title': self.problem.title, 'url': reverse('problem', kwargs={'slug':self.problem.slug}) },
            { 'title': _('Messages'), 'url': reverse('message_problem', kwargs={'problem_id':self.problem.id}) },
            { 'title': _('Compose new message'), 'classes': 'current' } ]

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.problem = self.problem
        self.object.sender = self.request.user
        self.object.save()
        # TODO
        #site_name = get_option('site_name') if get_option('site_name') else settings.DNSTORM['site_name']
        site_name = ''
        subject = '[%s] %s' % (site_name, form.cleaned_data['subject'])
        recipients = [r.email for r in self.problem.get_message_recipients()]
        if settings.DEBUG:
            print '[%s] "MAIL would be sent to %s"' % (time.strftime('%d/%b/%Y %H:%M:%S'), ', '.join(recipients))
        else:
            send_mail(subject, form.cleaned_data['content'], settings.EMAIL_HOST_USER, recipients)
        return HttpResponseRedirect(reverse('problem', kwargs={'slug':self.problem.slug}))

class MessageView(DetailView):
    model = Message
    template_name = 'message.html'

    def get_context_data(self, *args, **kwargs):
        context = super(MessageView, self).get_context_data(*args, **kwargs)
        self.problem = context['message'].problem
        self.message = context['message']
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['problem'] = context['message'].problem
        context['bulletin'] = Message.objects.filter(problem=context['problem']).order_by('-created')[:4]
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': self.problem.get_absolute_url() },
            { 'title': self.problem.title, 'url': reverse('problem', kwargs={'slug':self.problem.slug}) },
            { 'title': _('Messages'), 'url': reverse('message_problem', kwargs={'problem_id':self.problem.id}) },
            { 'title': _('Message #%(id)d' % {'id':self.message.id}), 'classes': 'current' } ]

class MessageProblemListView(ListView):
    model = Message
    template_name = 'message_list.html'

    def dispatch(self, *args, **kwargs):
        self.problem = get_object_or_404(Problem, id=self.kwargs['problem_id'])
        return super(MessageProblemListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(MessageProblemListView, self).get_context_data(*args, **kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        context['problem'] = self.problem
        context['bulletin'] = Message.objects.filter(problem=context['problem']).order_by('-created')
        context['message'] = True
        return context

    def get_breadcrumbs(self):
        return [
            { 'title': _('Problems'), 'url': self.problem.get_absolute_url() },
            { 'title': self.problem.title, 'url': reverse('problem', kwargs={'slug':self.problem.slug}) },
            { 'title': _('Messages'), 'classes': 'current' } ]
