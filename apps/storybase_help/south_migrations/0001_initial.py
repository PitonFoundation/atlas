# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'HelpTranslation'
        db.create_table('storybase_help_helptranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('translation_id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='en', max_length=15)),
            ('help', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storybase_help.Help'])),
            ('title', self.gf('storybase.fields.ShortTextField')(blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('storybase_help', ['HelpTranslation'])

        # Adding model 'Help'
        db.create_table('storybase_help_help', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('help_id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=50, blank=True)),
        ))
        db.send_create_signal('storybase_help', ['Help'])


    def backwards(self, orm):
        
        # Deleting model 'HelpTranslation'
        db.delete_table('storybase_help_helptranslation')

        # Deleting model 'Help'
        db.delete_table('storybase_help_help')


    models = {
        'storybase_help.help': {
            'Meta': {'object_name': 'Help'},
            'help_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'storybase_help.helptranslation': {
            'Meta': {'object_name': 'HelpTranslation'},
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'help': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_help.Help']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '15'}),
            'title': ('storybase.fields.ShortTextField', [], {'blank': 'True'}),
            'translation_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        }
    }

    complete_apps = ['storybase_help']
