# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Idea.deleted_by'
        db.add_column('dnstorm_idea', 'deleted_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='idea_deleted_by', null=True, to=orm['auth.User']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Idea.deleted_by'
        db.delete_column('dnstorm_idea', 'deleted_by_id')


    models = {
        u'app.alternative': {
            'Meta': {'object_name': 'Alternative', 'db_table': "'dnstorm_alternative'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'app.alternativeitem': {
            'Meta': {'object_name': 'AlternativeItem', 'db_table': "'dnstorm_alternative_item'"},
            'alternative': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Alternative']"}),
            'criteria': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Criteria']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['app.Idea']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {})
        },
        u'app.comment': {
            'Meta': {'object_name': 'Comment', 'db_table': "'dnstorm_comment'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']", 'null': 'True', 'blank': 'True'})
        },
        u'app.criteria': {
            'Meta': {'object_name': 'Criteria', 'db_table': "'dnstorm_criteria'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Criteria']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '90'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'app.idea': {
            'Meta': {'object_name': 'Idea', 'db_table': "'dnstorm_idea'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('ckeditor.fields.RichTextField', [], {}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'idea_deleted_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '90'})
        },
        u'app.invite': {
            'Meta': {'object_name': 'Invite', 'db_table': "'dnstorm_invite'"},
            'email': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"})
        },
        u'app.message': {
            'Meta': {'object_name': 'Message', 'db_table': "'dnstorm_message'"},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'subject': ('django.db.models.fields.TextField', [], {})
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
            'blind': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contributor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'contributor'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'criteria': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['app.Criteria']", 'null': 'True', 'blank': 'True'}),
            'description': ('ckeditor.fields.RichTextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'manager': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'manager'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'max': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '90'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'vote_author': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vote_count': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'voting': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'app.quantifier': {
            'Meta': {'object_name': 'Quantifier', 'db_table': "'dnstorm_quantifier'"},
            'format': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'help': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']", 'null': 'True', 'blank': 'True'})
        },
        u'app.quantifiervalue': {
            'Meta': {'object_name': 'QuantifierValue', 'db_table': "'dnstorm_quantifier_value'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']"}),
            'quantifier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Quantifier']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'app.vote': {
            'Meta': {'object_name': 'Vote', 'db_table': "'dnstorm_vote'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']"}),
            'weight': ('django.db.models.fields.SmallIntegerField', [], {})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
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