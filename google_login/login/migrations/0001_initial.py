# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BlackList'
        db.create_table('login_blacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=150)),
        ))
        db.send_create_signal('login', ['BlackList'])


    def backwards(self, orm):
        # Deleting model 'BlackList'
        db.delete_table('login_blacklist')


    models = {
        'login.blacklist': {
            'Meta': {'object_name': 'BlackList'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['login']