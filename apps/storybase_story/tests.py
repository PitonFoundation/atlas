# vim: set fileencoding=utf-8 :
"""Unit tests for storybase_story app"""

import datetime
import json
from time import sleep

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from django.utils import simplejson

from tastypie.bundle import Bundle
from tastypie.test import ResourceTestCase

from storybase.admin import toggle_featured
from storybase.tests.base import SloppyComparisonTestMixin, FixedTestApiClient
from storybase.utils import slugify
from storybase_asset.models import (Asset, HtmlAsset, HtmlAssetTranslation,
                                    create_html_asset)
from storybase_geo.models import Location, GeoLevel, Place
from storybase_help.models import create_help 
from storybase_story.api import (SectionAssetResource, SectionResource, 
                                 StoryResource)
from storybase_story.forms import SectionRelationAdminForm
from storybase_story.models import (Container, Story, StoryTranslation,
    Section, SectionAsset, SectionLayout, SectionRelation, StoryTemplate,
    StoryRelation,
    create_story, create_section, set_asset_license)
from storybase_story.templatetags.story import container
from storybase_story.views import StoryBuilderView
from storybase_taxonomy.models import Category, create_category
from storybase_user.models import (Organization, Project,
                                   create_organization, create_project)


class SectionRelationFormTest(TestCase):
    """Test custom forms for SectionRelations"""
    fixtures = ['section_layouts.json']

    def test_select_label(self):
        """
        Test that both Section title and its Story title appear in select
        labels
        """
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Test Section 1", story=story, layout=layout)
        section2 = create_section(title="Test Section 2", story=story, layout=layout)
        form = SectionRelationAdminForm()
        choices_list = list(form.fields['parent'].widget.choices)
        self.assertIn(story.title, choices_list[1][1])
        self.assertIn(story.title, choices_list[2][1])


class StoryModelTest(TestCase, SloppyComparisonTestMixin):
    """Unit tests for Story Model"""
    def test_auto_slug(self):
        """Test slug field is set automatically"""
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        story = Story()
        story.save()
        story_translation = StoryTranslation(title=title, story=story)
        story_translation.save()
        self.assertEqual(story.slug, slugify(title))

    def test_get_languages(self):
        """Test Story.get_languages() method for a single translation"""
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        self.assertEqual([settings.LANGUAGE_CODE], story.get_languages())

    def test_get_languages_multiple(self):
        """Test Story.get_languages() for multiple translations"""
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        translation = StoryTranslation(story=story, title="Spanish Title",
            summary="Spanish Summary", language="es")
        translation.save()
        story_languages = story.get_languages()
        self.assertEqual(len(story_languages), 2)
        for code in (settings.LANGUAGE_CODE, 'es'):
            self.assertIn(code, story_languages)

    def test_auto_set_published_on_create(self):
        """
        Test that the published date gets set on object creation when the
        status is set to published
        """
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline,
                             status='published')
        self.assertNowish(story.published)

    def test_auto_set_published_on_status_change(self):
        """
        Test that the published date gets set when the status is changed
        to published
        """ 
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        # Default status should be draft 
        self.assertEqual(story.status, 'draft')
        # and there should be no published date
        self.assertEqual(story.published, None)
        story.status = 'published'
        story.save()
        self.assertNowish(story.published)

    def test_contributor_name(self):
        """
        Test that the Story.contributor_name returns the first name
        and last initial of the Story's author user
        """
        user = User.objects.create(username='admin', first_name='Jordan',
                                   last_name='Wirfs-Brock')
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline,
                             author=user)
        self.assertEqual(story.contributor_name, 'Jordan W.')


    def test_contributor_name_no_last_name(self):
        """
        Test that the Story.contributor_name returns the first name
        of the Story's author user when no last name is set
        """
        user = User.objects.create(username='admin', first_name='Jordan')
                                   
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline,
                             author=user)
        self.assertEqual(story.contributor_name, 'Jordan')

    def test_contributor_name_no_names(self):
        """
        Test that the Story.contributor_name returns an empty string 
         when there is no first or last name
        """
        user = User.objects.create(username='admin')
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline,
                             author=user)
        self.assertEqual(story.contributor_name, '')

    def test_builder_url(self):
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        self.assertEqual(story.builder_url(), "/build/%s/" % (story.story_id))

    def test_builder_url_connected(self):
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        story2 = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published')
        StoryRelation.objects.create(source=story, target=story2,
                                     relation_type='connected')
        self.assertEqual(story2.builder_url(), 
                         "/stories/%s/build-connected/%s/" % 
                         (story.slug, story2.story_id))

    # TODO: Move this sot StorySignalsTest
    def test_add_assets_signal(self):
        """
        Test that an asset is also added to the assets relation
        when it's added to the featured_assets relation.
        """
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        asset = create_html_asset(type='text', title='Test Asset', 
                                  body='Test content')
        self.assertEqual(story.assets.count(), 0)
        story.featured_assets.add(asset)
        story.save()
        self.assertEqual(story.assets.count(), 1)

    def test_render_featured_asset_empty(self): 
        """
        Test that Story.render_featured_assets returns an empty string
        when the story has no featured assets and there isn't an
        acceptable default.
        """
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        self.assertEqual(story.assets.count(), 0)
        self.assertEqual(story.render_featured_asset(), '<img src="/static/img/default-image-story-335x200.png" />')

    def test_get_featured_asset_thumbnail_url_empty(self):
        """
        Test that Story.featured_asset_thumbnail_url returns None 
        when the story has no featured assets and there isn't an
        acceptable default.
        """
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        self.assertEqual(story.assets.count(), 0)
        self.assertEqual(story.featured_asset_thumbnail_url(), '/static/img/default-image-story-222x132.png')

    def test_unique_slug(self):
        """
        Test that the unique_slug function works for the Story model's
        title.
        """
        # While unique_slug lives in the storybase app, I test it here
        # because this is the app where the relevent models live
        from storybase.utils import unique_slugify
        story = create_story(title="Test Story", summary="Test Summary",
            byline="Test Byline")
        self.assertEqual(story.slug, "test-story")
        story2 = create_story(title="Test Story", summary="Test Summary 2",
            byline="Test Byline 2", slug="non-colliding-slug")
        self.assertEqual(story2.slug, "non-colliding-slug")
        unique_slugify(story2, story2.title)
        self.assertEqual(story2.slug, "test-story-2")

    def test_auto_unique_slug(self):
        """
        Test that a story's slug is automatically set to a unique value.
        """
        story = create_story(title="Test Story", summary="Test Summary",
            byline="Test Byline")
        self.assertEqual(story.slug, "test-story")
        story2 = create_story(title="Test Story", summary="Test Summary 2",
            byline="Test Byline 2")
        self.assertEqual(story2.slug, "test-story-2")
        self.assertEqual(Story.objects.filter(slug="test-story").count(), 1)


class StoryPermissionTest(TestCase):
    """Test case for story permissions"""
    def setUp(self):
        from django.contrib.auth.models import Group
        self.admin_group = Group.objects.create(name=settings.ADMIN_GROUP_NAME)
        self.user1 = User.objects.create_user("test1", "test1@example.com",
                                              "test1")
        self.user2 = User.objects.create_user("test2", "test2@example.com",
                                              "test2")
        self.story = create_story(title="Test Story", summary="Test Summary",
                                  byline="Test Byline", status='published',
                                  author=self.user1)

    def test_user_can_change_as_author(self):
        """Test that author has permissions to change their story"""
        self.assertTrue(self.story.user_can_change(self.user1))

    def test_user_can_change_not_author(self):
        """Test that a user doesn't have permissions to change another users story"""
        self.assertFalse(self.story.user_can_change(self.user2))

    def test_user_can_change_superuser(self):
        """Test that a superuser can change another user's story"""
        self.assertFalse(self.story.user_can_change(self.user2))
        self.user2.is_superuser = True
        self.user2.save()
        self.assertTrue(self.story.user_can_change(self.user2))

    def test_user_can_change_admin(self):
        """Test that a member of the admin group can change another user's story"""
        self.assertFalse(self.story.user_can_change(self.user2))
        self.user2.groups.add(self.admin_group)
        self.user2.save()
        self.assertTrue(self.story.user_can_change(self.user2))

    def test_user_can_change_inactive(self):
        """Test that an inactive user can't change their own story"""
        self.assertTrue(self.story.user_can_change(self.user1))
        self.user1.is_active = False 
        self.assertFalse(self.story.user_can_change(self.user1))

    def test_has_perm_change(self):
        """Test that has_perm(user, 'change') calls through to user_can_change"""
        perm = "change"
        self.assertTrue(self.story.has_perm(self.user1, perm))
        self.assertFalse(self.story.has_perm(self.user2, perm))


class StorySignalsTest(TestCase):
    """Tests for signals sent by the Story model"""
    def test_set_asset_license(self):
        """Test the set_asset_license signal handler"""

        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        asset = create_html_asset(type='text', title='Test Asset', 
                                  body='Test content')
        story.assets.add(asset)
        story.save()
        self.assertEqual(story.license, '')
        self.assertEqual(asset.license, '')
        story.license = 'CC BY-NC-SA'
        set_asset_license(sender=Story, instance=story)
        asset = Asset.objects.get(pk=asset.pk)
        self.assertEqual(asset.license, story.license)

    def test_set_asset_license_connected(self):
        """
        Test that the set_asset_licsense handler works when the
        a Story is saved.
        """
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        asset = create_html_asset(type='text', title='Test Asset', 
                                  body='Test content')
        story.assets.add(asset)
        story.save()
        self.assertEqual(story.license, '')
        self.assertEqual(asset.license, '')
        story.license = 'CC BY-NC-SA'
        story.save()
        asset = Asset.objects.get(pk=asset.pk)
        self.assertEqual(asset.license, story.license)

    def _test_invalidate_related_cache(self, field_name, cache_field_name,
                                       related_method, related_instance):
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        key = "storybase_story.story:%s:%s:en" % (story.pk, cache_field_name)
        test_value = "TEST"
        cache.set(key, "TEST")
        self.assertEqual(cache.get(key), test_value)
        related = getattr(story, field_name)
        fn = getattr(related, related_method)
        fn(related_instance)
        story.save()
        self.assertEqual(cache.get(key), None)

    def test_invalidate_points_cache(self):
        location_attrs = {
            "name": "The Piton Foundation",
            "address": "370 17th St",
            "address2": "#5300",
            "city": "Denver",
            "state": "CO",
            "postcode": "80202",
        }
        location = Location.objects.create(**location_attrs) 
        self._test_invalidate_related_cache('locations', 'points', 'add',
                                             location)

    def test_invalidate_topics_cache(self):
        topic = create_category(name="Schools")
        self._test_invalidate_related_cache('topics', 'topics', 'add', topic)
                                           

    def test_invalidate_organizations_cache(self):
        org = create_organization(name="Mile High Connects")
        self._test_invalidate_related_cache('organizations', 'organizations',
                                            'add', org)

    def test_invalidate_projects_cache(self):
        # BOOKMARK
        pass



