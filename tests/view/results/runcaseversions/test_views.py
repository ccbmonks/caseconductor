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
Tests for runcaseversion results view.

"""
from django.core.urlresolvers import reverse

from tests import case



class RunCaseVersionResultsViewTest(case.view.ListViewTestCase,
                                    case.view.ListFinderTests,
                                    ):
    """Tests for runcaseversion results view."""
    name_attr = "caseversion__name"


    @property
    def factory(self):
        """The RunCaseVersion factory."""
        return self.F.RunCaseVersionFactory


    @property
    def url(self):
        """Shortcut for runcaseversion results url."""
        return reverse("results_runcaseversions")


    def test_filter_by_status(self):
        """Can filter by status."""
        self.F.RunCaseVersionFactory.create(
            caseversion__status="draft", caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(
            caseversion__status="active", caseversion__name="Case 2")

        res = self.get(params={"filter-status": "draft"})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_id(self):
        """Can filter by id."""
        rcv1 = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")

        res = self.get(params={"filter-id": rcv1.caseversion.case.id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_bad_id(self):
        """Attempt to filter by non-integer id is ignored."""
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")

        res = self.get(params={"filter-id": "foo"})

        self.assertInList(res, "Case 1")


    def test_filter_by_name(self):
        """Can filter by name."""
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")

        res = self.get(params={"filter-name": "1"})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_tag(self):
        """Can filter by tag."""
        t = self.F.TagFactory.create()
        rcv = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        rcv.caseversion.tags.add(t)
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")

        res = self.get(params={"filter-tag": t.id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_product(self):
        """Can filter by product."""
        rcv = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")

        res = self.get(
            params={"filter-product": rcv.caseversion.case.product.id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_productversion(self):
        """Can filter by product version; no implicit filter by latest."""
        rcv = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        other_pv = self.F.ProductVersionFactory(
            product=rcv.caseversion.productversion.product, version="2.0")
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 2",
            caseversion__case=rcv.caseversion.case,
            caseversion__productversion=other_pv,
            run__productversion=other_pv)

        res = self.get(
            params={"filter-productversion": rcv.caseversion.productversion.id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_step_instruction(self):
        """Can filter by step instruction."""
        rcv1 = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        rcv2 = self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")
        self.F.CaseStepFactory.create(
            caseversion=rcv1.caseversion, instruction="do this")
        self.F.CaseStepFactory.create(
            caseversion=rcv2.caseversion, instruction="do that")

        res = self.get(params={"filter-instruction": "this"})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_step_expected_result(self):
        """Can filter by step expected result."""
        rcv1 = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        rcv2 = self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")
        self.F.CaseStepFactory.create(
            caseversion=rcv1.caseversion, expected="see this")
        self.F.CaseStepFactory.create(
            caseversion=rcv2.caseversion, expected="see that")

        res = self.get(params={"filter-expected": "this"})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_env_elements(self):
        """Can filter by environment elements."""
        envs = self.F.EnvironmentFactory.create_full_set(
            {"OS": ["Linux", "Windows"]})
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 1", environments=envs)
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 2", environments=envs[1:])

        res = self.get(
            params={"filter-envelement": envs[0].elements.all()[0].id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_filter_by_suite(self):
        """Can filter by suite."""
        rcv = self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")
        sc = self.F.SuiteCaseFactory.create(case=rcv.caseversion.case)

        res = self.get(params={"filter-suite": sc.suite.id})

        self.assertInList(res, "Case 1")
        self.assertNotInList(res, "Case 2")


    def test_sort_by_status(self):
        """Can sort by status."""
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 1", caseversion__status="draft")
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 2", caseversion__status="active")

        res = self.get(
            params={"sortfield": "caseversion__status", "sortdirection": "asc"})

        self.assertOrderInList(res, "Case 2", "Case 1")


    def test_sort_by_name(self):
        """Can sort by name."""
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 1")
        self.F.RunCaseVersionFactory.create(caseversion__name="Case 2")

        res = self.get(
            params={"sortfield": "caseversion__name", "sortdirection": "desc"}
            )

        self.assertOrderInList(res, "Case 2", "Case 1")


    def test_sort_by_run(self):
        """Can sort by run."""
        pv2 = self.F.ProductVersionFactory.create(version="2.0")
        pv1 = self.F.ProductVersionFactory.create(
            version="1.0", product=pv2.product)
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 2",
            caseversion__productversion=pv1,
            run__productversion=pv1,
            )
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 1",
            caseversion__productversion=pv2,
            run__productversion=pv2,
            )

        res = self.get(params={"sortfield": "run", "sortdirection": "asc"})

        self.assertOrderInList(res, "Case 2", "Case 1")


    def test_sort_by_productversion(self):
        """Can sort by product version."""
        pv2 = self.F.ProductVersionFactory.create(version="2.0")
        pv1 = self.F.ProductVersionFactory.create(
            version="1.0", product=pv2.product)
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 2",
            caseversion__productversion=pv1,
            run__productversion=pv1,
            )
        self.F.RunCaseVersionFactory.create(
            caseversion__name="Case 1",
            caseversion__productversion=pv2,
            run__productversion=pv2,
            )

        res = self.get(
            params={
                "sortfield": "run__productversion",
                "sortdirection": "desc",
                },
            )

        self.assertOrderInList(res, "Case 1", "Case 2")



class RunCaseVersionDetailTest(case.view.AuthenticatedViewTestCase):
    """Test for runcaseversion-detail ajax view."""
    def setUp(self):
        """Setup for runcaseversion details tests; create a runcaseversion."""
        super(RunCaseVersionDetailTest, self).setUp()
        self.rcv = self.F.RunCaseVersionFactory.create()


    @property
    def url(self):
        """Shortcut for runcaseversion detail url."""
        return reverse(
            "results_runcaseversion_details",
            kwargs=dict(rcv_id=self.rcv.id)
            )


    def test_details_steps(self):
        """Details lists case steps."""
        self.F.CaseStepFactory.create(
            instruction="fooinstr", caseversion=self.rcv.caseversion)

        res = self.get(headers={"X-Requested-With": "XMLHttpRequest"})

        res.mustcontain("fooinstr")


    def test_details_envs(self):
        """Details lists envs."""
        self.rcv.environments.add(
            *self.F.EnvironmentFactory.create_full_set({"OS": ["Windows"]}))

        res = self.get(headers={"X-Requested-With": "XMLHttpRequest"})

        res.mustcontain("Windows")


    def test_details_team(self):
        """Details lists testers with assigned/executed results."""
        u = self.F.UserFactory.create(username="somebody")
        self.F.ResultFactory.create(tester=u, runcaseversion=self.rcv)

        res = self.get(headers={"X-Requested-With": "XMLHttpRequest"})

        res.mustcontain("somebody")


    def test_details_drilldown(self):
        """Details contains link to drilldown to results for single case."""
        res = self.get(headers={"X-Requested-With": "XMLHttpRequest"})

        res.mustcontain(
            reverse("results_results", kwargs={"rcv_id": self.rcv.id})
            )
