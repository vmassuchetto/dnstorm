# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Alternative.updated'
        db.alter_column('dnstorm_alternative', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Alternative.created'
        db.alter_column('dnstorm_alternative', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Criteria.updated'
        db.alter_column('dnstorm_criteria', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Criteria.created'
        db.alter_column('dnstorm_criteria', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))
        # Deleting field 'Idea.modified'
        db.delete_column('dnstorm_idea', 'modified')

        # Adding field 'Idea.created'
        db.add_column('dnstorm_idea', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Idea.updated'
        db.add_column('dnstorm_idea', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True),
                      keep_default=False)

        # Deleting field 'Message.modified'
        db.delete_column('dnstorm_message', 'modified')

        # Adding field 'Message.created'
        db.add_column('dnstorm_message', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True),
                      keep_default=False)

        # Deleting field 'Comment.modified'
        db.delete_column('dnstorm_comment', 'modified')

        # Adding field 'Comment.created'
        db.add_column('dnstorm_comment', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Comment.updated'
        db.add_column('dnstorm_comment', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Vote.alternative'
        db.add_column('dnstorm_vote', 'alternative',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Alternative'], null=True, blank=True),
                      keep_default=False)


        # Changing field 'Vote.idea'
        db.alter_column('dnstorm_vote', 'idea_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.Idea'], null=True))
        # Deleting field 'Problem.modified'
        db.delete_column('dnstorm_problem', 'modified')

        # Adding field 'Problem.created'
        db.add_column('dnstorm_problem', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Problem.updated'
        db.add_column('dnstorm_problem', 'updated',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Problem.last_activity'
        db.add_column('dnstorm_problem', 'last_activity',
                      self.gf('django.db.models.fields.DateTimeField')(default='2000-01-01', auto_now=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):

        # Changing field 'Alternative.updated'
        db.alter_column('dnstorm_alternative', 'updated', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Alternative.created'
        db.alter_column('dnstorm_alternative', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Criteria.updated'
        db.alter_column('dnstorm_criteria', 'updated', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Criteria.created'
        db.alter_column('dnstorm_criteria', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Adding field 'Idea.modified'
        db.add_column('dnstorm_idea', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=1999, blank=True),
                      keep_default=False)

        # Deleting field 'Idea.created'
        db.delete_column('dnstorm_idea', 'created')

        # Deleting field 'Idea.updated'
        db.delete_column('dnstorm_idea', 'updated')

        # Adding field 'Message.modified'
        db.add_column('dnstorm_message', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=1999, blank=True),
                      keep_default=False)

        # Deleting field 'Message.created'
        db.delete_column('dnstorm_message', 'created')

        # Adding field 'Comment.modified'
        db.add_column('dnstorm_comment', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=1999, blank=True),
                      keep_default=False)

        # Deleting field 'Comment.created'
        db.delete_column('dnstorm_comment', 'created')

        # Deleting field 'Comment.updated'
        db.delete_column('dnstorm_comment', 'updated')

        # Deleting field 'Vote.alternative'
        db.delete_column('dnstorm_vote', 'alternative_id')


        # Changing field 'Vote.idea'
        db.alter_column('dnstorm_vote', 'idea_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1999, to=orm['app.Idea']))
        # Adding field 'Problem.modified'
        db.add_column('dnstorm_problem', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, default=1999, blank=True),
                      keep_default=False)

        # Deleting field 'Problem.created'
        db.delete_column('dnstorm_problem', 'created')

        # Deleting field 'Problem.updated'
        db.delete_column('dnstorm_problem', 'updated')

        # Deleting field 'Problem.last_activity'
        db.delete_column('dnstorm_problem', 'last_activity')


    models = {
        u'app.alternative': {
            'Meta': {'object_name': 'Alternative', 'db_table': "'dnstorm_alternative'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2001-01-01'", 'auto_now': 'True', 'blank': 'True'})
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
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Criteria']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '90'}),
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
        u'app.invite': {
            'Meta': {'object_name': 'Invite', 'db_table': "'dnstorm_invite'"},
            'email': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Problem']"})
        },
        u'app.message': {
            'Meta': {'object_name': 'Message', 'db_table': "'dnstorm_message'"},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now_add': 'True', 'blank': 'True'}),
            'criteria': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['app.Criteria']", 'null': 'True', 'blank': 'True'}),
            'description': ('ckeditor.fields.RichTextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_activity': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'manager': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'manager'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'max': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'open': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '90'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': "'2000-01-01'", 'auto_now': 'True', 'blank': 'True'}),
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
            'alternative': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Alternative']", 'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idea': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['app.Idea']", 'null': 'True', 'blank': 'True'}),
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