class StoryAdminTest(TestCase):
    fixtures = ['section_layouts.json']

    """Test case for the Story model's Django admin interface"""
    def test_toggle_featured(self):
        """
        Test the admin action function that toggles the "featured
        on homepage" flag.
        """
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             on_homepage=True)
        story2 = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             on_homepage=False)
        self.assertEqual(story.on_homepage, True)
        self.assertEqual(story2.on_homepage, False)
        toggle_featured(None, None,
                        Story.objects.filter(pk__in=[story.pk, story2.pk]))
        story = Story.objects.get(pk=story.pk)
        story2 = Story.objects.get(pk=story2.pk)
        self.assertEqual(story.on_homepage, False)
        self.assertEqual(story2.on_homepage, True)


class StoryApiTest(TestCase):
    """Test case for the internal Story API"""

    def test_create_story(self):
        """Test create_story() creates a Story instance"""
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        with self.assertRaises(Story.DoesNotExist):
            Story.objects.get(storytranslation__title=title)
        story = create_story(title=title, summary=summary, byline=byline)
        self.assertEqual(story.title, title)
        self.assertEqual(story.summary, summary)
        self.assertEqual(story.byline, byline)
        retrieved_story = Story.objects.get(pk=story.pk)
        self.assertEqual(retrieved_story.title, title)
        self.assertEqual(retrieved_story.summary, summary)
        self.assertEqual(retrieved_story.byline, byline)

class StoryManagerTest(TestCase):
    """Test case for custom manager for Story model"""

    def has_story_title(self, title, stories):
	"""
	Utility method to check that a given title is in a queryset of stories
	"""
	for story in stories:
	       break
	else:
	    self.fail("Story with title '%s' not found" % title)

    def test_on_homepage(self):
        """
	Test that Story.objects.on_homepage() returns filtered queryset
	"""
	homepage_titles = (
	    "The Power of Play: Playground Locations in the Children's Corridor",
	    "Birth Trends in the Children's Corridor: Focus on Foreign-born Mothers",
	    "Shattered Dreams: Revitalizing Hope in Original Aurora",
	    "A School Fight Rallies Hinkley High School Mothers to Organize",
	    "Transportation Challenges Limit Education Choices for Denver Parents")
	other_titles = ("Story 1", "Story 2")
	for title in homepage_titles + other_titles:
	    on_homepage = title in homepage_titles
	    create_story(title=title, on_homepage=on_homepage,
			 status='published')
	homepage_stories = Story.objects.on_homepage()
	self.assertEqual(homepage_stories.count(), len(homepage_titles))
	for title in homepage_titles:
	    self.has_story_title(title, homepage_stories)

    def test_on_homepage_published_only(self):
	"""
	Test that story.objects.on_homepage() returns only published stories
	"""
	published_titles = (
	    "The Power of Play: Playground Locations in the Children's Corridor",
	    "Birth Trends in the Children's Corridor: Focus on Foreign-born Mothers")
	unpublished_titles = (
	    "Shattered Dreams: Revitalizing Hope in Original Aurora",
	    "A School Fight Rallies Hinkley High School Mothers to Organize",
	    "Transportation Challenges Limit Education Choices for Denver Parents")
	for title in published_titles + unpublished_titles:
	    status = 'draft'
	    if title in published_titles:
		status = 'published'
	    create_story(title=title, on_homepage=True, status=status)
			 
	homepage_stories = Story.objects.on_homepage()
	self.assertEqual(homepage_stories.count(), len(published_titles))
	for title in published_titles:
	    self.has_story_title(title, homepage_stories)


class RelatedStoriesTest(TestCase):
    """Tests for managing relationships between stories"""
    def setUp(self):
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        self.story = create_story(title="Test Story", summary="Test Summary",
                                  byline="Test Byline", status='published',
                                  author=self.user)

    def test_create_relation(self):
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             connected_prompt="Test connected prompt",
                             allow_connected=True,
                             status='published',
                             author=self.user)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='connected')
        self.assertEqual(len(self.story.related_stories.all()), 1)
        self.assertEqual(self.story.related_stories.all()[0], story)

    def test_connected_stories(self):
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        story2 = create_story(title="Test Related Story 2", 
                              summary="Test Related Story Summary 2",
                              byline="Test Related Story Byline 2",
                              status='published',
                              author=self.user)
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='connected')
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='blahblahblah')
        self.assertEqual(len(self.story.related_stories.all()), 2)
        self.assertEqual(len(self.story.connected_stories()), 1)
        self.assertEqual(self.story.connected_stories()[0], story)

    def test_connected_to_stories(self):
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='connected')
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='blahblahblah')
        self.assertEqual(len(story.connected_to_stories()), 1)
        self.assertEqual(story.connected_to_stories()[0], self.story)

    def test_is_connected(self):
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='connected')
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='blahblahblah')
        self.assertEqual(self.story.is_connected(), False)
        self.assertEqual(story.is_connected(), True)

    def test_get_prompt(self):
        """
        Test retrieving the prompt from the parent story in a connected
        story relationship.
        """
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        StoryRelation.objects.create(source=self.story, target=story,
                                     relation_type='connected')
        self.assertEqual(story.get_prompt(), self.story.connected_prompt)

    def test_get_prompt_no_connections(self):
        """
        Test that an empty prompt is returned when there is no
        connected story relationship.
        """
        story = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        self.assertEqual(story.get_prompt(), "")


class ViewsTest(TestCase):
    """Tests for story-related views"""

    def test_homepage_story_list(self):
        """Test homepage_story_list()"""
        import lxml.html
        from storybase_story.views import homepage_story_list

        homepage_titles = (
            "The Power of Play: Playground Locations in the Children's Corridor",
            "Birth Trends in the Children's Corridor: Focus on Foreign-born Mothers",
            "Shattered Dreams: Revitalizing Hope in Original Aurora",
            "A School Fight Rallies Hinkley High School Mothers to Organize",
            "Transportation Challenges Limit Education Choices for Denver Parents")
        for title in homepage_titles:
            create_story(title=title, on_homepage=True, status='published')
            # Force different timestamps for stories
            sleep(1)
        homepage_stories = Story.objects.on_homepage()
        html = homepage_story_list(len(homepage_titles))
        fragment = lxml.html.fromstring(html)
        # TODO: Finish implementing this
        elements = fragment.cssselect('.stories > li')
        self.assertEqual(len(elements), homepage_stories.count())
        sorted_titles = tuple(reversed(homepage_titles))
        for i in range(len(sorted_titles)):
            self.assertTrue(sorted_titles[i] in elements[i].text_content())


class StoryBuilderViewTest(TestCase):
    """Test case for view that bootstraps Backbone view for editing stories"""
    fixtures = ['section_layouts.json']
    
    def setUp(self):
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        self.story = create_story(title="Test Story", summary="Test Summary",
                                  byline="Test Byline", status='published',
                                  author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Test Section 1", story=self.story,
                                  layout=layout)
        section2 = create_section(title="Test Section 2", story=self.story,
                                  layout=layout)
        create_html_asset(type='text', title='Test Asset', 
            body='Test content')
        create_html_asset(type='text', title='Test Asset 2',
            body='Test content 2')
        create_html_asset(type='text', title='Test Asset 3',
            body='Test content 3')
        create_html_asset(type='text', title='Test Asset 4',
            body='Test content 4')
        left = Container.objects.get(name='left')
        right = Container.objects.get(name='right')
        assets = Asset.objects.all()
        SectionAsset.objects.create(section=section1, asset=assets[0], container=left)
        SectionAsset.objects.create(section=section1, asset=assets[1], container=right)
        SectionAsset.objects.create(section=section2, asset=assets[2], container=left)
        SectionAsset.objects.create(section=section2, asset=assets[3], container=right)
        self.view = StoryBuilderView()

    def test_get_sections_json(self):
        """Test getting serialized section data for a story"""
        json_data = self.view.get_sections_json(story=self.story)
        data = json.loads(json_data)
        self.assertEqual(len(data['objects']), len(self.story.sections.all()))
        section_ids = [section_data['section_id'] for section_data in data['objects']]
        for section in self.story.sections.all():
            self.assertIn(section.section_id, section_ids)

    def test_get_section_assets_json(self):
        """Test getting serialized asset data for a story"""
        json_data = self.view.get_section_assets_json(story=self.story)
        data = json.loads(json_data)
        self.assertEqual(len(data), len(self.story.sections.all()))
        for section in self.story.sections.all():
            self.assertIn(section.section_id, data)
            self.assertEqual(len(data[section.section_id]['objects']),
                             len(section.assets.all()))
            asset_ids = [sectionasset['asset']['asset_id'] for
                         sectionasset in 
                         data[section.section_id]['objects']]
            for asset in section.assets.all():
                self.assertIn(asset.asset_id, asset_ids)


class SectionModelTest(TestCase, SloppyComparisonTestMixin):
    """Test Case for Section model"""
    fixtures = ['section_layouts.json']

    def test_update_story_timestamp(self):
        """
        Test that a section's story's last edited timestamp is updated when
        the section is saved
        """
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section 1", story=story, layout=layout)
        sleep(2)
        section.save()
        self.assertNowish(story.last_edited)


