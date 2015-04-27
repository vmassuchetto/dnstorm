
from django.test import TestCase
from django.test import Client
from django import template
from django.db.models import get_model

class Testmaker(TestCase):

    #fixtures = ["app_testmaker"]


    def test__142996960498(self):
        r = self.client.get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['message']), u'
                There's no public problems available. You can <a class="button radius small" href="/accounts/login/">log in</a> or <a class="button radius small" href="">create an account</a> to start!
            ')
        self.assertEqual(unicode(r.context[-1]['icon']), u'prohibited')
    def test_jsi18n_142996960547(self):
        r = self.client.get('/jsi18n/', {})
        self.assertEqual(r.status_code, 200)
    def test_ajax_142996960585(self):
        r = self.client.get('/ajax/', {'help': '1', })
        self.assertEqual(r.status_code, 404)
    def test_problemsmy_142996960729(self):
        r = self.client.get('/problems/my/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['message']), u'
                There's no public problems available. You can <a class="button radius small" href="/accounts/login/">log in</a> or <a class="button radius small" href="">create an account</a> to start!
            ')
        self.assertEqual(unicode(r.context[-1]['icon']), u'prohibited')
    def test_jsi18n_142996960772(self):
        r = self.client.get('/jsi18n/', {})
        self.assertEqual(r.status_code, 200)
    def test_problemsdrafts_142996960884(self):
        r = self.client.get('/problems/drafts/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['message']), u'
                There's no public problems available. You can <a class="button radius small" href="/accounts/login/">log in</a> or <a class="button radius small" href="">create an account</a> to start!
            ')
        self.assertEqual(unicode(r.context[-1]['icon']), u'prohibited')
    def test_jsi18n_142996960921(self):
        r = self.client.get('/jsi18n/', {})
        self.assertEqual(r.status_code, 200)
    def test_problemscollaborating_142996961001(self):
        r = self.client.get('/problems/collaborating/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['message']), u'
                There's no public problems available. You can <a class="button radius small" href="/accounts/login/">log in</a> or <a class="button radius small" href="">create an account</a> to start!
            ')
        self.assertEqual(unicode(r.context[-1]['icon']), u'prohibited')
    def test_jsi18n_142996961041(self):
        r = self.client.get('/jsi18n/', {})
        self.assertEqual(r.status_code, 200)
    def test__142996961085(self):
        r = self.client.get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context[-1]['message']), u'
                There's no public problems available. You can <a class="button radius small" href="/accounts/login/">log in</a> or <a class="button radius small" href="">create an account</a> to start!
            ')
        self.assertEqual(unicode(r.context[-1]['icon']), u'prohibited')
    def test_jsi18n_142996961123(self):
        r = self.client.get('/jsi18n/', {})
        self.assertEqual(r.status_code, 200)
    def test_ajax_14299696116(self):
        r = self.client.get('/ajax/', {'help': '1', })
        self.assertEqual(r.status_code, 404)
