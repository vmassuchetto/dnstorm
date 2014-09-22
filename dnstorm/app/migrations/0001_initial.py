# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Option'
        db.create_table('dnstorm_option', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'app', ['Option'])

        # Adding model 'Criteria'
        db.create_table('dnstorm_criteria', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=90)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=60, populate_from='name', unique_with=())),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('help_star1', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('help_star2', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('help_star3', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('help_star4', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('help_star5', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2001-01-01', auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default='2001-01-01', auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Criteria'])

        # Adding model 'Problem'
        db.create_table('dnstorm_problem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=90)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=60, populate_from='title', unique_with=())),
            ('description', self.gf('ckeditor.fields.RichTextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='author', to=orm['auth.User'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True)),
            ('last_activity', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Problem'])

        # Adding M2M table for field criteria on 'Problem'
        m2m_table_name = db.shorten_name('dnstorm_problem_criteria')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('problem', models.ForeignKey(orm[u'app.problem'], null=False)),
            ('criteria', models.ForeignKey(orm[u'app.criteria'], null=False))
        ))
        db.create_unique(m2m_table_name, ['problem_id', 'criteria_id'])

        # Adding M2M table for field contributor on 'Problem'
        m2m_table_name = db.shorten_name('dnstorm_problem_contributor')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('problem', models.ForeignKey(orm[u'app.problem'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['problem_id', 'user_id'])

        # Adding model 'Invitation'
        db.create_table('dnstorm_invitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('problem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Problem'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'app', ['Invitation'])

        # Adding model 'Idea'
        db.create_table('dnstorm_idea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('problem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Problem'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=90)),
            ('content', self.gf('ckeditor.fields.RichTextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='idea_deleted_by', null=True, to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Idea'])

        # Adding model 'IdeaCriteria'
        db.create_table('dnstorm_idea_criteria', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('idea', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Idea'])),
            ('criteria', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Criteria'])),
            ('stars', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'app', ['IdeaCriteria'])

        # Adding model 'Comment'
        db.create_table('dnstorm_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('problem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Problem'], null=True, blank=True)),
            ('idea', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Idea'], null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('deleted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='comment_deleted_by', null=True, to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Comment'])

        # Adding model 'Alternative'
        db.create_table('dnstorm_alternative', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('problem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Problem'])),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2001-01-01', auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Alternative'])

        # Adding M2M table for field idea on 'Alternative'
        m2m_table_name = db.shorten_name('dnstorm_alternative_idea')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('alternative', models.ForeignKey(orm[u'app.alternative'], null=False)),
            ('idea', models.ForeignKey(orm[u'app.idea'], null=False))
        ))
        db.create_unique(m2m_table_name, ['alternative_id', 'idea_id'])

        # Adding model 'Vote'
        db.create_table('dnstorm_vote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('idea', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vote_idea', null=True, to=orm['app.Idea'])),
            ('comment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vote_comment', null=True, to=orm['app.Alternative'])),
            ('alternative', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vote_alternative', null=True, to=orm['app.Alternative'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('weight', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default='2001-01-01', auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'app', ['Vote'])


    def backwards(self, orm):
        # Deleting model 'Option'
        db.delete_table('dnstorm_option')

        # Deleting model 'Criteria'
        db.delete_table('dnstorm_criteria')

        # Deleting model 'Problem'
        db.delete_table('dnstorm_problem')

        # Removing M2M table for field criteria on 'Problem'
        db.delete_table(db.shorten_name('dnstorm_problem_criteria'))

        # Removing M2M table for field contributor on 'Problem'
        db.delete_table(db.shorten_name('dnstorm_problem_contributor'))

        # Deleting model 'Invitation'
        db.delete_table('dnstorm_invitation')

        # Deleting model 'Idea'
        db.delete_table('dnstorm_idea')

        # Deleting model 'IdeaCriteria'
        db.delete_table('dnstorm_idea_criteria')

        # Deleting model 'Comment'
        db.delete_table('dnstorm_comment')

        # Deleting model 'Alternative'
        db.delete_table('dnstorm_alternative')

        # Removing M2M table for field idea on 'Alternative'
        db.delete_table(db.shorten_name('dnstorm_alternative_idea'))

        # Deleting model 'Vote'
        db.delete_table('dnstorm_vote')


    models = {
        u'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': u"orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'data': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'app.alternative': {
            'Meta': {'object_name': 'Alternative', 'db_table': "'dnstorm_alternative'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['app.Idea']", 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"})
        },
        u'app.comment': {
            'Meta': {'object_name': 'Comment', 'db_table': "'dnstorm_comment'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comment_deleted_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']", 'null': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.criteria': {
            'Meta': {'object_name': 'Criteria', 'db_table': "'dnstorm_criteria'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'help_star1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'help_star2': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'help_star3': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'help_star4': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'help_star5': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '60', 'populate_from': "'name'", 'unique_with': '()'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.idea': {
            'Meta': {'object_name': 'Idea', 'db_table': "'dnstorm_idea'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('ckeditor.fields.RichTextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'idea_deleted_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.ideacriteria': {
            'Meta': {'object_name': 'IdeaCriteria', 'db_table': "'dnstorm_idea_criteria'"},
            'criteria': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Criteria']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']"}),
            'stars': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        u'app.invitation': {
            'Meta': {'object_name': 'Invitation', 'db_table': "'dnstorm_invitation'"},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"})
        },
        u'app.option': {
            'Meta': {'object_name': 'Option', 'db_table': "'dnstorm_option'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'app.problem': {
            'Meta': {'object_name': 'Problem', 'db_table': "'dnstorm_problem'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'author'", 'to': u"orm['auth.User']"}),
            'contributor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'contributor'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'criteria': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['app.Criteria']", 'symmetrical': 'False'}),
            'description': ('ckeditor.fields.RichTextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_activity': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '60', 'populate_from': "'title'", 'unique_with': '()'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.vote': {
            'Meta': {'object_name': 'Vote', 'db_table': "'dnstorm_vote'"},
            'alternative': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vote_alternative'", 'null': 'True', 'to': u"orm['app.Alternative']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vote_comment'", 'null': 'True', 'to': u"orm['app.Alternative']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vote_idea'", 'null': 'True', 'to': u"orm['app.Idea']"}),
            'weight': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['app']