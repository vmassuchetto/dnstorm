import re
import random

from django.db.models import Q
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from avatar.templatetags.avatar_tags import avatar_url

from dnstorm.app.models import Criteria

class CriteriaLookup(object):
    model = Criteria

    def get_query(self, q, request):
        qs = Q(name__icontains=q) \
            | Q(description__icontains=q)
        return Criteria.objects.filter(qs).order_by('name')[:10]

    def get_objects(self, ids):
        return Criteria.objects.filter(pk__in=ids).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_item_display(self, obj):
        return render_to_string('criteria_lookup_display.html', {'criteria': obj})


class UserLookup(object):
    model = User

    def get_query(self, q, request):
        """
        Will display and invitation button instead of the user result if it's
        an e-mail.
        """
        e = re.compile('[^@]+@[^@]+\.[^@]+')
        if e.match(q):
            u = User(username=q, email=q)
            u.id = random.randint(0, (2**32)-1)
            u.invitation = True
            u.button = '<div class="button no-margin-bottom radius small"><i class="fi-mail"></i> %s</div>' % q
            return [u]
        qs = Q(username__icontains=q) \
            | Q(email__icontains=q) \
            | Q(first_name__icontains=q) \
            | Q(last_name__icontains=q)
        return User.objects.filter(qs).order_by('username')[:10]

    def get_objects(self, ids):
        return User.objects.filter(pk__in=ids).order_by('username')[:10]

    def get_result(self, obj):
        return obj.username

    def format_item_display(self, obj):
        return render_to_string('user_lookup_display.html', {'user': obj, 'avatar_url': avatar_url(obj, 24)})
