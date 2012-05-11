"""REST API for Stories"""

from django.conf.urls.defaults import url

from haystack.query import SearchQuerySet

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization

from storybase.utils import get_language_name
from storybase_story.models import Story
from storybase_taxonomy.models import Category
from storybase_user.models import Organization, Project

class StoryResource(ModelResource):
    # Explicitly declare fields that are on the translation model
    title = fields.CharField(attribute='title')
    summary = fields.CharField(attribute='summary')

    class Meta:
        queryset = Story.objects.filter(status__exact='published')
        resource_name = 'stories'
        allowed_methods = ['get']
	# Allow open access to this resource for now since it's read-only
        authentication = Authentication()
	authorization = ReadOnlyAuthorization()

    def override_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/explore%s$'  % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_explore'), name="api_get_explore"),
        ]

    def _get_facet_field_name(self, field_name):
        """Convert public filter name to underlying Haystack index field"""
	return field_name.rstrip('s') + '_ids'

    def _get_filter_field_name(self, field_name):
        """Convert underlying Haystack index field to public filter name"""
	return field_name.rstrip('_ids') + 's'

    def _get_facet_choices(self, field_name, items):
        """Build tuples of ids and human readable strings for a given facet"""
        getter_fn = getattr(self, '_get_facet_choices_%s' % field_name)
        return getter_fn(items)

    def _get_facet_choices_topic_ids(self, items):
        return [(obj.pk, obj.name) 
                for obj in Category.objects.filter(pk__in=items)]

    def _get_facet_choices_project_ids(self, items):
        return [(obj.project_id, obj.name) 
                for obj in Project.objects.filter(project_id__in=items)]

    def _get_facet_choices_organization_ids(self, items):
        return [(obj.organization_id, obj.name) 
                for obj in Organization.objects.filter(organization_id__in=items)]

    def _get_facet_choices_language_ids(self, items):
        return [(item, get_language_name(item)) for item in items]
            
    def get_explore(self, request, **kwargs):
	"""Custom endpoint to drive the drill-down in the "Explore" view"""
	# TODO: Implement paging
	# BOOKMARK
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

	sqs = SearchQuerySet().models(Story)

        filter_fields = ['topics', 'projects', 'organizations', 'languages']
	filters = {}
	for filter_field in filter_fields:
            facet_field = self._get_facet_field_name(filter_field)
            sqs = sqs.facet(facet_field)
            filter_values = request.GET.get(filter_field, '').split(',')
	    if filter_values:
                filters['%s__in' % facet_field] = filter_values
	if filters:
            sqs = sqs.filter(**filters)

        objects = []

	for result in sqs.all():
            bundle = self.build_bundle(obj=result.object, request=request)
	    bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        object_list = {
            'objects': objects,
        }

	for facet_field, items in sqs.facet_counts()['fields'].iteritems():
            filter_field = self._get_filter_field_name(facet_field)
            object_list[filter_field] = self._get_facet_choices(
                facet_field, [item[0] for item in items])

        return self.create_response(request, object_list)
