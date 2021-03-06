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
Utility functions for deployment-related path-munging.

"""
import os, sys, site


def add_vendor_lib():
    """
    Adds the vendor library to the front of sys.path.

    """
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    vendor_lib = os.path.join(
        base_dir, "requirements", "vendor", "lib", "python")

    orig_sys_path = set(sys.path)

    # Add vendor-lib directory to sys.path (using site.addsitedir so pth
    # files are processed)
    site.addsitedir(vendor_lib)

    # Give vendor lib precedence over global Python environment
    new_sys_path = []
    for item in list(sys.path):
        if item not in orig_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path
