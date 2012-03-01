# Case Conductor is a Test Case Management system.
# Copyright (C) 2011-2012 Mozilla
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
Utility base TestCase classes for testing manage views.

"""
from datetime import datetime

from . import base



class ListViewTestCase(base.FormViewTestCase, base.ListViewTestCase):
    """Base class for testing manage list views."""
    # subclasses should specify these:
    perm = None          # required management permission codename


    def assertActionRequiresPermission(self, action, permission=None):
        """Assert that the given list action requires the given permission."""
        if permission is None:
            permission = self.perm

        o = self.factory.create()

        form = self.get_form()

        name = "action-{0}".format(action)

        # action button not shown to the user
        self.assertTrue(name not in form.fields)

        # ...but if they cleverly submit it anyway they get a 403...
        res = self.post(
            {
                name: str(o.id),
                "csrfmiddlewaretoken":
                    form.fields.get("csrfmiddlewaretoken")[0].value
                },
            status=403,
            )

        # ...with a message about permissions.
        res.mustcontain("permission")


    def test_delete(self):
        """Can delete objects from list."""
        self.add_perm(self.perm)

        o = self.factory.create()

        self.get_form().submit(
            name="action-delete",
            index=0,
            headers={"X-Requested-With": "XMLHttpRequest"}
            )

        self.assertTrue(bool(self.refresh(o).deleted_on))


    def test_delete_requires_permission(self):
        """Deleting requires appropriate permission."""
        self.assertActionRequiresPermission("delete")


    def test_create_link(self):
        """With proper perm, create link is there."""
        self.add_perm(self.perm)
        res = self.get()

        self.assertElement(res.html, "a", "create")


    def test_create_link_requires_perms(self):
        """Without proper perm, create link is not there."""
        res = self.get()

        self.assertElement(res.html, "a", "create", count=0)



class CCModelListTests(object):
    """Additional manage list view tests for CCModels."""
    def test_clone(self):
        """Can clone objects in list."""
        self.add_perm(self.perm)

        self.factory.create()

        res = self.get_form().submit(
            name="action-clone",
            index=0,
            headers={"X-Requested-With": "XMLHttpRequest"},
            )

        self.assertElement(
            res.json["html"], "h3", "title", count=2)


    def test_clone_requires_permission(self):
        """Cloning requires appropriate permission."""
        self.assertActionRequiresPermission("clone")


    def test_filter_by_creator(self):
        """Can filter by creator."""
        self.factory.create(name="Foo 1", user=self.user)
        self.factory.create(name="Foo 2")

        res = self.get(params={"filter-creator": self.user.id})

        self.assertInList(res, "Foo 1")
        self.assertNotInList(res, "Foo 2")


    def test_default_sort_by_last_created(self):
        """Default sort is by latest created first."""
        self.factory.create(
            name="Foo 1", created_on=datetime(2012, 1, 21))
        self.factory.create(
            name="Foo 2", created_on=datetime(2012, 1, 22))

        res = self.get()

        self.assertOrderInList(res, "Foo 2", "Foo 1")



class StatusListTests(object):
    """Extra tests for manage lists with activated/deactivate actions."""
    def test_activate(self):
        """Can activate objects in list."""
        self.add_perm(self.perm)

        s = self.factory.create(status="draft")

        self.get_form().submit(
            name="action-activate",
            index=0,
            headers={"X-Requested-With": "XMLHttpRequest"},
            )

        self.assertEqual(self.refresh(s).status, "active")


    def test_activate_requires_permission(self):
        """Activating requires appropriate permission."""
        self.assertActionRequiresPermission("activate", self.perm)


    def test_deactivate(self):
        """Can deactivate objects in list."""
        self.add_perm(self.perm)

        s = self.factory.create(status="active")

        self.get_form().submit(
            name="action-deactivate",
            index=0,
            headers={"X-Requested-With": "XMLHttpRequest"},
            )

        self.assertEqual(self.refresh(s).status, "disabled")


    def test_deactivate_requires_permission(self):
        """Deactivating requires appropriate permission."""
        self.assertActionRequiresPermission("deactivate", self.perm)
