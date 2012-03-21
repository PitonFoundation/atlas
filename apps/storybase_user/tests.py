from django.test import TestCase
from django.utils import translation
from storybase.utils import slugify
from models import (Organization, OrganizationTranslation, Project,
    ProjectTranslation)

class OrganizationModelTest(TestCase):
    def _create_organization(self, name, language):
        org = Organization()
        org.save()
        trans = OrganizationTranslation(name=name, language=language,
            organization=org)
        trans.save()
        return org

    def test_get_translated_field(self):
        """
        Tests that you can get a translated field as if it were the model's own
        """
        org_name_en = "Mile High Connects"
        org = self._create_organization(org_name_en, "en")
        self.assertEqual(org.name, org_name_en)

    def test_get_translated_field_default_fallback(self):
        """
        Tests that if a translated field doesn't exist in the current
        language, it falls back to the default language.
        """
        org_name_en = "Mile High Connects"
        org = self._create_organization(org_name_en, "en")
        translation.activate('es')
        self.assertEqual(org.name, org_name_en)

    def test_get_translated_field_first_fallback(self):
        """
        Tests that if a translated field doesn't exist in the current
        language, and it doesn't exist in the default language, the 
        first available language is used
        """
        org_name_es = "Mile High Conecta"
        org = self._create_organization(org_name_es, 'es')
        translation.activate('en')
        self.assertEqual(org.name, org_name_es)

    def test_auto_slug(self):
        name = 'Mile High Connects'
        organization = Organization()
        organization.save()
        organization_translation = OrganizationTranslation(name=name, organization=organization)
        self.assertEqual(organization_translation.slug, '')
        organization_translation.save()
        self.assertEqual(organization_translation.slug, slugify(name))

class OrganizationApiTest(TestCase):
    def test_create_organization(self):
        from storybase_user.models import create_organization, Organization

        name = "Mile High Connects"
        website_url = "http://www.urbanlandc.org/collaboratives/mile-high-connects/"
        description = 'Mile High Connects (formerly know as the Mile High Transit Opportunity Collaborative) is an emerging collaborative of nonprofit and philanthropic organizations working together to ensure the creation of the region’s $6.7 billion FasTracks transit system benefits all communities in the region, including low-income populations.'
        with self.assertRaises(Organization.DoesNotExist):
            Organization.objects.get(organizationtranslation__name=name)
        org = create_organization(name=name, description=description, website_url=website_url)
        self.assertEqual(org.name, name)
        self.assertEqual(org.description, description)
        self.assertEqual(org.website_url, website_url)
        retrieved_org = Organization.objects.get(pk=org.pk)
        self.assertEqual(retrieved_org.name, name)
        self.assertEqual(retrieved_org.description, description)
        self.assertEqual(retrieved_org.website_url, website_url)

class ProjectModelTest(TestCase):
    def test_auto_slug(self):
        name = 'The Metro Denver Regional Equity Atlas'
        project = Project()
        project.save()
        project_translation = ProjectTranslation(name=name, project=project)
        self.assertEqual(project_translation.slug, '')
        project_translation.save()
        self.assertEqual(project_translation.slug, slugify(name))

class ProjectApiTest(TestCase):
    def test_create_project(self):
        from storybase_user.models import create_project, Project 

        name = "The Metro Denver Regional Equity Atlas"
        description = """
            The Denver Regional Equity Atlas is a product of Mile High
            Connects (MHC), which came together in 2011 to ensure that 
            the region’s significant investment in new rail and bus
            service will provide greater access to opportunity and a
            higher quality of life for all of the region’s residents, but
            especially for economically disadvantaged populations who
            would benefit the most from safe, convenient transit service.

            The Atlas visually documents the Metro Denver region’s
            demographic, educational, employment, health and housing
            characteristics in relation to transit, with the goal of
            identifying areas of opportunity as well as challenges to
            creating and preserving quality communities near transit.
            """
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(projecttranslation__name=name)
        project = create_project(name=name, description=description)
        self.assertEqual(project.name, name)
        self.assertEqual(project.description, description)
        retrieved_project = Project.objects.get(pk=project.pk)
        self.assertEqual(retrieved_project.name, name)
        self.assertEqual(retrieved_project.description, description)
