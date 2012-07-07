"""URL routing for storybase_story app"""

#import datetime
from django.conf.urls.defaults import patterns, url
#from haystack.query import SearchQuerySet
#from haystack.views import FacetedSearchView

#from storybase_story.forms import StoryFacetedSearchForm
from storybase_story.views import (ExploreStoriesView, 
    StoryBuilderView, StoryDetailView, StoryViewerView)

#sqs = SearchQuerySet().date_facet('pub_date', 
#                                   start_date=datetime.date(2009, 1, 1),
#                                   end_date=datetime.date.today(),
#                                   gap_by='month').facet('author') \
#                      .facet('school').facet('topic')

urlpatterns = patterns('',
#    url(r'search/', FacetedSearchView(form_class=StoryFacetedSearchForm,
#                                      searchqueryset=sqs),
#        name='story_search'),
    url(r'build/$', StoryBuilderView.as_view(), name='story_builder'),
    url(r'explore/$', ExploreStoriesView.as_view(), name='explore_stories'),
    url(r'stories/(?P<story_id>[0-9a-f]{32,32})/$',
        StoryDetailView.as_view(), name='story_detail_by_id'), 
    url(r'stories/(?P<slug>[0-9a-z-]+)/$',
        StoryDetailView.as_view(), name='story_detail'), 
    url(r'stories/(?P<story_id>[0-9a-f]{32,32})/viewer/$',
        StoryViewerView.as_view(), name='story_viewer_by_id'), 
    url(r'stories/(?P<slug>[0-9a-z-]+)/viewer/$',
        StoryViewerView.as_view(), name='story_viewer'), 
)
