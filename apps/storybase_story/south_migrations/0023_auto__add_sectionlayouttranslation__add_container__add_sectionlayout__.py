# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SectionLayoutTranslation'
        db.create_table('storybase_story_sectionlayouttranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('translation_id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='en', max_length=15)),
            ('layout', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storybase_story.SectionLayout'])),
            ('name', self.gf('storybase.fields.ShortTextField')()),
        ))
        db.send_create_signal('storybase_story', ['SectionLayoutTranslation'])

        # Adding model 'Container'
        db.create_table('storybase_story_container', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal('storybase_story', ['Container'])

        # Adding model 'SectionLayout'
        db.create_table('storybase_story_sectionlayout', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layout_id', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=32, blank=True)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('storybase_story', ['SectionLayout'])

        # Adding M2M table for field containers on 'SectionLayout'
        db.create_table('storybase_story_sectionlayout_containers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sectionlayout', models.ForeignKey(orm['storybase_story.sectionlayout'], null=False)),
            ('container', models.ForeignKey(orm['storybase_story.container'], null=False))
        ))
        db.create_unique('storybase_story_sectionlayout_containers', ['sectionlayout_id', 'container_id'])

        # Adding field 'SectionAsset.container'
        db.add_column('storybase_story_sectionasset', 'container', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storybase_story.Container'], null=True), keep_default=False)

        # Adding field 'Section.layout'
        db.add_column('storybase_story_section', 'layout', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storybase_story.SectionLayout'], null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'SectionLayoutTranslation'
        db.delete_table('storybase_story_sectionlayouttranslation')

        # Deleting model 'Container'
        db.delete_table('storybase_story_container')

        # Deleting model 'SectionLayout'
        db.delete_table('storybase_story_sectionlayout')

        # Removing M2M table for field containers on 'SectionLayout'
        db.delete_table('storybase_story_sectionlayout_containers')

        # Deleting field 'SectionAsset.container'
        db.delete_column('storybase_story_sectionasset', 'container_id')

        # Deleting field 'Section.layout'
        db.delete_column('storybase_story_section', 'layout_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'storybase_asset.asset': {
            'Meta': {'object_name': 'Asset'},
            'asset_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'asset_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'attribution': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'assets'", 'blank': 'True', 'to': "orm['storybase_asset.DataSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'default': "'CC BY-NC-SA'", 'max_length': '25'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assets'", 'null': 'True', 'to': "orm['auth.User']"}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'section_specific': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'draft'", 'max_length': '10'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'storybase_asset.dataset': {
            'Meta': {'object_name': 'DataSet'},
            'attribution': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dataset_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dataset_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'links_to_file': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'datasets'", 'null': 'True', 'to': "orm['auth.User']"}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'draft'", 'max_length': '10'})
        },
        'storybase_geo.geolevel': {
            'Meta': {'object_name': 'GeoLevel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['storybase_geo.GeoLevel']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'storybase_geo.location': {
            'Meta': {'object_name': 'Location'},
            'address': ('storybase.fields.ShortTextField', [], {'blank': 'True'}),
            'address2': ('storybase.fields.ShortTextField', [], {'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lng': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'name': ('storybase.fields.ShortTextField', [], {'blank': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'storybase_geo.place': {
            'Meta': {'object_name': 'Place'},
            'boundary': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['storybase_geo.Place']", 'null': 'True', 'through': "orm['storybase_geo.PlaceRelation']", 'blank': 'True'}),
            'geolevel': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'places'", 'null': 'True', 'to': "orm['storybase_geo.GeoLevel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('storybase.fields.ShortTextField', [], {}),
            'place_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        'storybase_geo.placerelation': {
            'Meta': {'unique_together': "(('parent', 'child'),)", 'object_name': 'PlaceRelation'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'place_parent'", 'to': "orm['storybase_geo.Place']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'place_child'", 'to': "orm['storybase_geo.Place']"})
        },
        'storybase_story.container': {
            'Meta': {'object_name': 'Container'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'storybase_story.section': {
            'Meta': {'object_name': 'Section'},
            'assets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'sections'", 'blank': 'True', 'through': "orm['storybase_story.SectionAsset']", 'to': "orm['storybase_asset.Asset']"}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['storybase_story.Section']", 'null': 'True', 'through': "orm['storybase_story.SectionRelation']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layout': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.SectionLayout']", 'null': 'True'}),
            'root': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'section_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sections'", 'to': "orm['storybase_story.Story']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storybase_story.sectionasset': {
            'Meta': {'object_name': 'SectionAsset'},
            'asset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_asset.Asset']"}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Container']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Section']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storybase_story.sectionlayout': {
            'Meta': {'object_name': 'SectionLayout'},
            'containers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'layouts'", 'blank': 'True', 'to': "orm['storybase_story.Container']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layout_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'storybase_story.sectionlayouttranslation': {
            'Meta': {'object_name': 'SectionLayoutTranslation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '15'}),
            'layout': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.SectionLayout']"}),
            'name': ('storybase.fields.ShortTextField', [], {}),
            'translation_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        'storybase_story.sectionrelation': {
            'Meta': {'object_name': 'SectionRelation'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'section_parent'", 'to': "orm['storybase_story.Section']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'section_child'", 'to': "orm['storybase_story.Section']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storybase_story.sectiontranslation': {
            'Meta': {'unique_together': "(('section', 'language'),)", 'object_name': 'SectionTranslation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '15'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Section']"}),
            'title': ('storybase.fields.ShortTextField', [], {}),
            'translation_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        'storybase_story.story': {
            'Meta': {'object_name': 'Story'},
            'assets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_asset.Asset']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'stories'", 'null': 'True', 'to': "orm['auth.User']"}),
            'byline': ('django.db.models.fields.TextField', [], {}),
            'contact_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'featured_assets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'featured_in_stories'", 'blank': 'True', 'to': "orm['storybase_asset.Asset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'default': "'CC BY-NC-SA'", 'max_length': '25'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_geo.Location']"}),
            'on_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_user.Organization']"}),
            'places': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_geo.Place']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_user.Project']"}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'draft'", 'max_length': '10'}),
            'story_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'structure_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'topics': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'stories'", 'blank': 'True', 'to': "orm['storybase_taxonomy.Category']"})
        },
        'storybase_story.storytemplate': {
            'Meta': {'object_name': 'StoryTemplate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Story']", 'null': 'True', 'blank': 'True'}),
            'template_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'time_needed': ('django.db.models.fields.CharField', [], {'max_length': '140', 'blank': 'True'})
        },
        'storybase_story.storytemplatetranslation': {
            'Meta': {'object_name': 'StoryTemplateTranslation'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '15'}),
            'story_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.StoryTemplate']"}),
            'title': ('storybase.fields.ShortTextField', [], {}),
            'translation_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        'storybase_story.storytranslation': {
            'Meta': {'unique_together': "(('story', 'language'),)", 'object_name': 'StoryTranslation'},
            'call_to_action': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '15'}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Story']"}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('storybase.fields.ShortTextField', [], {'blank': 'True'}),
            'translation_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        },
        'storybase_taxonomy.category': {
            'Meta': {'object_name': 'Category'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['storybase_taxonomy.Category']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'storybase_user.organization': {
            'Meta': {'object_name': 'Organization'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curated_stories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'curated_in_organizations'", 'blank': 'True', 'through': "orm['storybase_user.OrganizationStory']", 'to': "orm['storybase_story.Story']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'on_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organization_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'storybase_user.organizationstory': {
            'Meta': {'object_name': 'OrganizationStory'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_user.Organization']"}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Story']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'storybase_user.project': {
            'Meta': {'object_name': 'Project'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'curated_stories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'curated_in_projects'", 'blank': 'True', 'through': "orm['storybase_user.ProjectStory']", 'to': "orm['storybase_story.Story']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'on_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['storybase_user.Organization']"}),
            'project_id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'storybase_user.projectstory': {
            'Meta': {'object_name': 'ProjectStory'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_user.Project']"}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storybase_story.Story']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['storybase_story']
