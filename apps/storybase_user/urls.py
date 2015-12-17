try:
    import shortuuid
except ImportError:
    shortuuid = None

from django.conf import settings
from django.conf.urls import patterns, url
from storybase_user.views import (OrganizationDetailView, OrganizationListView,
    OrganizationShareView, OrganizationSharePopupView,
    OrganizationEmbedView, OrganizationEmbedPopupView,
    ProjectDetailView, ProjectListView,
    ProjectShareView, ProjectSharePopupView,
    ProjectEmbedView, ProjectEmbedPopupView,
    UserProfileDetailView, UserProfileShareView, UserProfileSharePopupView,
    CreateOrganizationView, CreateProjectView)

uuid_pattern = settings.UUID_PATTERN

urlpatterns = patterns('',
    url(r'organizations/$', OrganizationListView.as_view(),
        name='organization_list'),
    url(r'organizations/(?P<organization_id>{})/$'.format(uuid_pattern),
        OrganizationDetailView.as_view(), name='organization_detail_by_id'),
    url(r'organizations/(?P<slug>[0-9a-z-]+)/$',
        OrganizationDetailView.as_view(), name='organization_detail'),
    url(r'organizations/(?P<organization_id>{})/share/$'.format(uuid_pattern),
        OrganizationShareView.as_view(),
        name='organization_share'),
    url(r'organizations/(?P<slug>[0-9a-z-]+)/share/$',
        OrganizationShareView.as_view(),
        name='organization_share'),
    url(r'organizations/(?P<organization_id>{})/share/popup/$'.format(uuid_pattern),
        OrganizationSharePopupView.as_view(),
        name='organization_share_popup'),
    url(r'organizations/(?P<slug>[0-9a-z-]+)/share/popup/$',
        OrganizationSharePopupView.as_view(),
        name='organization_share_popup'),
    url(r'organizations/(?P<organization_id>{})/embed/$'.format(uuid_pattern),
        OrganizationEmbedView.as_view(),
        name='organization_embed'),
    url(r'organizations/(?P<slug>[0-9a-z-]+)/embed/$',
        OrganizationEmbedView.as_view(),
        name='organization_embed'),
    url(r'organizations/(?P<organization_id>{})/embed/popup/$'.format(uuid_pattern),
        OrganizationEmbedPopupView.as_view(),
        name='organization_embed_popup'),
    url(r'organizations/(?P<slug>[0-9a-z-]+)/embed/popup/$',
        OrganizationEmbedPopupView.as_view(),
        name='organization_embed_popup'),
    url(r'create-organization/$', CreateOrganizationView.as_view(),
        name='create_organization'),
    url(r'projects/$', ProjectListView.as_view(), name='project_list'),
    url(r'projects/(?P<project_id>{})/$'.format(uuid_pattern),
        ProjectDetailView.as_view(), name='project_detail_by_id'),
    url(r'projects/(?P<slug>[0-9a-z-]+)/$',
        ProjectDetailView.as_view(), name='project_detail'),
    url(r'projects/(?P<project_id>{})/share/$'.format(uuid_pattern),
        ProjectShareView.as_view(), name='project_share'),
    url(r'projects/(?P<slug>[0-9a-z-]+)/share/$',
        ProjectShareView.as_view(), name='project_share'),
    url(r'projects/(?P<project_id>{})/share/popup/$'.format(uuid_pattern),
        ProjectSharePopupView.as_view(), name='project_share_popup'),
    url(r'projects/(?P<slug>[0-9a-z-]+)/share/popup/$',
        ProjectSharePopupView.as_view(), name='project_share_popup'),
    url(r'projects/(?P<project_id>{})/embed/$'.format(uuid_pattern),
        ProjectEmbedView.as_view(),
        name='project_embed'),
    url(r'projects/(?P<slug>[0-9a-z-]+)/embed/$',
        ProjectEmbedView.as_view(),
        name='project_embed'),
    url(r'projects/(?P<project_id>{})/embed/popup/$'.format(uuid_pattern),
        ProjectEmbedPopupView.as_view(),
        name='project_embed_popup'),
    url(r'projects/(?P<slug>[0-9a-z-]+)/embed/popup/$',
        ProjectEmbedPopupView.as_view(),
        name='project_embed_popup'),
    url(r'create-project/$', CreateProjectView.as_view(),
        name='create_project'),
    url(r'users/(?P<profile_id>{})/$'.format(uuid_pattern),
        UserProfileDetailView.as_view(), name='userprofile_detail'),
    url(r'users/(?P<profile_id>{})/share/$'.format(uuid_pattern),
        UserProfileShareView.as_view(),
        name='userprofile_share'),
    url(r'users/(?P<profile_id>{})/share/popup/$'.format(uuid_pattern),
        UserProfileSharePopupView.as_view(),
        name='userprofile_share_popup'),
)

if shortuuid:
    alphabet = shortuuid.get_alphabet()
    urlpatterns = urlpatterns + patterns('',
        url(r"users/(?P<short_profile_id>[%s]+)/$" % (alphabet),
            UserProfileDetailView.as_view(), name='userprofile_detail'),
        url(r"users/(?P<short_profile_id>[%s]+)/share/$" % (alphabet),
            UserProfileShareView.as_view(),
            name='userprofile_share'),
        url(r"users/(?P<short_profile_id>[%s]+)/share/popup/$" % (alphabet),
            UserProfileSharePopupView.as_view(),
            name='userprofile_share_popup'),
    )
