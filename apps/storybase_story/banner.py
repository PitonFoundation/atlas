import random
from django.db.models import Count
from django.template.loader import render_to_string
from storybase_story.models import Story
from storybase_taxonomy.models import Category

class BannerRegistry(object):
    """
    A registry of banner implementations.

    You shouldn't instantiate this, but instead import
    ``storybase_story.banner.registry`` to register your banner classes.

    Example::

        from storybase_story.banner import Banner, registry

        class MyBanner(Banner):
            banner_id = "my_banner"
            ...

        registry.register(MyBanner)

    """
    _banner_classes = {}

    def register(self, banner_cls):
        """
        Register a new banner implementation.
        """
        self._banner_classes[banner_cls.banner_id] = banner_cls

    def get(self, banner_id, **kwargs):
        """
        Get a banner instance using a specific implementation.

        Arguments:
        banner_id -- banner_id attribute of the Banner subclass that should
                     be instantiated

        Keyword arguments are passed to the constructor for the banner.


        """
        return self._banner_classes[banner_id](**kwargs)

    def get_random(self, **kwargs):
        """
        Get a banner instance using a randomly-selected implementation.
        """
        banner_id = random.choice(self._banner_classes.keys())
        return self.get_banner(banner_id, **kwargs)


class Banner(object):
    """
    Base class for banner implementations.

    In most cases, just override get_objects in the subclass to use a
    different strategy for selecting stories.

    """
    # Override this in subclasses. This is used to retrieve a banner instance
    # via BannerRegistry
    banner_id = "base"
    template_name = "storybase_story/banner.html"
    # TODO: Decide on real value for this default
    img_width = 335

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    # Using "objects" instead of "stories" to anticipate including other
    # things (projects, organizations, users) in banner one day.
    def get_objects(self, count=10):
        """
        Get items to be displayed in the banner.

        Keyword arguments:
        count -- The number of items to show in the banner (default 10)

        """
        return Story.objects.public()[:count]

    def encode_args(self):
        """
        Encode arguments used to initialize a Banner instance as a string.

        This is mostly to provide a way to differentiate between different
        instantiations of the same banner class when looking at analytics.

        """
        # The base class doesn't know how to handle arguments. But this should
        # be implemented in subclasses that do take arguments.
        return ""

    def get_context_data(self):
        """
        Return a dictionary that will be used as context when rendering
        the banner template.
        """
        return {
            'banner_args': self.encode_args(),
            'banner_id': self.banner_id,
            'objects': [o.normalize_for_view(img_width=self.img_width)
                        for o in self.get_objects()],
        }

    def render(self):
        """
        Return a string containing the HTML for the rendered banner
        """
        # TODO: Cache output
        rendered = render_to_string(self.template_name, self.get_context_data())
        return rendered


class RandomBanner(Banner):
    """
    Banner that shows randomly selected stories

    """
    banner_id = "random"

    def get_objects(self, count=10):
        # Sort the objects randomly. Unfortunately, we can't use call
        # the parent's get_objects because QuerySets can't be reordered
        # after being sliced.
        return Story.objects.public().order_by('?')[:count]


class TopicBanner(Banner):
    """
    Banner that selects stories with a specified topic.
    """
    banner_id = "topic"

    def __init__(self, **kwargs):
        """
        Keyword arguments:
        count -- number of stories to select (default 10). This is used
                 to filter out Topics with too few stories when a random
                 topic is desired.
        slug  -- Slug of the Topic to be selected. If no value is selected
                 a topic is selected randomly.

        """
        super(TopicBanner, self).__init__(**kwargs)
        count = getattr(self, 'count', 10)
        try:
            slug = getattr(self, 'slug')
            self.topic = Category.objects.get(categorytranslation__slug=slug)
        except AttributeError:
            # No topic was specified. Get a random one
            self.topic = self.get_random_topic(count)
            if self.topic:
                self.slug = self.topic.slug

    def get_random_topic(self, min_count):
        # Limit elgible topics to only those with at least ``count``
        # associated stories
        topics = Category.objects.filter(stories__status='published')\
                         .annotate(num_stories=Count('stories'))\
                         .filter(num_stories__gte=min_count)
        if not topics.count():
            # No topics with stories
            return None

        return topics[0]

    def get_objects(self, count=10):
        if not self.topic:
            # No eligible topic, return an empty list
            return []

        # Return all the stories
        return self.topic.stories.public().order_by('?')[:count]

    def encode_args(self):
        return getattr(self, 'slug', "")


# Create a single instance of BannerRegistry for import elsewhere
registry = BannerRegistry()

# Register our banner implementations
registry.register(RandomBanner)
registry.register(TopicBanner)