class TemplateTagTest(TestCase):
    """Test case for custom template tags"""
    fixtures = ['section_layouts.json']

    def setUp(self):
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary,
            byline=byline)
        create_html_asset(type='text', title='Test Asset', 
            body='Test content')
        create_html_asset(type='text', title='Test Asset 2',
            body='Test content 2')
        create_html_asset(type='text', title='Test Asset 3',
            body='Test content 3')
        layout = SectionLayout.objects.get(
                sectionlayouttranslation__name="Side by Side")
        self.section = create_section(title="Test Section1", story=self.story,
                layout=layout)

    def test_container_no_assets(self):
        """
        Test that the container tag returns a placeholder when no 
        assets are provided in the context 
        """
        context = {}
        container_name = "left"
        html = container(context, container_name)
        self.assertIn("storybase-container-placeholder", html)
        self.assertIn(container_name, html)

    def test_container_empty_assets(self):
        """
        Test that the container tag returns a placeholder when no 
        assets are associated with a section.

        """
        context = {
            'assets': self.section.sectionasset_set.order_by('weight')
        }
        container_name = "left"
        html = container(context, container_name)
        self.assertIn("storybase-container-placeholder", html)
        self.assertIn(container_name, html)

    def test_container_no_asset_for_container(self):
        """
        Test that the container tag returns a placeholder when there
        are no assets associated with a particular section container.
        """
        assets = Asset.objects.select_subclasses()
        right = Container.objects.get(name='right')
        SectionAsset.objects.create(section=self.section, asset=assets[0],
            container=right)
        # Refresh the section object to get new relations
        self.section = Section.objects.get(pk=self.section.pk)
        context = {
            'assets': self.section.sectionasset_set.order_by('weight')
        }
        container_name = "left"
        html = container(context, container_name)
        self.assertIn("storybase-container-placeholder", html)
        self.assertIn(container_name, html)

    def test_container_with_assets(self):
        """
        Test that the container tag returns the asset's content when
        there are assets associated with a particular section container
        """
        assets = Asset.objects.select_subclasses()
        left = Container.objects.get(name='left')
        right = Container.objects.get(name='right')
        SectionAsset.objects.create(section=self.section, asset=assets[0],
            container=left)
        SectionAsset.objects.create(section=self.section, asset=assets[1],
            container=right)
        # Refresh the section object to get new relations
        self.section = Section.objects.get(pk=self.section.pk)
        context = {
            'assets': self.section.sectionasset_set.order_by('weight')
        }
        html = container(context, "left")
        self.assertEqual(html, assets[0].render_html())
        html = container(context, "right")
        self.assertEqual(html, assets[1].render_html())


class SectionRenderTest(TestCase):
    """Test Case for rendering section assets"""
    fixtures = ['section_layouts.json']

    def setUp(self):
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary,
            byline=byline)
        create_html_asset(type='text', title='Test Asset', 
            body='Test content')
        create_html_asset(type='text', title='Test Asset 2',
            body='Test content 2')
        create_html_asset(type='text', title='Test Asset 3',
            body='Test content 3')

    def test_render_html_side_by_side(self):
        """Test rendering assets with the "Side by Side" layout"""
        assets = Asset.objects.select_subclasses()
        layout = SectionLayout.objects.get(
                sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section1", story=self.story,
                layout=layout)
        left = Container.objects.get(name='left')
        right = Container.objects.get(name='right')
        SectionAsset.objects.create(section=section, asset=assets[0], container=left)
        SectionAsset.objects.create(section=section, asset=assets[1], container=right)
        html = section.render_html()
        self.assertIn('class="left"', html)
        self.assertIn('class="right"', html)
        self.assertIn(assets[0].title, html)
        self.assertIn(assets[1].title, html)

    def test_render_html_no_layout(self):
        """
        Test rendering a section when no section layout is specified and when
        there are no containers associated with section assets.
        
        This is the case for stories created with the Django backend in early
        versions of the software, when there wasn't the concept of 
        layouts/containers, just weights.
        """
        assets = Asset.objects.select_subclasses()
        # Create a section without specifying layout 
        section = create_section(title="Test Section1", story=self.story)
        # Associate assets with the section without specifying a container
        SectionAsset.objects.create(section=section, asset=assets[0])
        SectionAsset.objects.create(section=section, asset=assets[1])
        html = section.render_html()
        self.assertIn(assets[0].title, html)
        self.assertIn(assets[1].title, html)
                

class SectionLayoutModelTest(TestCase):
    fixtures = ['section_layouts.json']

    def test_get_template_contents(self):
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        template_contents = layout.get_template_contents()
        self.assertIn("class=\"section-layout", template_contents)


class SectionRelationModelTest(TestCase):
    fixtures = ['section_layouts.json']

    def test_force_unicode(self):
        """
        Test that the unicode representation of SectionRelation model instances
        can be passed to ``force_unicode``

        Test to reproduce issue #135

        """
        from django.utils.encoding import force_unicode
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        unicode_section_title = u"What’s in this guide?"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title=unicode_section_title, story=story, layout=layout)
        section2 = create_section(title="Understanding the School Performance Framework: A Guide for Parents", story=story, layout=layout)
        relation = SectionRelation.objects.create(parent=section2, child=section1)
        self.assertEqual(force_unicode(relation), u"What’s in this guide? is child of Understanding the School Performance Framework: A Guide for Parents")


class SectionApiTest(TestCase):
    """Test case for public Section creation API"""
    fixtures = ['section_layouts.json']

    def test_create_section(self):
        """Test that create_section() function creates a new Section"""
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        section_title = "Test Section 1"
        with self.assertRaises(Section.DoesNotExist):
            Section.objects.get(sectiontranslation__title=section_title)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title=section_title, story=story, layout=layout)
        self.assertEqual(section.title, section_title)
        self.assertEqual(section.story, story)
        self.assertEqual(section.layout, layout)
        retrieved_section = Section.objects.get(pk=section.pk)
        self.assertEqual(retrieved_section.title, section_title)
        self.assertEqual(retrieved_section.story, story)
        self.assertEqual(retrieved_section.layout, layout)

class SectionAssetModelTest(TestCase):
    """Test Case for Asset to Section relation through model"""
    fixtures = ['section_layouts.json']

    def test_auto_add_assets_to_story(self):
        """
        Test that when an asset is added to a section it is also added
        to the Story
        """
        # Create a story
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        # Confirm that the story has no assets
        self.assertEqual(story.assets.count(), 0)
        # create a Section
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section 1", story=story, layout=layout)
        # create a HtmlAsset
        asset = HtmlAsset()
        asset.save()
        translation = HtmlAssetTranslation(title='Test Asset', asset=asset)
        translation.save()
        # Assign the asset to the section
        container = Container.objects.get(name='left')
        section_asset = SectionAsset(section=section, asset=asset, container=container)
        section_asset.save()
        # Confirm the asset is in the section's list
        self.assertTrue(asset in section.assets.select_subclasses())
        # Confirm that the asset is in the story's list
        self.assertTrue(asset in story.assets.select_subclasses())

    def test_already_added_asset(self):
        """
        Test that when an asset that is related to a story is also
        related to a section, nothing breaks
        """
        # Create a story
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        # create a HtmlAsset
        asset = HtmlAsset()
        asset.save()
        translation = HtmlAssetTranslation(title='Test Asset', asset=asset)
        translation.save()
        # assign the asset to the story
        story.assets.add(asset)
        story.save()
        # confirm the asset is added to the story
        self.assertTrue(asset in story.assets.select_subclasses())
        # create a Section
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section 1", story=story, layout=layout)
        # Assign the asset to the section
        container = Container.objects.get(name='left')
        section_asset = SectionAsset(section=section, asset=asset, container=container)
        section_asset.save()
        # Confirm the asset is in the section's list
        self.assertTrue(asset in section.assets.select_subclasses())
        # Confirm that the asset is in the story's list
        self.assertTrue(asset in story.assets.select_subclasses())

    def test_remove_asset(self):
        """
        Test that when an asset is removed from a section, it is not 
        removed from the story
        """
        # Create a story
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        story = create_story(title=title, summary=summary, byline=byline)
        # Confirm that the story has no assets
        self.assertEqual(story.assets.count(), 0)
        # create a Section
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section 1", story=story, layout=layout)
        # create a HtmlAsset
        asset = HtmlAsset()
        asset.save()
        translation = HtmlAssetTranslation(title='Test Asset', asset=asset)
        translation.save()
        # Assign the asset to the section
        container = Container.objects.get(name='left')
        section_asset = SectionAsset(section=section, asset=asset, container=container)
        section_asset.save()
        # Confirm the asset is in the section's list
        self.assertTrue(asset in section.assets.select_subclasses())
        # Confirm that the asset is in the story's list
        self.assertTrue(asset in story.assets.select_subclasses())
        # Delete the asset from the section.
        section_asset.delete()
        # Confirm that the asset is NOT in the section's list
        self.assertFalse(asset in section.assets.select_subclasses())
        # Confirm that the asset is in the story's list
        self.assertTrue(asset in story.assets.select_subclasses())


