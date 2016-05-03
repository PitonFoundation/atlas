from haystack import indexes

from storybase.search.fields import GeoHashMultiValueField, TextSpellField
from storybase_story.models import Story


class StoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.FacetCharField(model_attr='author')
    published = indexes.FacetDateTimeField(model_attr='published')
    created = indexes.FacetDateTimeField(model_attr='created')
    last_edited = indexes.FacetDateTimeField(model_attr='last_edited')
    # TODO: Use a meta class to dynamically populate these from "official"
    # tag sets
    topic_ids = indexes.FacetMultiValueField()
    organization_ids = indexes.FacetMultiValueField()
    project_ids = indexes.FacetMultiValueField()
    language_ids = indexes.FacetMultiValueField()
    place_ids = indexes.FacetMultiValueField()
    badge_ids = indexes.FacetMultiValueField()
    points = GeoHashMultiValueField()
    num_points = indexes.IntegerField()
    suggestions = TextSpellField()

    def get_model(self):
        return Story

    def prepare_topic_ids(self, obj):
        return [topic.id for topic in obj.topics.all()]

    def prepare_organization_ids(self, obj):
        return [organization.organization_id for organization in obj.organizations.all()]

    def prepare_project_ids(self, obj):
        return [project.project_id for project in obj.projects.all()]

    def prepare_language_ids(self, obj):
        return obj.get_languages()

    def prepare_place_ids(self, obj):
        return [place.place_id for place in obj.inherited_places]

    def prepare_badge_ids(self, obj):
        return [badge.id for badge in obj.badges.all()]

    def prepare_points(self, obj):
        return ["%s,%s" % (point[0], point[1]) for point in obj.points]

    def prepare_num_points(self, obj):
        return len(obj.points)

    def prepare(self, obj):
        prepared_data = super(StoryIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data

    def index_queryset(self, using=None):
        """
        Get the default QuerySet to index when doing a full update.

        Excludes unpublish stories, template stories, and connected stories.
        """
        return Story.objects.filter(status__exact='published',
                                    is_template=False)\
                            .exclude(source__relation_type='connected')

    def should_update(self, instance, **kwargs):
        """
        Determine if an object should be updated in the index.
        """
        should_update = True
        translation_set = getattr(instance, instance.translation_set)
        if translation_set.count() == 0:
            should_update = False
        if 'action' in kwargs:
            # The signal is m2m_changed.  We only want to update
            # on the post actions
            if kwargs['action'] in ('pre_add', 'pre_remove', 'pre_clear'):
                should_update = False
        return should_update

    def should_remove_on_update(self, instance, **kwargs):
        if instance.status != 'published':
            return True

        if instance.is_template == True:
            return True

        return False

    def update_object(self, instance, using=None, **kwargs):
        """
        Update the index for a single object. Attached to the class's
        post-save hook.

        This version removes unpublished stories from the index
        """
        if self.should_remove_on_update(instance, **kwargs):
            self.remove_object(instance, using, **kwargs)
        else:
            super(StoryIndex, self).update_object(instance, using, **kwargs)

    def translation_update_object(self, instance, **kwargs):
        """Signal handler for updating story index when the translation changes"""
        # Deal with race condition when stories are deleted
        # See issue #138
        try:
            self.update_object(instance.story)
        except Story.DoesNotExist:
            pass

    def location_update_object(self, instance, **kwargs):
        """Signal handler for updating story index when a related location changes"""
        for story in instance.stories.all():
            self.update_object(story)

    def section_translation_update_object(self, instance, **kwargs):
        """
        Signal handler for updating story index when a related section
        translation changes

        This is needed because the section titles in all languages are part
        of the document field of the index.

        """
        self.update_object(instance.section.story)

    def asset_translation_update_object(self, instance, **kwargs):
        """
        Signal handler for updating story index when a related text asset
        translation changes

        This is needed because the text from text assets is part of the
        document field in the index.

        """
        stories = []
        if instance.asset.type == 'text':
            for section in instance.asset.sections.all():
                # Should I use a set here to make this faster?
                if section.story not in stories:
                    stories.append(section.story)

            for story in stories:
                self.update_object(story)

    def cache_story_for_delete(self, instance, **kwargs):
        """
        Store a reference to the section asset's story

        This makes the story available to post_delete signal handlers, because
        it won't neccessarily be available via instance.section.story at
        that point.

        This is designed to be attached to the pre_delete signal

        """
        instance._story = instance.section.story

    def asset_relation_update_object(self, instance, **kwargs):
        """
        Signal handler for when an asset to section relationship is
        created or destroyed.

        This is needed because the text from assets is part of the
        document field of the index.

        """
        if instance.asset.type == 'text':
            # Try using the cached story. This will be present if
            # we're deleting the section asset
            story = getattr(instance, '_story', None)
            if story is None:
                # No cached story present, it's safe to get it by following
                # the relations
                story = instance.section.story
            self.update_object(story)
