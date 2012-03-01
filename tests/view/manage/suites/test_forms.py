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
Tests for suite-management forms.

"""
from tests import case



class EditSuiteFormTest(case.DBTestCase):
    """Tests for EditSuiteForm."""
    @property
    def form(self):
        """The form class under test."""
        from cc.view.manage.suites.forms import EditSuiteForm
        return EditSuiteForm


    def test_edit_suite(self):
        """Can edit suite, including new product, sets modified-by."""
        p = self.F.ProductFactory()
        s = self.F.SuiteFactory()
        u = self.F.UserFactory()

        f = self.form(
            {
                "product": str(p.id),
                "name": "new name",
                "description": "new desc",
                "status": "draft",
                "cc_version": str(s.cc_version),
                },
            instance=s,
            user=u)

        suite = f.save()

        self.assertEqual(suite.product, p)
        self.assertEqual(suite.name, "new name")
        self.assertEqual(suite.description, "new desc")
        self.assertEqual(suite.modified_by, u)


    def test_no_change_product_option(self):
        """No option to change to different product if there are cases."""
        self.F.ProductFactory.create()
        s = self.F.SuiteFactory()
        self.F.SuiteCaseFactory(suite=s)

        f = self.form(instance=s)
        self.assertEqual(
            [c[0] for c in f.fields["product"].choices],
            ['', s.product.id]
            )
        self.assertTrue(f.fields["product"].readonly)


    def test_no_edit_product(self):
        """Can't change product if there are cases"""
        p = self.F.ProductFactory()
        s = self.F.SuiteFactory()
        self.F.SuiteCaseFactory(suite=s)

        f = self.form(
            {
                "product": str(p.id),
                "name": "new name",
                "description": "new desc",
                "status": "draft",
                "cc_version": str(s.cc_version),
                },
            instance=s,
            )

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["product"],
            [u"Select a valid choice. "
             "That choice is not one of the available choices."]
            )


    def test_add_cases(self):
        """Can add cases to a suite."""
        s = self.F.SuiteFactory()
        c = self.F.CaseFactory(product=s.product)

        f = self.form(
            {
                "product": str(s.product.id),
                "name": s.name,
                "description": s.description,
                "status": s.status,
                "cases": [str(c.id)],
                "cc_version": str(s.cc_version),
                },
            instance=s,
            )

        self.assertTrue(f.is_valid())
        suite = f.save()

        self.assertEqual(set(suite.cases.all()), set([c]))


    def test_edit_cases(self):
        """Can edit cases of a suite."""
        s = self.F.SuiteFactory.create()
        self.F.SuiteCaseFactory.create(suite=s)
        c = self.F.CaseFactory.create(product=s.product)

        f = self.form(
            {
                "product": str(s.product.id),
                "name": s.name,
                "description": s.description,
                "status": s.status,
                "cases": [str(c.id)],
                "cc_version": str(s.cc_version),
                },
            instance=s,
            )

        self.assertTrue(f.is_valid())
        suite = f.save()

        self.assertEqual(set(suite.cases.all()), set([c]))



class AddSuiteFormTest(case.DBTestCase):
    """Tests for AddSuiteForm."""
    @property
    def form(self):
        """The form class under test."""
        from cc.view.manage.suites.forms import AddSuiteForm
        return AddSuiteForm


    def test_add_suite(self):
        """Can add suite, has created-by user."""
        p = self.F.ProductFactory()
        u = self.F.UserFactory()

        f = self.form(
            {
                "product": str(p.id),
                "name": "Foo",
                "description": "foo desc",
                "status": "draft",
                "cc_version": "0",
                },
            user=u
            )

        suite = f.save()

        self.assertEqual(suite.product, p)
        self.assertEqual(suite.name, "Foo")
        self.assertEqual(suite.description, "foo desc")
        self.assertEqual(suite.created_by, u)


    def test_add_with_cases(self):
        """Can add cases to a new suite."""
        c = self.F.CaseFactory()

        f = self.form(
            {
                "product": str(c.product.id),
                "name": "some name",
                "description": "some desc",
                "status": "draft",
                "cases": [str(c.id)],
                "cc_version": "0",
                },
            )

        self.assertTrue(f.is_valid())
        suite = f.save()

        self.assertEqual(set(suite.cases.all()), set([c]))


    def test_product_id_attrs(self):
        """Product and cases options have data-product-id."""
        case = self.F.CaseFactory.create()

        f = self.form()

        self.assertEqual(
            [
                c[1].attrs["data-product-id"]
                for c in f.fields["product"].choices
                if c[0]
                ],
            [case.product.id]
            )
        self.assertEqual(
            [
                c[1].attrs["data-product-id"]
                for c in f.fields["cases"].choices
                if c[0]
                ],
            [case.product.id]
            )