class StructureTest(TestCase):
    """Test rendering of different story structures"""
    fixtures = ['section_layouts.json']

    def test_linear_toc_simple(self):
        """
        Test that a table of contents can be rendered for a
        simple story structure
        """
        import lxml.html

        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        section_data = [
            {'title': 'Children and Affordable Housing', 'weight': 0},
            {'title': 'School Quality', 'weight': 1},
            {'title': 'Early Childhood Education', 'weight': 2},
            {'title': 'Low-Income Families and FRL', 'weight': 3},
            {'title': 'Transportation Spending', 'weight': 4},
            {'title': 'The Choice System', 'weight': 5}
        ]
        story = create_story(title=title, structure='linear',
                             summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        for section_dict in section_data:
            create_section(title=section_dict['title'],
                           story=story,
                           layout=layout,
                           weight=section_dict['weight'],
                           root=True)
        rendered_toc = story.structure.render_toc(format='html')
        fragment = lxml.html.fromstring(rendered_toc)
        elements = fragment.cssselect('li')
        self.assertEqual(len(elements), len(section_data) + 1)
	self.assertEqual(elements[0].text_content().strip(), "Summary")
        for i in range(1, len(section_data)):
            self.assertEqual(section_data[i-1]['title'],
                             elements[i].text_content().strip())
        
    def test_sections_flat_linear_nested(self):
        """
        Test sections_flat() when sections are arranged in a linear
        fashion with one root and each subsequent section nested below
        the previous
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story,
                                  layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2)
        SectionRelation.objects.create(parent=section2, child=section3)
        SectionRelation.objects.create(parent=section3, child=section4)
        self.assertEqual(story.structure.sections_flat, [section1, section2, 
                                                section3, section4])

    def test_sections_flat_spider(self):
        """
        Test sections_flat() when sections are arranged as children of a
        single root section.
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section1, child=section3,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section4,
                                       weight=2)
        self.assertEqual(story.structure.sections_flat, [section1, section2,
                                                 section3, section4])

    def test_sections_flat_tree(self):
        """
        Test sections_flat() when sections are arranged in a tree-like
        structure
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        section5 = create_section(title="Last section", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section3,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section4,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section5,
                                       weight=1)
        self.assertEqual(story.structure.sections_flat, [section1, section2,
                                                 section3, section4,
                                                 section5])

    def test_sections_flat_no_sections(self):
        """
        Test sections_flat() when there are no child sections
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        self.assertEqual(story.structure.sections_flat, [])

    def test_sections_flat_one_section(self):
        """
        Test sections_flat() when there is only a single root section
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        self.assertEqual(story.structure.sections_flat, [section1])

    def test_sections_flat_no_root_section(self):
        """
        Test sections_flat() when there is only a single root section
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story, layout=layout,
                                  root=False)
        self.assertEqual(story.structure.sections_flat, [])

    def test_get_next_section_linear_nested(self):
        """
        Test get_next_section() when sections are arranged in a linear
        fashion with one root and each subsequent section nested below
        the previous
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story, layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2)
        SectionRelation.objects.create(parent=section2, child=section3)
        SectionRelation.objects.create(parent=section3, child=section4)
        self.assertEqual(story.structure.get_next_section(section1),   
                         section2)
        self.assertEqual(story.structure.get_next_section(section2),
                         section3)
        self.assertEqual(story.structure.get_next_section(section3),
                         section4)
        self.assertEqual(story.structure.get_next_section(section4),
                         None)

    def test_get_previous_section_linear_nested(self):
        """
        Test get_previous_section() when sections are arranged in a linear
        fashion with one root and each subsequent section nested below
        the previous
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story, layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story,
                                  layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2)
        SectionRelation.objects.create(parent=section2, child=section3)
        SectionRelation.objects.create(parent=section3, child=section4)
        self.assertEqual(story.structure.get_previous_section(section1),   
                         None)
        self.assertEqual(story.structure.get_previous_section(section2),
                         section1)
        self.assertEqual(story.structure.get_previous_section(section3),
                         section2)
        self.assertEqual(story.structure.get_previous_section(section4),
                         section3)

    def test_get_next_section_spider(self):
        """
        Test test_get_next_section() when sections are arranged as children
        of a single root section.
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story, layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", 
                                  story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps",
                                  story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section1, child=section3,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section4,
                                       weight=2)
        self.assertEqual(story.structure.get_next_section(section1),   
                         section2)
        self.assertEqual(story.structure.get_next_section(section2),
                         section3)
        self.assertEqual(story.structure.get_next_section(section3),
                         section4)
        self.assertEqual(story.structure.get_next_section(section4),
                         None)

    def test_get_previous_section_spider(self):
        """
        Test test_get_previous_section() when sections are arranged as 
        children of a single root section.
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section1, child=section3,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section4,
                                       weight=2)
        self.assertEqual(story.structure.get_previous_section(section1),   
                         None)
        self.assertEqual(story.structure.get_previous_section(section2),
                         section1)
        self.assertEqual(story.structure.get_previous_section(section3),
                         section2)
        self.assertEqual(story.structure.get_previous_section(section4),
                         section3)

    def test_get_next_section_tree(self):
        """
        Test get_next_section() when sections are arranged in a tree-like
        structure
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        section5 = create_section(title="Last section", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section3,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section4,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section5,
                                       weight=1)
        self.assertEqual(story.structure.get_next_section(section1),   
                         section2)
        self.assertEqual(story.structure.get_next_section(section2),   
                         section3)
        self.assertEqual(story.structure.get_next_section(section3),   
                         section4)
        self.assertEqual(story.structure.get_next_section(section4),   
                         section5)
        self.assertEqual(story.structure.get_next_section(section5),   
                         None)

    def test_get_previous_section_tree(self):
        """
        Test get_previous_section() when sections are arranged in a tree-like
        structure
        """
        title = ("Neighborhood Outreach for I-70 Alignment Impacting "
                 "Elyria, Globeville and Swansea")
        summary = """
            The City of Denver and Colorado Department of Transportation 
            (CDOT) are working together to do neighborhood outreach
            regarding the I-70 alignment between Brighton Boulevard and
            Colorado. For detailed information on the neighborhood outreach
            efforts please visit www.DenverGov.org/ccdI70.
            """
        byline = "Denver Public Works and CDOT"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Background and context",
                                  story=story,
                                  layout=layout,
                                  root=True)
        section2 = create_section(title="Decisions to be made", story=story, layout=layout)
        section3 = create_section(title="Who has been involved", 
                                  story=story, layout=layout)
        section4 = create_section(title="Next steps", story=story, layout=layout)
        section5 = create_section(title="Last section", story=story, layout=layout)
        SectionRelation.objects.create(parent=section1, child=section2,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section3,
                                       weight=0)
        SectionRelation.objects.create(parent=section2, child=section4,
                                       weight=1)
        SectionRelation.objects.create(parent=section1, child=section5,
                                       weight=1)
        self.assertEqual(story.structure.get_previous_section(section1),   
                         None)
        self.assertEqual(story.structure.get_previous_section(section2),   
                         section1)
        self.assertEqual(story.structure.get_previous_section(section3),   
                         section2)
        self.assertEqual(story.structure.get_previous_section(section4),   
                         section3)
        self.assertEqual(story.structure.get_previous_section(section5),   
                         section4)

    def _get_section(self, sections, section_id):
	"""
	Utility to get a section with a given ID from a list of simplified
	section dictionaries
	"""
        for section in sections:
	    if section['section_id'] == section_id:
	        return section

    def test_sections_json_spider_three_levels(self):
        """
        Test that sections_json() returns the sections in the correct 
        order and with the correct relationships
        """

        title = ("Taking Action for the Social and Emotional Health of "
	             "Young Children: A Report to the Community from the "  
                 "Denver Early Childhood Council")
        summary = ("Now, Denver has a plan of action to make it easier "
                   "for families to access early childhood mental health "
                   "information, intervention and services.")
        byline = "Denver Early Childhood Council"
        story = create_story(title=title, summary=summary, byline=byline)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section("We're ready to take action. Are you?",
                                   story=story, layout=layout, weight=7)
        section2 = create_section("Ricardo's Story",
			                      story=story, layout=layout, weight=2)
        section3 = create_section("Meeting the need for better child mental health services",
			                      story=story, layout=layout, root=True,
                                  weight=1)
        section4 = create_section("Healthy Minds Support Strong Futures",
                                  story=story, layout=layout, weight=5) 
        section5 = create_section("Community Voices",
			                      story=story, layout=layout, weight=3)
        section6 = create_section("Our Vision: That All Children in Denver are Valued, Healthy and Thriving",
			                      story=story, layout=layout, weight=4)
        section7 = create_section("Defining a \"Framework for Change\" with Actionable Goals and Strategies",
			                      story=story, layout=layout, weight=5) 
        section8 = create_section("How Can the Plan Make a Difference?",
			                      story=story, layout=layout, weight=5)
        section9 = create_section("Impact", story=story, layout=layout,
                                  weight=6)
        SectionRelation.objects.create(parent=section6, child=section8,
                                       weight=0)
        SectionRelation.objects.create(parent=section7, child=section9,
                                       weight=0)
        SectionRelation.objects.create(parent=section6, child=section7,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section1,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section6,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section4,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section5,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section2,
                                       weight=0)
        json_sections = simplejson.loads(story.structure.sections_json(
            include_summary=False, include_call_to_action=False))
        self.assertIn(section8.section_id,
            self._get_section(
                json_sections, section6.section_id)['children'])
        self.assertIn(section9.section_id,
          self._get_section(json_sections, section7.section_id)['children'])
        self.assertIn(section7.section_id,
            self._get_section(json_sections, section6.section_id)['children'])
        self.assertIn(section1.section_id,
            self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(section6.section_id,
            self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(section4.section_id,
            self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(section5.section_id,
            self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(section2.section_id,
            self._get_section(json_sections, section3.section_id)['children'])

    def test_sections_json_spider_three_levels_with_summary_and_call(self):
        """
        Test that sections_json() returns the sections in the correct 
        order and with the correct relationships and also includes
        the summary and call to action
        """
        title = ("Taking Action for the Social and Emotional Health of "
                 "Young Children: A Report to the Community from the " 
		         "Denver Early Childhood Council")
        summary = ("Now, Denver has a plan of action to make it easier "
                   "for families to access early childhood mental health "
                   "information, intervention and services.")
        call_to_action = ("Test call to action.")
        byline = "Denver Early Childhood Council"
        story = create_story(title=title, summary=summary, byline=byline,
			     call_to_action=call_to_action)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section("We're ready to take action. Are you?",
			          story=story, layout=layout, weight=7)
        section2 = create_section("Ricardo's Story",
			          story=story, layout=layout, weight=2)
        section3 = create_section("Meeting the need for better child mental health services",
			           story=story, layout=layout, root=True, weight=1)
        section4 = create_section("Healthy Minds Support Strong Futures",
			          story=story, layout=layout, weight=5) 
        section5 = create_section("Community Voices",
			          story=story, layout=layout, weight=3)
        section6 = create_section("Our Vision: That All Children in Denver are Valued, Healthy and Thriving",
			          story=story, layout=layout, weight=4)
        section7 = create_section("Defining a \"Framework for Change\" with Actionable Goals and Strategies",
			          story=story, layout=layout, weight=5) 
        section8 = create_section("How Can the Plan Make a Difference?",
			          story=story, layout=layout, weight=5)
        section9 = create_section("Impact", 
                                  story=story, layout=layout,  weight=6)
        SectionRelation.objects.create(parent=section6, child=section8,
                                       weight=0)
        SectionRelation.objects.create(parent=section7, child=section9,
                                       weight=0)
        SectionRelation.objects.create(parent=section6, child=section7,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section1,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section6,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section4,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section5,
                                       weight=0)
        SectionRelation.objects.create(parent=section3, child=section2,
                                       weight=0)
        json_sections = simplejson.loads(story.structure.sections_json(
            include_summary=True, include_call_to_action=True))
        self.assertIn(
            section8.section_id,
            self._get_section(json_sections, section6.section_id)['children'])
        self.assertIn(
          section9.section_id,
          self._get_section(json_sections, section7.section_id)['children'])
        self.assertIn(
          section7.section_id,
          self._get_section(json_sections, section6.section_id)['children'])
        self.assertIn(
          section1.section_id,
          self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(
          section6.section_id,
          self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(
          section4.section_id,
          self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(
          section5.section_id,
          self._get_section(json_sections, section3.section_id)['children'])
        self.assertIn(
          section2.section_id,
          self._get_section(json_sections, section3.section_id)['children'])
        self.assertEqual(json_sections[0]['section_id'], 'summary')
        self.assertEqual(json_sections[0]['next_section_id'], 
                 json_sections[1]['section_id'])
        self.assertEqual(json_sections[1]['previous_section_id'], 'summary')
        self.assertEqual(json_sections[-1]['section_id'], 'call-to-action')
        self.assertEqual(json_sections[-1]['previous_section_id'], 
                 json_sections[-2]['section_id'])
        self.assertEqual(json_sections[-2]['next_section_id'], 'call-to-action')


class StoryResourceTest(ResourceTestCase):
    """Tests for backend to Tastypie-driven REST endpoint"""
    fixtures = ['section_layouts.json']

    def setUp(self):
        super(StoryResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = StoryResource()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)

    def assertPointInList(self, point, l):
        for p in l:
            if p == point:
                return True
        else:
            self.fail("Point (%f, %f) not found in %s" % (point[0], point[1], str(l)))

    def test_locations_in_points(self):
        """
        Test that related Location coordinates are included in the ``points``
        field of a story's serialized data
        """
        locations = [
            Location.objects.create(name="The Piton Foundation", lat=39.7438167, lng=-104.9884953),
            Location.objects.create(name="Hull House", lat=41.8716782, lng=-87.6474517)
        ]
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        story.locations.add(locations[0])
        story.locations.add(locations[1])
        story.save()
        req = HttpRequest()
        req.GET['story_id'] = story.story_id
        resp = self.resource.get_detail(req)
        dehydrated = simplejson.loads(resp.content)
        self.assertEqual(len(dehydrated['points']), 2)
        for location in locations:
            self.assertPointInList([location.lat, location.lng],
                                   dehydrated['points'])

    def test_get_detail(self):
        story_attribute_keys = ['allow_connected',
                                'byline',
                                'call_to_action',
                                'connected_prompt',
                                'contact_info',
                                'created',
                                'featured_asset_url',
                                'language',
                                'languages', 
                                'last_edited',
                                'license',
                                'is_template',
                                'on_homepage',
                                'organizations',
                                'places',
                                'points',
                                'projects',
                                'published',
                                'resource_uri',
                                'slug',
                                'status',
                                'story_id',
                                'structure_type',
                                'summary',
                                'template_story',
                                'title',
                                'topics',
                                'url']
                                
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en")
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        section2 = create_section(title="Test Section 2", story=story,
                                  layout=layout)
        resp = self.api_client.get('/api/0.1/stories/%s/' % story.story_id)
        self.assertValidJSONResponse(resp)
        self.assertKeys(self.deserialize(resp), story_attribute_keys)
        self.assertEqual(self.deserialize(resp)['byline'], "Test Byline")
        self.assertEqual(self.deserialize(resp)['title'], "Test Story")
        self.assertEqual(self.deserialize(resp)['summary'], "Test Summary")
        self.assertEqual(self.deserialize(resp)['status'], "published")
        self.assertEqual(len(self.deserialize(resp)['languages']), 1)
        self.assertEqual(self.deserialize(resp)['languages'][0]['id'], "en")

    def test_post_list_unauthorized(self):
        """Test that a user cannot create a story if they aren't logged in"""
        self.assertHttpUnauthorized(self.api_client.post('/api/0.1/stories/', format='json'))

    def test_post_list(self):
        """Test that a user can create a story"""
        post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        self.assertEqual(Story.objects.count(), 0)
        self.api_client.client.login(username=self.username, password=self.password)
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=post_data)
        self.assertHttpCreated(response)
        self.assertEqual(Story.objects.count(), 1)
        created_story = Story.objects.get()
        self.assertEqual(created_story.title, post_data['title'])
        self.assertEqual(created_story.summary, post_data['summary'])
        self.assertEqual(created_story.byline, post_data['byline'])
        self.assertEqual(created_story.status, post_data['status'])
        self.assertEqual(created_story.get_languages(), [post_data['language']])
        self.assertEqual(created_story.author, self.user)
        # Check that the story id is returned by the endpoint
        returned_story_id = response['location'].split('/')[-2]
        self.assertEqual(created_story.story_id, returned_story_id)

    def test_post_list_es(self):
        """Test that a user can create a story in Spanish"""
        post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "es",
        }
        self.assertEqual(Story.objects.count(), 0)
        self.api_client.client.login(username=self.username, password=self.password)
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=post_data)
        self.assertHttpCreated(response)
        self.assertEqual(Story.objects.count(), 1)
        created_story = Story.objects.get()
        self.assertEqual(created_story.title, post_data['title'])
        self.assertEqual(created_story.summary, post_data['summary'])
        self.assertEqual(created_story.byline, post_data['byline'])
        self.assertEqual(created_story.status, post_data['status'])
        self.assertEqual(created_story.get_languages(), [post_data['language']])
        self.assertEqual(created_story.author, self.user)
        # Check that the language returned in the response is the 
        # same as the post
        self.assertEqual(self.deserialize(response)['language'],
                         post_data['language'])
        # Check that the story id is returned by the endpoint
        returned_story_id = response['location'].split('/')[-2]
        self.assertEqual(created_story.story_id, returned_story_id)

    def test_post_list_with_template(self):
        """
        Test that a user can create a story specifying the story that
        provides the structure for this story.
        """
        template_story = create_story(title="Test Template Story",
            summary="Test Template Story Summary", 
            byline="Test Template Story Byline",  status="published",
            language="en")
        post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
            'template_story': template_story.story_id
        }
        self.assertEqual(Story.objects.count(), 1)
        self.api_client.client.login(username=self.username, password=self.password)
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=post_data)
        self.assertHttpCreated(response)
        self.assertEqual(Story.objects.count(), 2)
        returned_story_id = response['location'].split('/')[-2]
        created_story = Story.objects.get(story_id=returned_story_id)
        self.assertEqual(created_story.title, post_data['title'])
        self.assertEqual(created_story.summary, post_data['summary'])
        self.assertEqual(created_story.byline, post_data['byline'])
        self.assertEqual(created_story.status, post_data['status'])
        self.assertEqual(created_story.get_languages(), [post_data['language']])
        self.assertEqual(created_story.author, self.user)
        self.assertEqual(created_story.template_story, template_story)

    def test_patch_detail_unauthorized_unauthenticated(self):
        """Test that anonymouse users cannot update a story"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=self.user)
        post_data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.patch('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=post_data)
        self.assertHttpUnauthorized(response)

    def test_patch_detail_unauthorized(self):
        """Test that user who is not author cannot update a story"""
        author = User.objects.create_user("test2", "test2@example.com", "test2")
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=author)
        self.api_client.client.login(username=self.username, password=self.password)
        post_data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.patch('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=post_data)
        self.assertHttpUnauthorized(response)

    def test_patch_detail(self):
        """Test that an author can update her own story"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=self.user)
        self.api_client.client.login(username=self.username, password=self.password)
        data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.patch('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=data)
        self.assertHttpAccepted(response)
        story = Story.objects.get(story_id=story.story_id)
        self.assertEqual(story.title, data['title'])
        self.assertEqual(story.summary, data['summary'])
        self.assertEqual(story.byline, data['byline'])
        self.assertEqual(story.status, data['status'])

    def test_patch_detail_no_translation_in_lang(self):
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             language="en",
                             author=self.user)
        self.api_client.client.login(username=self.username, password=self.password)
        data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
            'language': "es",
        }
        response = self.api_client.patch('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=data)
        self.assertHttpNotFound(response)

    def test_put_detail_unauthorized_unauthenticated(self):
        """Test that anonymouse users cannot update a story"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=self.user)
        post_data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.put('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=post_data)
        self.assertHttpUnauthorized(response)

    def test_put_detail_unauthorized(self):
        """Test that user who is not author cannot update a story"""
        author = User.objects.create_user("test2", "test2@example.com", "test2")
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=author)
        self.api_client.client.login(username=self.username, password=self.password)
        post_data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.put('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=post_data)
        self.assertHttpUnauthorized(response)

    def test_put_detail(self):
        """Test that an author can update her own story"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=self.user)
        self.api_client.client.login(username=self.username, password=self.password)
        data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
        }
        response = self.api_client.put('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=data)
        self.assertHttpAccepted(response)
        story = Story.objects.get(story_id=story.story_id)
        self.assertEqual(story.title, data['title'])
        self.assertEqual(story.summary, data['summary'])
        self.assertEqual(story.byline, data['byline'])
        self.assertEqual(story.status, data['status'])

    def test_put_detail_no_translation_in_lang(self):
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             language="en",
                             author=self.user)
        self.api_client.client.login(username=self.username, password=self.password)
        data = {
            'title': "New Title",
            'summary': "New Summary",
            'byline': "New Byline",
            'status': "published",
            'language': "es",
        }
        response = self.api_client.put('/api/0.1/stories/%s/' % (story.story_id),
                               format='json', data=data)
        self.assertHttpNotFound(response)

    def test_get_list_published_only(self):
        """Test that unauthenticated users see only published stories"""
        story1 = create_story(title="Test Story", summary="Test Summary",
                              byline="Test Byline", status='published',
                              language="en", author=self.user)
        story2 = create_story(title="Test Story 2", summary="Test Summary 2",
                              byline="Test Byline 2", status='draft',
                              language="en", author=self.user)
        uri = '/api/0.1/stories/'
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        story_ids = [story['story_id'] for story in self.deserialize(resp)['objects']]
        self.assertNotIn(story2.story_id, story_ids)

    def test_get_list_published_user_drafts(self):
        """
        Test that authenticated users see their own stories regardless of
        publication status
        
        """
        story1 = create_story(title="Test Story", summary="Test Summary",
                              byline="Test Byline", status='published',
                              language="en", author=self.user)
        story2 = create_story(title="Test Story 2", summary="Test Summary 2",
                              byline="Test Byline 2", status='draft',
                              language="en", author=self.user)
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/'
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        story_ids = [story['story_id'] for story in self.deserialize(resp)['objects']]
        self.assertIn(story1.story_id, story_ids)
        self.assertIn(story2.story_id, story_ids)

    def test_dehydrate_last_edited_return_tz_aware(self):
        """
        Test that the dehydrate_last_edited method returns a
        timezone-aware value.
        """
        bundle = Bundle(data={
            'last_edited': datetime.datetime(2012, 7, 24, 19, 0, 0, 0)
        })
        resource = StoryResource()
        self.assertEqual('-0500', resource.dehydrate_last_edited(bundle).strftime('%z'))


