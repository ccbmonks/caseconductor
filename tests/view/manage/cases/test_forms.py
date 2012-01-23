# Case Conductor is a Test Case Management system.
# Copyright (C) 2011-12 Mozilla
#
# This file is part of Case Conductor.
#
# Case Conductor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Case Conductor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Case Conductor.  If not, see <http://www.gnu.org/licenses/>.
"""
Tests for case management forms.

"""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.datastructures import MultiValueDict

from django.contrib.auth.models import Permission

from .... import factories as F



class AddCaseFormTest(TestCase):
    """Tests for add-case form."""
    def setUp(self):
        """All add-case tests require at least one product version."""
        self.productversion = F.ProductVersionFactory.create(version="1.0")
        self.product = self.productversion.product


    @property
    def user(self):
        """A lazily-created user with create-cases perm."""
        if not hasattr(self, "_user"):
            self._user = F.UserFactory.create()
            perm = Permission.objects.get(codename="create_cases")
            self._user.user_permissions.add(perm)
        return self._user


    @property
    def form(self):
        from cc.view.manage.cases.forms import AddCaseForm
        return AddCaseForm


    def get_form_data(self):
        defaults = {
            "product": [self.product.id],
            "productversion": [self.productversion.id],
            "name": ["Can register."],
            "description": ["A user can sign up for the site."],
            "steps-TOTAL_FORMS": [1],
            "steps-INITIAL_FORMS": [0],
            "steps-0-instruction": ["Fill in form and submit."],
            "steps-0-expected": ["You should get a welcome email."],
            }
        return MultiValueDict(defaults)


    def test_product_id(self):
        """Product choices render data-product-id attr."""
        html = unicode(self.form()["product"])

        self.assertIn('data-product-id="{0}"'.format(self.product.id), html)


    def test_productversion_product_id(self):
        """Product version choices render data-product-id attr."""
        html = unicode(self.form()["productversion"])

        self.assertIn('data-product-id="{0}"'.format(self.product.id), html)



    def test_success(self):
        """Can add a test case."""
        form = self.form(data=self.get_form_data())

        cv = form.save().versions.get()

        self.assertEqual(cv.name, "Can register.")


    def test_created_by(self):
        """If user is provided, created objects have created_by set."""
        form = self.form(data=self.get_form_data(), user=self.user)

        cv = form.save().versions.get()

        self.assertEqual(cv.case.created_by, self.user)
        self.assertEqual(cv.created_by, self.user)
        self.assertEqual(cv.steps.get().created_by, self.user)


    def test_wrong_product_version(self):
        """Selecting version of wrong product results in validation error."""
        data = self.get_form_data()
        data["product"] = F.ProductFactory.create().id

        form = self.form(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'__all__': [u'Must select a version of the correct product.']}
            )


    def test_no_initial_suite(self):
        """If no manage-suite-cases perm, no initial_suite field."""
        self.assertNotIn("initial_suite", self.form().fields)


    def test_initial_suite(self):
        """Can pick an initial suite for case to be in (with right perms)."""
        self.user.user_permissions.add(
            Permission.objects.get(codename="manage_suite_cases"))
        suite = F.SuiteFactory.create(product=self.product)

        data = self.get_form_data()
        data["initial_suite"] = suite.id

        case = self.form(data=data, user=self.user).save()

        self.assertEqual(list(case.suites.all()), [suite])


    def test_wrong_suite_product(self):
        """Selecting suite from wrong product results in validation error."""
        self.user.user_permissions.add(
            Permission.objects.get(codename="manage_suite_cases"))
        suite = F.SuiteFactory.create() # some other product

        data = self.get_form_data()
        data["initial_suite"] = suite.id

        form = self.form(data=data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"__all__": [u"Must select a suite for the correct product."]}
            )


    def test_tag_autocomplete_url(self):
        """Tag autocomplete field renders data-autocomplete-url."""
        self.assertIn(
            'data-autocomplete-url="{0}"'.format(
                reverse("manage_tags_autocomplete")),
            unicode(self.form()["add_tags"])
            )


    def test_tag(self):
        """Can tag a new case with some existing tags."""
        t1 = F.TagFactory.create(name="foo")
        t2 = F.TagFactory.create(name="bar")
        data = self.get_form_data()
        data.setlist("tag-tag", [t1.id, t2.id])

        caseversion = self.form(data=data).save().versions.get()

        self.assertEqual(list(caseversion.tags.all()), [t1, t2])


    def test_new_tag(self):
        """Can create a new case with a new tag."""
        data = self.get_form_data()
        data.setlist("tag-newtag", ["baz"])

        caseversion = self.form(data=data).save().versions.get()

        self.assertEqual([t.name for t in caseversion.tags.all()], ["baz"])


    def test_attachment(self):
        """Can add an attachment to the new case."""
        files = MultiValueDict(
            {"add_attachment": [SimpleUploadedFile("name.txt", "contents")]}
            )

        caseversion = self.form(
            data=self.get_form_data(), files=files).save().versions.get()

        self.assertEqual(len(caseversion.attachments.all()), 1)


    def test_and_later_versions(self):
        """Can add multiple versions of a test case at once."""
        F.ProductVersionFactory.create(
            product=self.product, version="0.5")
        newer_version = F.ProductVersionFactory.create(
            product=self.product, version="1.1")

        data = self.get_form_data()
        data["and_later_versions"] = 1

        case = self.form(data=data).save()

        self.assertEqual(
            [v.productversion for v in case.versions.all()],
            [self.productversion, newer_version]
            )



class StepFormSetTest(TestCase):
    """Tests for StepFormSet."""
    @property
    def formset(self):
        from cc.view.manage.cases.forms import StepFormSet
        return StepFormSet


    def test_commit_false(self):
        """Can save a StepFormSet with commit=False."""
        fs = self.formset(
            data={
                "steps-TOTAL_FORMS": 1,
                "steps-INITIAL_FORMS": 0,
                "steps-0-instruction": "instruction",
                "steps-0-expected": "expected",
                }
            )

        steps = fs.save(commit=False)

        self.assertEqual([s.id for s in steps], [None])