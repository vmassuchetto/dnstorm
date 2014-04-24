from django.db.models import Q
from django.contrib.auth.models import User

from avatar.templatetags.avatar_tags import avatar_url

class UserLookup(object):

    model = User

    def get_query(self, q, request):
        qs = Q(username__icontains=q) \
            | Q(email__icontains=q) \
            | Q(first_name__icontains=q) \
            | Q(last_name__icontains=q)
        return User.objects.filter(qs).order_by('username')[:10]

    def format_item(self, user):
        return '''
            <div class="row collapse user-result">
            <div class="columns large-12">
                <div class="th avatar left"><img src="%s" /></div>
                <div class="info">%s <small>(%s)</small></div>
            </div>
        ''' % (avatar_url(user, 24), user.get_full_name(), user.username)

    def get_objects(self, ids):
        return User.objects.filter(pk__in=ids).order_by('username')[:10]