class SectionResourceTest(ResourceTestCase):
    fixtures = ['section_layouts.json']

    def setUp(self):
        super(SectionResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = SectionResource(api_name='0.1')
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        self.user2 = User.objects.create_user("test2", "test2@example.com",
                                              "test2")

    def test_get_resource_uri_detail(self):
        """Tests retrieving a URI for a specific section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en")
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section = create_section(title="Test Section 1", story=story,
                                 layout=layout)
        uri = self.resource.get_resource_uri(bundle_or_obj=section)
        self.assertEqual(uri, "/api/0.1/stories/%s/sections/%s/" %
                        (story.story_id, section.section_id))

    def test_get_list(self):
        """Test that a user can get a list of story sections"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section1 = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        section2 = create_section(title="Test Section 2", story=story,
                                  layout=layout)
        uri = '/api/0.1/stories/%s/sections/' % story.story_id
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        section_titles = [section['title'] for section in self.deserialize(resp)['objects']]
        self.assertIn(section1.title, section_titles)
        self.assertIn(section2.title, section_titles)
        self.assertEqual(section1.layout.get_template_contents(),
                         self.deserialize(resp)['objects'][0]['layout_template'])

    def test_get_list_with_help(self):
        """Test that a section's help is included in the list response"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        section_help = create_help(title="Test section help item",
                                   body="Test section help item body")
        section1 = create_section(title="Test Section 1", story=story,
                                  layout=layout, help=section_help)
        section2 = create_section(title="Test Section 2", story=story,
                                  layout=layout)
        uri = '/api/0.1/stories/%s/sections/' % story.story_id
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        self.assertEqual(self.deserialize(resp)['objects'][0]['help']['help_id'],
                         section_help.help_id)
        self.assertEqual(self.deserialize(resp)['objects'][0]['help']['title'],
                         section_help.title)
        self.assertEqual(self.deserialize(resp)['objects'][0]['help']['body'],
                         section_help.body)

    def test_post_list(self):
        """Test that a user can add a new section to a story"""
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        self.assertEqual(Story.objects.count(), 0)
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        # Retrieve a model instance for the created story
        story_id = story_resource_uri.split('/')[-2]
        story = Story.objects.get(story_id=story_id)
        # Confirm there are no sections
        self.assertEqual(len(story.sections.all()), 0)
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_resource_uri = response['location']
        # Retrieve a model instance for the newly created section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.all()[0]
        self.assertEqual("%s%s/" % (sections_uri, section.section_id), 
                         section_resource_uri)
        self.assertEqual(section.title, section_post_data['title'])
        self.assertEqual(section.layout.layout_id, section_post_data['layout'])

    def test_post_list_other_user(self):
        """Test that a user can't add a new section to another user's story"""
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published',
                             author=self.user2)
        self.api_client.client.login(username=self.username, password=self.password)
        story_resource_uri = '/api/0.1/stories/%s/' % story.story_id 
        # Confirm there are no sections
        self.assertEqual(len(story.sections.all()), 0)
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpUnauthorized(response)
        self.assertEqual(len(story.sections.all()), 0)

    def test_post_list_with_help(self):
        """
        Test that a user can add a new section to a story including
        help.
        """
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_help = create_help(title="Test section help item",
                                   body="Test section help item body")
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb",
            'help': {
                'help_id': section_help.help_id,
            }
        }
        self.assertEqual(Story.objects.count(), 0)
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        # Retrieve a model instance for the created story
        story_id = story_resource_uri.split('/')[-2]
        story = Story.objects.get(story_id=story_id)
        # Confirm there are no sections
        self.assertEqual(len(story.sections.all()), 0)
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_resource_uri = response['location']
        # Retrieve a model instance for the newly created section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.all()[0]
        self.assertEqual("%s%s/" % (sections_uri, section.section_id), 
                         section_resource_uri)
        self.assertEqual(section.title, section_post_data['title'])
        self.assertEqual(section.layout.layout_id, section_post_data['layout'])
        self.assertEqual(section.help, section_help)

    def test_post_list_with_template_section(self):
        """
        Test that a user can add a new section to a story including
        a reference to the section that was used to provide defaults
        for the new section.
        """
        template_story = create_story(title="Test Template Story",
            summary="Test Template Story Summary", byline="",
            status="published", language="en")
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        template_section = create_section(title="Test Template Section",
            story=template_story, layout=layout)
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb",
            'template_section': template_section.section_id
        }
        self.assertEqual(Story.objects.count(), 1)
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        # Retrieve a model instance for the created story
        story_id = story_resource_uri.split('/')[-2]
        story = Story.objects.get(story_id=story_id)
        # Confirm there are no sections
        self.assertEqual(len(story.sections.all()), 0)
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_resource_uri = response['location']
        # Retrieve a model instance for the newly created section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.all()[0]
        self.assertEqual("%s%s/" % (sections_uri, section.section_id), 
                         section_resource_uri)
        self.assertEqual(section.title, section_post_data['title'])
        self.assertEqual(section.layout.layout_id, section_post_data['layout'])
        self.assertEqual(section.template_section, template_section)

    def test_patch_detail(self):
        """Test that a user can update the metadata of a section"""
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        section_patch_data = {
            'title': "New Test Section Title",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        story_id = story_resource_uri.split('/')[-2]
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_uri = response['location']
        section_id = section_uri.split('/')[-2]
        # Update the section title
        response = self.api_client.patch(section_uri, format='json',
                                         data=section_patch_data)
        self.assertHttpAccepted(response)
        # Retrieve a model instance for the newly modified section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.get(section_id=section_id)
        self.assertEqual(section.title, section_patch_data['title'])

    def test_put_detail(self):
        """Test that a user can update the metadata of a section"""
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        section_put_data = {
            'title': "New Test Section Title",
            'language': "en",
            'layout': "ccaea5bac5c7467eb014baf6f7476ccb"
        }
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        story_id = story_resource_uri.split('/')[-2]
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
                                        format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_uri = response['location']
        section_id = section_uri.split('/')[-2]
        # Update the section title
        response = self.api_client.put(section_uri, format='json',
                                         data=section_put_data)
        self.assertHttpAccepted(response)
        # Retrieve a model instance for the newly modified section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.get(section_id=section_id)
        self.assertEqual(section.title, section_put_data['title'])
        self.assertEqual(section.layout.layout_id, section_put_data['layout'])

    def test_put_detail_with_help(self):
        """Test that a user can update the help of a section"""
        section_help = create_help(title="Test section help item",
                                   body="Test section help item body")
        story_post_data = {
            'title': "Test Story",
            'summary': "Test Summary",
            'byline': "Test Byline",
            'status': "draft",
            'language': "en",
        }
        section_post_data = {
            'title': "Test Section",
            'language': "en",
            'layout': "26c81c9dd24c4aecab7ab4eb1cc9e2fb"
        }
        section_put_data = {
            'help': {
                'help_id': section_help.help_id,
            }
        }
        self.api_client.client.login(username=self.username, password=self.password)
        # Create a new story through the API
        response = self.api_client.post('/api/0.1/stories/',
                               format='json', data=story_post_data)
        story_resource_uri = response['location']
        story_id = story_resource_uri.split('/')[-2]
        # Create a new section
        sections_uri = "%ssections/" % (story_resource_uri)
        response = self.api_client.post(sections_uri,
            format='json', data=section_post_data)
        self.assertHttpCreated(response)
        section_uri = response['location']
        section_id = section_uri.split('/')[-2]
        # Update the section help 
        response = self.api_client.put(section_uri, format='json',
                                         data=section_put_data)
        self.assertHttpAccepted(response)
        # Retrieve a model instance for the newly modified section
        story = Story.objects.get(story_id=story_id)
        self.assertEqual(len(story.sections.all()), 1)
        section = story.sections.get(section_id=section_id)
        self.assertEqual(section.help, section_help) 

    def test_delete_detail(self):
        """Test that a user can delete a section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                 layout=layout)
        self.assertEqual(Section.objects.filter(story=story).count(), 1)
        self.api_client.client.login(username=self.username,
                                     password=self.password)
        uri = '/api/0.1/stories/%s/sections/%s/' % (story.story_id,
            section.section_id)
        resp = self.api_client.delete(uri)
        self.assertHttpAccepted(resp)
        self.assertEqual(Section.objects.filter(story=story).count(), 0)
        self.assertEqual(
            Section.objects.filter(section_id=section.section_id).count(),
            0)

    def test_delete_detail_unauthenticated(self):
        """Test that an unauthenticated user cannot delete a section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                 layout=layout)
        self.assertEqual(Section.objects.filter(story=story).count(), 1)
        uri = '/api/0.1/stories/%s/sections/%s/' % (story.story_id,
            section.section_id)
        resp = self.api_client.delete(uri)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(Section.objects.filter(story=story).count(), 1)
        self.assertEqual(
            Section.objects.filter(section_id=section.section_id).count(),
            1)

    def test_delete_detail_unauthorized(self):
        """Test that a user cannot delete another user's section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user2)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                 layout=layout)
        self.assertEqual(Section.objects.filter(story=story).count(), 1)
        self.api_client.client.login(username=self.username,
                                     password=self.password)
        uri = '/api/0.1/stories/%s/sections/%s/' % (story.story_id,
            section.section_id)
        resp = self.api_client.delete(uri)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(Section.objects.filter(story=story).count(), 1)
        self.assertEqual(
            Section.objects.filter(section_id=section.section_id).count(),
            1)


