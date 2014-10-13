# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Criteria.author'
        db.add_column('dnstorm_criteria', 'author',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['auth.User']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Criteria.author'
        db.delete_column('dnstorm_criteria', 'author_id')


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
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.comment': {
            'Meta': {'object_name': 'Comment', 'db_table': "'dnstorm_comment'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']", 'null': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']", 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'})
        },
        u'app.criteria': {
            'Meta': {'object_name': 'Criteria', 'db_table': "'dnstorm_criteria'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
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
            'coauthor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'idea_coauthor'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'content': ('ckeditor.fields.RichTextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
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
            'coauthor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'problem_coauthor'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'contributor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'contributor'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'criteria': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['app.Criteria']", 'symmetrical': 'False'}),
            'description': ('ckeditor.fields.RichTextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_activity': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vote_idea'", 'null': 'True', 'to': u"orm['app.Idea']"})
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