"""REST API for Stories"""

from django.conf.urls.defaults import url

from haystack.query import SearchQuerySet

from tastypie import fields
from tastypie.bundle import Bundle
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
    url = fields.CharField(attribute='get_absolute_url')
    topics = fields.ListField(readonly=True)
    organizations = fields.ListField(readonly=True)
    projects = fields.ListField(readonly=True)
    languages = fields.ListField(readonly=True)

    class Meta:
        queryset = Story.objects.filter(status__exact='published')
        resource_name = 'stories'
        allowed_methods = ['get']
	# Allow open access to this resource for now since it's read-only
        authentication = Authentication()
	authorization = ReadOnlyAuthorization()
	# Hide the underlying id
	excludes = ['id']
	# Filter arguments for custom explore endpoint
	explore_filter_fields = ['topics', 'projects', 'organizations', 'languages']

    def override_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/explore%s$'  % (self._meta.resource_name, trailing_slash()), self.wrap_view('explore_get_list'), name="api_explore_get_list"),
            url(r"^(?P<resource_name>%s)/(?P<story_id>[0-9a-f]{32,32})/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def get_resource_uri(self, bundle_or_obj):
        """
        Handles generating a resource URI for a single resource.

        Uses the model's ``story_id`` in order to create the URI.
        """
        kwargs = {
            'resource_name': self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.story_id
        else:
            kwargs['pk'] = bundle_or_obj.story_id

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def dehydrate_topics(self, bundle):
        """Populate a list of topic ids and names in the response objects"""
        return [(topic.pk, topic.name) for topic in bundle.obj.topics.all()]

    def dehydrate_organizations(self, bundle):
        """
        Populate a list of organization ids and names in the response objects
	"""
	return [(organization.organization_id, organization.name)
                for organization in bundle.obj.organizations.all()]

    def dehydrate_projects(self, bundle):
        """
        Populate a list of project ids and names in the response objects
	"""
	return [(project.project_id, project.name)
                for project in bundle.obj.projects.all()]

    def dehydrate_languages(self, bundle):
        """
        Populate a list of language codes and names in the response objects
	"""
        return [(code, get_language_name(code))
                for code in bundle.obj.get_languages()]

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

    def explore_get_result_list(self, request):
	sqs = SearchQuerySet().models(Story)
	filter_fields = self._meta.explore_filter_fields
	for filter_field in filter_fields:
            facet_field = self._get_facet_field_name(filter_field)
            sqs = sqs.facet(facet_field)

	return sqs

    def explore_build_filters(self, filters=None):
	applicable_filters = {}
	filter_fields = self._meta.explore_filter_fields
	for filter_field in filter_fields:
            facet_field = self._get_facet_field_name(filter_field)
            filter_values = filters.get(filter_field, '').split(',')
	    if filter_values:
                applicable_filters['%s__in' % facet_field] = filter_values

        return applicable_filters

    def explore_apply_filters(self, request, applicable_filters):
	object_list = self.explore_get_result_list(request)
	if applicable_filters:
            return object_list.filter(**applicable_filters)
        else:
            return object_list
        
    def explore_result_get_list(self, request=None, **kwargs):
        filters = {}

        if hasattr(request, 'GET'):
            # Grab a mutable copy.
            filters = request.GET.copy()

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters = self.build_filters(filters=filters)
	results = self.explore_apply_filters(request, applicable_filters)
	return results
            
    def explore_get_list(self, request, **kwargs):
	"""Custom endpoint to drive the drill-down in the "Explore" view"""
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        objects = []
	results = self.explore_result_get_list(request, **kwargs)

	for result in results:
            bundle = self.build_bundle(obj=result.object, request=request)
	    bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        paginator = self._meta.paginator_class(request.GET, objects, resource_uri=self.get_resource_list_uri(), limit=self._meta.limit)
        to_be_serialized = paginator.page()

	for facet_field, items in results.facet_counts()['fields'].iteritems():
            filter_field = self._get_filter_field_name(facet_field)
            to_be_serialized[filter_field] = self._get_facet_choices(
                facet_field, [item[0] for item in items])

        return self.create_response(request, to_be_serialized)