class SectionAssetResourceTest(ResourceTestCase):
    fixtures = ['section_layouts.json']

    def setUp(self):
        super(SectionAssetResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = SectionAssetResource(api_name='0.1')
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        self.user2 = User.objects.create_user("test2", "test2@example.com",
                                              "test2")

    def get_asset_uri(self, asset):
        return "/api/0.1/assets/%s/" % (asset.asset_id)

    def test_get_list(self):
        """Test that a user can get a list of section assets"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset1 = create_html_asset(type='text', title='Test Asset',
                                   body='Test content')
        asset2 = create_html_asset(type='text', title='Test Asset 2',
                                   body='Test content 2')
        asset3 = create_html_asset(type='text', title='Test Asset 3',
                                   body='Test content 3')
        story2 = create_story(title="Test Story 2", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        section2 = create_section(title="Test Section 2", story=story2,
                                  layout=layout)
        SectionAsset.objects.create(section=section, asset=asset1, container=container1)
        SectionAsset.objects.create(section=section, asset=asset2, container=container2)
        SectionAsset.objects.create(section=section2, asset=asset3, container=container1)
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        self.assertEqual(self.deserialize(resp)['objects'][0]['container'],
                         container1.name)
        self.assertEqual(self.deserialize(resp)['objects'][1]['container'],
                         container2.name)
        self.assertEqual(
            self.deserialize(resp)['objects'][0]['asset']['asset_id'],
            asset1.asset_id)
        self.assertEqual(
            self.deserialize(resp)['objects'][1]['asset']['asset_id'],
            asset2.asset_id)
        self.assertEqual(
            self.deserialize(resp)['objects'][0]['asset']['type'],
            asset1.type)
        self.assertEqual(
            self.deserialize(resp)['objects'][1]['asset']['type'],
            asset2.type)
        self.assertEqual(
            self.deserialize(resp)['objects'][0]['asset']['title'],
            asset1.title)
        self.assertEqual(
            self.deserialize(resp)['objects'][1]['asset']['title'],
            asset2.title)

    def test_get_detail(self):
        """Test that a user can get details of a single section asset"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset = create_html_asset(type='text', title='Test Asset',
                                   body='Test content')
        SectionAsset.objects.create(section=section, asset=asset, container=container1)
        uri = '/api/0.1/stories/%s/sections/%s/assets/%s/' % (
            story.story_id, section.section_id, asset.asset_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['container'],
                         container1.name)
        self.assertEqual(
            self.deserialize(resp)['asset']['asset_id'],
            asset.asset_id)
        self.assertEqual(
            self.deserialize(resp)['asset']['type'],
            asset.type)
        self.assertEqual(
            self.deserialize(resp)['asset']['title'],
            asset.title)

    def test_post_list(self):
        """Test that a user can associate an asset with a story"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset = create_html_asset(type='text', title='Test Asset',
                                   body='Test content', owner=self.user)
        self.assertEqual(SectionAsset.objects.count(), 0)
        post_data = {
            'asset': self.get_asset_uri(asset),
            'container': container1.name
        }
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        self.api_client.client.login(username=self.username, password=self.password)
        resp = self.api_client.post(uri, format='json', data=post_data)
        self.assertHttpCreated(resp)
        self.assertEqual(SectionAsset.objects.count(), 1)
        section_asset = SectionAsset.objects.get()
        self.assertEqual(section_asset.section, section)
        self.assertEqual(section_asset.container, container1)

    def test_delete_detail(self):
        """Tests that a user can remove an asset from a section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset1 = create_html_asset(type='text', title='Test Asset',
                                   body='Test content', owner=self.user)
        asset2 = create_html_asset(type='text', title='Test Asset 2',
                                   body='Test content 2', owner=self.user)
        SectionAsset.objects.create(section=section, asset=asset1, container=container1)
        SectionAsset.objects.create(section=section, asset=asset2, container=container2)
        self.assertEqual(SectionAsset.objects.count(), 2)
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        uri = '/api/0.1/stories/%s/sections/%s/assets/%s/' % (
            story.story_id, section.section_id, asset1.asset_id)
        resp = self.api_client.delete(uri)
        self.assertHttpAccepted(resp)
        self.assertEqual(SectionAsset.objects.count(), 1)

    def test_delete_detail_unauthenticated(self):
        """Test that an anonymous user cannot remove an asset from a section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset1 = create_html_asset(type='text', title='Test Asset',
                                   body='Test content', owner=self.user)
        asset2 = create_html_asset(type='text', title='Test Asset 2',
                                   body='Test content 2', owner=self.user)
        SectionAsset.objects.create(section=section, asset=asset1, container=container1)
        SectionAsset.objects.create(section=section, asset=asset2, container=container2)
        self.assertEqual(SectionAsset.objects.count(), 2)
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        uri = '/api/0.1/stories/%s/sections/%s/assets/%s/' % (
            story.story_id, section.section_id, asset1.asset_id)
        resp = self.api_client.delete(uri)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(SectionAsset.objects.count(), 2)

    def test_delete_detail_other_user(self):
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user2)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset1 = create_html_asset(type='text', title='Test Asset',
                                   body='Test content', owner=self.user2)
        asset2 = create_html_asset(type='text', title='Test Asset 2',
                                   body='Test content 2', owner=self.user2)
        SectionAsset.objects.create(section=section, asset=asset1, container=container1)
        SectionAsset.objects.create(section=section, asset=asset2, container=container2)
        self.assertEqual(SectionAsset.objects.count(), 2)
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        uri = '/api/0.1/stories/%s/sections/%s/assets/%s/' % (
            story.story_id, section.section_id, asset1.asset_id)
        resp = self.api_client.delete(uri)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(SectionAsset.objects.count(), 2)

    def test_delete_list(self):
        """Tests that a user can't remove all assets from a section"""
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status="published",
                             language="en", author=self.user)
        layout = SectionLayout.objects.get(sectionlayouttranslation__name="Side by Side")
        container1 = Container.objects.get(name='left')
        container2 = Container.objects.get(name='right')
        section = create_section(title="Test Section 1", story=story,
                                  layout=layout)
        asset1 = create_html_asset(type='text', title='Test Asset',
                                   body='Test content', owner=self.user)
        asset2 = create_html_asset(type='text', title='Test Asset 2',
                                   body='Test content 2', owner=self.user)
        SectionAsset.objects.create(section=section, asset=asset1, container=container1)
        SectionAsset.objects.create(section=section, asset=asset2, container=container2)
        self.assertEqual(SectionAsset.objects.count(), 2)
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/sections/%s/assets/' % (story.story_id,
            section.section_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        resp = self.api_client.delete(uri)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(SectionAsset.objects.count(), 2)


