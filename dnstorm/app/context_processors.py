from dnstorm.app.models import Option
from dnstorm.app import DNSTORM_URL

def base(request):
    context = dict()
    context['dnstorm_url'] = DNSTORM_URL
    context['options'] = Option().get_all()
    return context
