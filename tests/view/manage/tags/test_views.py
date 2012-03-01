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
Tests for tag management views.

"""
from django.core.urlresolvers import reverse

from tests import case



class TagsTest(case.view.manage.ListViewTestCase,
               case.view.manage.CCModelListTests,
               ):
    """Test for tags manage list view."""
    form_id = "manage-tags-form"
    perm = "manage_tags"


    @property
    def factory(self):
        """The model factory for this manage list."""
        return self.F.TagFactory


    @property
    def url(self):
        """Shortcut for manage-tags url."""
        return reverse("manage_tags")


    def test_filter_by_name(self):
        """Can filter by name."""
        self.factory.create(name="Tag 1")
        self.factory.create(name="Tag 2")

        res = self.get(params={"filter-name": "1"})

        self.assertInList(res, "Tag 1")
        self.assertNotInList(res, "Tag 2")


    def test_sort_by_name(self):
        """Can sort by name."""
        self.factory.create(name="Tag 1")
        self.factory.create(name="Tag 2")

        res = self.get(params={"sortfield": "name", "sortdirection": "desc"})

        self.assertOrderInList(res, "Tag 2", "Tag 1")


    def test_filter_by_product(self):
        """Can filter by product."""
        p = self.F.ProductFactory.create()
        self.factory.create(name="Tag 1", product=p)
        self.factory.create(name="Tag 2")

        res = self.get(params={"filter-product": str(p.id)})

        self.assertInList(res, "Tag 1")
        self.assertNotInList(res, "Tag 2")


    def test_sort_by_product(self):
        """Can sort by product."""
        pb = self.F.ProductFactory.create(name="B")
        pa = self.F.ProductFactory.create(name="A")
        self.factory.create(name="Tag 1", product=pb)
        self.factory.create(name="Tag 2", product=pa)

        res = self.get(params={"sortfield": "product", "sortdirection": "asc"})

        self.assertOrderInList(res, "Tag 2", "Tag 1")



class AddTagTest(case.view.FormViewTestCase):
    """Tests for add tag view."""
    form_id = "tag-add-form"


    @property
    def url(self):
        """Shortcut for add-tag url."""
        return reverse("manage_tag_add")


    def setUp(self):
        """Add manage-tags permission to user."""
        super(AddTagTest, self).setUp()
        self.add_perm("manage_tags")


    def test_success(self):
        """Can add a tag with basic data, including a product."""
        p = self.F.ProductFactory.create()
        form = self.get_form()
        form["name"] = "Some browser"
        form["product"] = str(p.id)

        res = form.submit(status=302)

        self.assertRedirects(res, reverse("manage_tags"))

        res.follow().mustcontain("Tag 'Some browser' added.")

        t = self.model.Tag.objects.get()
        self.assertEqual(t.name, "Some browser")
        self.assertEqual(t.product, p)


    def test_error(self):
        """Bound form with errors is re-displayed."""
        res = self.get_form().submit()

        self.assertEqual(res.status_int, 200)
        res.mustcontain("This field is required.")


    def test_requires_manage_tags_permission(self):
        """Requires manage-tags permission."""
        res = self.app.get(
            self.url, user=self.F.UserFactory.create(), status=302)

        self.assertRedirects(res, reverse("auth_login") + "?next=" + self.url)



class EditTagTest(case.view.FormViewTestCase):
    """Tests for edit-tag view."""
    form_id = "tag-edit-form"


    def setUp(self):
        """Setup for tag edit tests; create a tag, add perm."""
        super(EditTagTest, self).setUp()
        self.tag = self.F.TagFactory.create()
        self.add_perm("manage_tags")


    @property
    def url(self):
        """Shortcut for edit-tag url."""
        return reverse(
            "manage_tag_edit", kwargs=dict(tag_id=self.tag.id))


    def test_requires_manage_tags_permission(self):
        """Requires manage-tags permission."""
        res = self.app.get(self.url, user=self.F.UserFactory.create(), status=302)

        self.assertRedirects(res, reverse("auth_login") + "?next=" + self.url)


    def test_save_basic(self):
        """Can save updates; redirects to manage tags list."""
        p = self.F.ProductFactory.create()
        form = self.get_form()
        form["name"] = "new name"
        form["product"] = str(p.id)
        res = form.submit(status=302)

        self.assertRedirects(res, reverse("manage_tags"))

        res.follow().mustcontain("Saved 'new name'.")

        t = self.refresh(self.tag)
        self.assertEqual(t.name, "new name")
        self.assertEqual(t.product, p)


    def test_errors(self):
        """Test bound form redisplay with errors."""
        form = self.get_form()
        form["name"] = ""
        res = form.submit(status=200)

        res.mustcontain("This field is required.")


    def test_concurrency_error(self):
        """Concurrency error is displayed."""
        form = self.get_form()

        self.tag.save()

        form["name"] = "New"
        res = form.submit(status=200)

        res.mustcontain("Another user saved changes to this object")



class TagsAutocompleteTest(case.view.AuthenticatedViewTestCase):
    """Test for tags autocomplete view."""
    @property
    def url(self):
        """Shortcut for tag-autocomplete url."""
        return reverse("manage_tags_autocomplete")


    def get(self, query=None):
        """Shortcut for getting tag-autocomplete url authenticated."""
        url = self.url
        if query is not None:
            url = url + "?text=" + query
        return self.app.get(url, user=self.user)


    def test_matching_tags_json(self):
        """Returns list of matching tags in JSON."""
        t = self.F.TagFactory.create(name="foo")

        res = self.get("o")

        self.assertEqual(
            res.json,
            {
                "suggestions": [
                    {
                        "id": t.id,
                        "name": "foo",
                        "postText": "o",
                        "preText": "f",
                        "product-id": None,
                        "type": "tag",
                        "typedText": "o",
                        }
                    ]
                }
            )


    def test_not_wrong_product_tags(self):
        """Only tags for the correct product, or global tags, are returned."""
        p1 = self.F.ProductFactory.create()
        p2 = self.F.ProductFactory.create()

        t1 = self.F.TagFactory.create(product=p1, name="t1")
        self.F.TagFactory.create(product=p2, name="t2")
        t3 = self.F.TagFactory.create(product=None, name="t3")

        res = self.app.get(
            self.url, user=self.user, params={"text": "t", "product-id": p1.id})

        self.assertEqual(
            [(t["id"], t["product-id"]) for t in res.json["suggestions"]],
            [(t1.id, p1.id), (t3.id, None)]
            )


    def test_case_insensitive(self):
        """Matching is case-insensitive, but pre/post are case-accurate."""
        t = self.F.TagFactory.create(name="FooBar")

        res = self.get("oO")

        self.assertEqual(
            res.json,
            {
                "suggestions": [
                    {
                        "id": t.id,
                        "name": "FooBar",
                        "postText": "Bar",
                        "preText": "F",
                        "product-id": None,
                        "type": "tag",
                        "typedText": "oO",
                        }
                    ]
                }
            )


    def test_no_query(self):
        """If no query is provided, no tags are returned."""
        self.F.TagFactory.create(name="foo")

        res = self.get()

        self.assertEqual(res.json, {"suggestions": []})