class StoryExploreResourceTest(ResourceTestCase):
    """Test story exploration REST endpoint"""

    def setUp(self):
        super(StoryExploreResourceTest, self).setUp()
        self.resource = StoryResource()
        self._rebuild_index()

    def _rebuild_index(self):
        """Call management command to rebuild the Haystack search index"""
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False, verbosity=0)

    def test_distance_query(self):
        """
        Test that resource can be filtered based on distance about a point
        """
        locations = [
            Location.objects.create(name="The Piton Foundation", lat=39.7438167, lng=-104.9884953),
            Location.objects.create(name="Hull House", lat=41.8716782, lng=-87.6474517)
        ]
        story = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        story.locations.add(locations[0])
        story.save()
        story2 = create_story(title="Test Story 2", summary="Test Summary 2",
                             byline="Test Byline 2", status='published')
        story2.locations.add(locations[1])
        story2.save()
        # If south migrations are enabled, we need to explicitly rebuild
        # the indexes because the RealTimeIndex signal handlers don't get
        # wired up. 
        # See https://github.com/toastdriven/django-haystack/issues/599
        # In general, I think we can work around this by just setting
        # SOUTH_TESTS_MIGRATE = False in the settings
        #self._rebuild_index()
        req = HttpRequest()
        req.method = 'GET'
        req.GET['near'] = '39.7414581054089@-104.9877892025,1'
        resp = self.resource.explore_get_list(req)
        dehydrated = simplejson.loads(resp.content)
        self.assertEqual(len(dehydrated['objects']), 1)
        self.assertEqual(dehydrated['objects'][0]['story_id'], story.story_id)

    def test_explore_get_list_only_published(self):
        """Test that story exploration endpoint doesn't show unpublished stories"""
        story1 = create_story(title="Test Story", summary="Test Summary",
                             byline="Test Byline", status='published')
        
        story2 = create_story(title="Test Story 2", summary="Test Summary 2",
                             byline="Test Byline 2", status='draft')
        resp = self.api_client.get('/api/0.1/stories/explore/')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['story_id'], story1.story_id)


class StoryTemplateResourceTest(ResourceTestCase):
    fixtures = ['section_layouts.json', 'story_templates.json']

    def setUp(self):
        super(StoryTemplateResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()

    def test_get_list(self):
        uri = '/api/0.1/stories/templates/'
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        self.assertEqual(self.deserialize(resp)['objects'][0]['title'],
                         "PhotoVoice")
        self.assertEqual(self.deserialize(resp)['objects'][1]['title'],
                         "Explainer")

    def test_get_detail(self):
        story_template = StoryTemplate.objects.all()[0]
        uri = '/api/0.1/stories/templates/%s/' % (story_template.template_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'], story_template.title)
        self.assertEqual(self.deserialize(resp)['description'], story_template.description)


class StoryCategoryResourceTest(ResourceTestCase):
    def setUp(self):
        super(StoryCategoryResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = StoryResource()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary, byline=byline,
                                  status='published', author=self.user)
        for cat_name in ('Schools', 'Violence', 'Food', 'Healthcare'):
            create_category(cat_name)

    def test_put_list_replace(self):
        """Test that the categories can be replaced by a new set"""
        self.story.topics.add(*list(Category.objects.filter(categorytranslation__name__in=('Schools', 'Violence'))))
        self.story.save()
        self.assertEqual(self.story.topics.count(), 2)
        put_data = [cat.id for cat in
                     Category.objects.filter(categorytranslation__name__in=('Food', 'Healthcare'))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/topics/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.topics.count(), 2)
        topic_ids = [cat.id for cat in self.story.topics.all()]
        self.assertEqual(topic_ids, put_data)

    def test_put_list_new(self):
        """Test that a story's categories can be set"""
        put_data = [cat.id for cat in
                     Category.objects.filter(categorytranslation__name__in=('Food', 'Healthcare'))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/topics/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.topics.count(), 2)
        topic_ids = [cat.id for cat in self.story.topics.all()]
        self.assertEqual(topic_ids, put_data)


class StoryPlaceResourceTest(ResourceTestCase):
    def setUp(self):
        super(StoryPlaceResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = StoryResource()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary, byline=byline,
                                  status='published', author=self.user)
        neighborhood = GeoLevel.objects.create(name='Neighborhood',
            slug='neighborhood')
        for name in ("Humboldt Park", "Wicker Park", "Logan Square"):
            Place.objects.create(name=name, geolevel=neighborhood)

    def test_put_list_replace(self):
        """Test that the places can be replaced by a new set"""
        self.story.places.add(*list(Place.objects.filter(name__in=('Humboldt Park', 'Wicker Park'))))
        self.story.save()
        self.assertEqual(self.story.places.count(), 2)
        put_data = [place.place_id for place in
                    Place.objects.filter(name="Logan Square")]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/places/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.places.count(), 1)
        ids = [place.place_id for place in self.story.places.all()]
        self.assertEqual(ids, put_data)

    def test_put_list_new(self):
        """Test that a story's categories can be set"""
        self.story.save()
        self.assertEqual(self.story.places.count(), 0)
        put_data = [place.place_id for place in
                    Place.objects.filter(name="Logan Square")]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/places/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.places.count(), 1)
        ids = [place.place_id for place in self.story.places.all()]
        self.assertEqual(ids, put_data)


