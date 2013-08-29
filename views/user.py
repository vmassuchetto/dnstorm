from django.views.generic.detail import DetailView
from django.contrib.auth.models import User

class UserDetailView(DetailView):
    model = User

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        return context
