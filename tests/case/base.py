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
Utility base TestCase classes for Case Conductor.

"""
from django.test import TestCase



class DBMixin(object):
    """Mixin for Case Conductor test case classes that need the database."""
    @property
    def model(self):
        """The data model."""
        from cc import model
        return model


    @property
    def F(self):
        """The model factories."""
        from tests import factories
        return factories


    def refresh(self, obj):
        """
        Return the given object as it currently exists in the database.

        """
        return obj.__class__._base_manager.get(pk=obj.pk)




class DBTestCase(DBMixin, TestCase):
    """Base test case class for Case Conductor tests that need the database."""
    pass