class StoryOrganizationResourceTest(ResourceTestCase):
    def setUp(self):
        super(StoryOrganizationResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = StoryResource()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary, byline=byline,
                                  status='published', author=self.user)
        create_organization(name="Mile High Connects")
        create_organization(name="Piton Foundation")
        create_organization(name="Urban Land Conservancy")
        create_organization(name="America Scores Denver")

    def test_put_list_new(self):
        """Test that a story's categories can be set"""
        self.user.organizations.add(*list(Organization.objects.all()))
        self.user.save()
        self.story.save()
        self.assertEqual(self.story.organizations.count(), 0)
        put_data = [org.organization_id for org in
                    Organization.objects.filter(organizationtranslation__name="Piton Foundation")]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/organizations/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.organizations.count(), 1)
        ids = [org.organization_id for org in self.story.organizations.all()]
        self.assertEqual(ids, put_data)

    def test_put_list_replace(self):
        """Test that the organizations can be replaced by a new set"""
        self.user.organizations.add(*list(Organization.objects.all()))
        self.user.save()
        self.story.organizations.add(*list(Organization.objects.filter(organizationtranslation__name__in=("Urban Land Conservancy", "America Scores Denver"))))
        self.story.save()
        self.assertEqual(self.story.organizations.count(), 2)
        put_data = [organization.organization_id for organization in
                    Organization.objects.filter(organizationtranslation__name__in=("Mile High Connects", "Piton Foundation"))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/organizations/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.organizations.count(), 2)
        ids = [organization.organization_id for organization in self.story.organizations.all()]
        self.assertEqual(ids, put_data)

    def test_put_list_non_member(self):
        """Test that a user cannot add organizations to a story unless they're a member of the organization"""
        self.assertEqual(self.story.organizations.count(), 0)
        put_data = [organization.organization_id for organization in
                    Organization.objects.filter(organizationtranslation__name__in=("Mile High Connects", "Piton Foundation"))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/organizations/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpBadRequest(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.organizations.count(), 0)


class StoryProjectResourceTest(ResourceTestCase):
    def setUp(self):
        super(StoryProjectResourceTest, self).setUp()
        # Use our fixed TestApiClient instead of the default
        self.api_client = FixedTestApiClient()
        self.resource = StoryResource()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        title = ('Transportation Challenges Limit Education Choices for '
                 'Denver Parents')
        summary = """
            Many families in the Denver metro area use public
            transportation instead of a school bus because for them, a
            quality education is worth hours of daily commuting. Colorado's
            school choice program is meant to foster educational equity,
            but the families who benefit most are those who have time and
            money to travel. Low-income families are often left in a lurch.
            """
        byline = "Mile High Connects"
        self.story = create_story(title=title, summary=summary, byline=byline,
                                  status='published', author=self.user)
        create_project(name="Finding a Bite: Food Access in the Children's Corridor")
        create_project(name="Redeveloping The Holly: From Gang Violence to Hope")
        create_project(name="Soccer in the Corridor")
        create_project(name="Stories of Integration")

    def test_put_list_new(self):
        """Test that a story's categories can be set"""
        self.user.projects.add(*list(Project.objects.all()))
        self.user.save()
        self.story.save()
        self.assertEqual(self.story.projects.count(), 0)
        put_data = [proj.project_id for proj in
                    Project.objects.filter(projecttranslation__name="Soccer in the Corridor")]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/projects/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.projects.count(), 1)
        ids = [proj.project_id for proj in self.story.projects.all()]
        self.assertEqual(ids, put_data)

    def test_put_list_replace(self):
        """Test that the projects can be replaced by a new set"""
        self.user.projects.add(*list(Project.objects.all()))
        self.user.save()
        self.story.projects.add(*list(Project.objects.filter(projecttranslation__name__in=("Finding a Bite: Food Access in the Children's Corridor", "Redeveloping The Holly: From Gang Violence to Hope"))))
        self.story.save()
        self.assertEqual(self.story.projects.count(), 2)
        put_data = [project.project_id for project in
                    Project.objects.filter(projecttranslation__name__in=("Soccer in the Corridor", "Stories of Integration"))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/projects/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.projects.count(), 2)
        ids = [project.project_id for project in self.story.projects.all()]
        self.assertEqual(ids, put_data)

    def test_put_list_non_member(self):
        """Test that a user cannot add projects to a story unless they're a member of the project"""
        self.assertEqual(self.story.projects.count(), 0)
        put_data = [project.project_id for project in
                    Project.objects.filter(projecttranslation__name__in=("Soccer in the Corridor", "Stories of Integration"))]
        self.api_client.client.login(username=self.username, password=self.password)
        uri = '/api/0.1/stories/%s/projects/' % (self.story.story_id)
        response = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpBadRequest(response)
        self.story = Story.objects.get(story_id=self.story.story_id)
        self.assertEqual(self.story.projects.count(), 0)


class StoryRelationResourceTest(ResourceTestCase):
    def setUp(self):
        super(StoryRelationResourceTest, self).setUp()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create_user(self.username, 'test@example.com', self.password)
        self.user2 = User.objects.create_user("test2", "test2@example.com",
                                              "test2")
        self.story = create_story(title="Test Story", summary="Test Summary",
                                  byline="Test Byline", status='published',
                                  author=self.user)

    def test_get_list(self):
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user)
        story2 = create_story(title="Test Story 2",
                              summary="Test Story Summary 2",
                              byline="Test Story Byline 2",
                              status='published',
                              author=self.user)
        related_story2 = create_story(title="Test Related Story", 
                             summary="Test Related Story Summary",
                             byline="Test Related Story Byline",
                             status='published',
                             author=self.user)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        StoryRelation.objects.create(source=self.story,
            target=related_story, relation_type='connected')
        # Create a second story relation to make sure filtering by
        # story works correctly
        StoryRelation.objects.create(source=story2,
            target=related_story2, relation_type='connected')
        self.assertEqual(len(self.story.related_stories.all()), 1)
        self.assertEqual(self.story.related_stories.all()[0], 
                         related_story)
        # Test getting the relation through the target story
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['relation_type'], 'connected')
        self.assertEqual(self.deserialize(resp)['objects'][0]['source'], self.story.story_id)
        self.assertEqual(self.deserialize(resp)['objects'][0]['target'], related_story.story_id)
        # Test getting the relation through the source story
        uri = '/api/0.1/stories/%s/related/' % (self.story.story_id)
        resp = self.api_client.get(uri)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['relation_type'], 'connected')
        self.assertEqual(self.deserialize(resp)['objects'][0]['source'], self.story.story_id)
        self.assertEqual(self.deserialize(resp)['objects'][0]['target'], related_story.story_id)

    def test_post_list(self):
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        post_data = {
            'relation_type': 'connected',
            'source': self.story.story_id,
            'target': related_story.story_id,
        }
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        self.api_client.client.login(username=self.username, password=self.password)
        resp = self.api_client.post(uri,  format='json', 
                                    data=post_data)
        self.assertHttpCreated(resp)
        self.assertEqual(StoryRelation.objects.count(), 1)
        created_rel = StoryRelation.objects.get()
        self.assertEqual(created_rel.relation_type,
                         post_data['relation_type'])
        self.assertEqual(created_rel.source, self.story)
        self.assertEqual(created_rel.target, related_story)

    def test_post_list_unauthenticated(self):
        """Test that an aunauthenticated user can't create a relation"""
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        post_data = {
            'relation_type': 'connected',
            'source': self.story.story_id,
            'target': related_story.story_id,
        }
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        resp = self.api_client.post(uri, format='json',  data=post_data)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(len(StoryRelation.objects.all()), 0)

    def test_post_list_connected_unauthorized(self):
        """
        Test that a user can't define a connected story relation for a story
        they don't own
        """
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user2)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        post_data = {
            'relation_type': 'connected',
            'source': self.story.story_id,
            'target': related_story.story_id,
        }
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        resp = self.api_client.post(uri, format='json',  data=post_data)
        self.assertHttpUnauthorized(resp)
        self.assertEqual(len(StoryRelation.objects.all()), 0)

    def test_post_list_connected_other_users_story(self):
        """
        Test that a user can define their own story as connected
        to another user's story
        """
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user2)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        post_data = {
            'relation_type': 'connected',
            'source': related_story.story_id,
            'target': self.story.story_id,
        }
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        self.api_client.client.login(username=self.username, password=self.password)
        resp = self.api_client.post(uri,  format='json', 
                                    data=post_data)
        self.assertHttpCreated(resp)
        self.assertEqual(StoryRelation.objects.count(), 1)
        created_rel = StoryRelation.objects.get()
        self.assertEqual(created_rel.relation_type,
                         post_data['relation_type'])
        self.assertEqual(created_rel.source, related_story)
        self.assertEqual(created_rel.target, self.story)

    def test_put_list(self):
        related_story = create_story(title="Test Related Story", 
             summary="Test Related Story Summary",
             byline="Test Related Story Byline",
             status='published',
             author=self.user)
        story2 = create_story(title="Test Story 2",
                              summary="Test Story Summary 2",
                              byline="Test Story Byline 2",
                              status='published',
                              author=self.user)
        self.assertEqual(len(self.story.related_stories.all()), 0)
        put_data = [
            {
                'relation_type': 'connected',
                'source': self.story.story_id,
                'target': related_story.story_id,
            },
            {
                'relation_type': 'connected',
                'source': story2.story_id,
                'target': related_story.story_id,
            },
        ]
        # Test getting the relation through the target story
        uri = '/api/0.1/stories/%s/related/' % (related_story.story_id)
        self.api_client.client.login(username=self.username, password=self.password)
        resp = self.api_client.get(uri)
        resp = self.api_client.put(uri, format='json', data=put_data)
        self.assertHttpAccepted(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        related_story = Story.objects.get(story_id=related_story.story_id)
        self.assertEqual(len(related_story.related_to.all()), 2)
