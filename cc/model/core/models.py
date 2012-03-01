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
Core Case Conductor models (Product).

"""
from django.core.exceptions import ValidationError
from django.db import models

from pkg_resources import parse_version

from ..environments.models import HasEnvironmentsModel
from ..ccmodel import CCModel, TeamModel



class Product(CCModel, TeamModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)


    def __unicode__(self):
        return self.name


    class Meta:
        permissions = [
            ("manage_products", "Can add/edit/delete products."),
            ("manage_users", "Can add/edit/delete user accounts."),
            ]
        ordering = ["name"]


    def clone(self, *args, **kwargs):
        """
        Clone Product, with team.

        """
        kwargs.setdefault("cascade", ["team"])
        overrides = kwargs.setdefault("overrides", {})
        overrides.setdefault("name", "Cloned: {0}".format(self.name))
        return super(Product, self).clone(*args, **kwargs)


    def reorder_versions(self, update_instance=None):
        """
        Reorder versions of this product, saving new order in db.

        If an ``update_instance`` is given, update it with new order and
        ``latest`` flag.

        """
        ordered = sorted(self.versions.all(), key=by_version)
        for i, version in enumerate(ordered, 1):
            version.order = i
            version.latest = (i == len(ordered))
            version.save(force_update=True, skip_reorder=True, notrack=True)
            if version == update_instance:
                update_instance.order = version.order
                update_instance.latest = version.latest
                update_instance.cc_version += 1
        # now we have to update latest caseversions too, @@@ too slow?
        for case in self.cases.all():
            case.set_latest_version()



class ProductVersion(CCModel, TeamModel, HasEnvironmentsModel):
    product = models.ForeignKey(Product, related_name="versions")
    version = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0, editable=False)
    # denormalized for querying
    latest = models.BooleanField(default=False, editable=False)


    @property
    def name(self):
        """A ProductVersion's name is its product name and version."""
        return u"%s %s" % (self.product, self.version)


    def __unicode__(self):
        """A ProductVersion's unicode representation is its name."""
        return self.name


    class Meta:
        ordering = ["product", "order"]


    def save(self, *args, **kwargs):
        """Save productversion, updating latest version."""
        skip_reorder = kwargs.pop("skip_reorder", False)
        super(ProductVersion, self).save(*args, **kwargs)
        if not skip_reorder:
            self.product.reorder_versions(update_instance=self)


    def delete(self, *args, **kwargs):
        """Delete productversion, updating latest version."""
        super(ProductVersion, self).delete(*args, **kwargs)
        self.product.reorder_versions()


    def undelete(self, *args, **kwargs):
        """Undelete productversion, updating latest version."""
        super(ProductVersion, self).undelete(*args, **kwargs)
        self.product.reorder_versions()


    def clean(self):
        """
        Validate uniqueness of product/version combo.

        Can't use actual unique constraint due to soft-deletion; if we don't
        include deleted-on in the constraint, deleted objects can cause
        integrity errors; if we include deleted-on in the constraint it
        nullifies the constraint entirely, since NULL != NULL in SQL.

        """
        try:
            dupes = ProductVersion.objects.filter(
                product=self.product, version=self.version)
        except Product.DoesNotExist:
            # product is not set or is invalid; dupes are not an issue.
            return
        if self.pk is not None:
            dupes = dupes.exclude(pk=self.pk)
        if dupes.exists():
            raise ValidationError(
                "Product version '{0}' for '{1}' already exists.".format(
                    self.version, self.product)
                )


    @property
    def parent(self):
        return self.product


    @classmethod
    def cascade_envs_to(cls, objs, adding):
        Run = cls.runs.related.model
        CaseVersion = cls.caseversions.related.model

        runs = Run.objects.filter(productversion__in=objs)
        caseversions = CaseVersion.objects.filter(productversion__in=objs)

        if adding:
            runs = runs.filter(status=Run.STATUS.draft)
            caseversions = caseversions.filter(envs_narrowed=False)

        return {Run: runs, CaseVersion: caseversions}


    def clone(self, *args, **kwargs):
        """
        Clone ProductVersion, with ".next" version and "Cloned:" codename.

        """
        overrides = kwargs.setdefault("overrides", {})
        overrides["version"] = "%s.next" % self.version
        overrides["codename"] = "Cloned: %s" % self.codename
        kwargs.setdefault("cascade", ["environments", "team"])
        return super(ProductVersion, self).clone(*args, **kwargs)



def by_version(productversion):
    """
    Given a ProductVersion, return a version tuple that will order correctly.

    Uses pkg_resources' ``parse_version`` function.

    This function is intended to be passed to the ``key`` argument of the
    ``sorted`` builtin.

    """
    return parse_version(productversion.version)
