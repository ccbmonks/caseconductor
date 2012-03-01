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
Manage views for environments.

"""
import json

from django.http import HttpResponse, Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

from cc import model

from cc.view.filters import ProfileFilterSet, EnvironmentFilterSet
from cc.view.lists import decorators as lists
from cc.view.utils.ajax import ajax

from . import forms
from .decorators import category_element_ajax_add_edit



@login_required
@lists.actions(
    model.Profile,
    ["delete", "clone"],
    permission="environments.manage_environments")
@lists.filter("profiles", filterset_class=ProfileFilterSet)
@lists.sort("profiles")
@ajax("manage/environment/profile_list/_profiles_list.html")
def profiles_list(request):
    """List profiles."""
    return TemplateResponse(
        request,
        "manage/environment/profiles.html",
        {
            "profiles": model.Profile.objects.all(),
            }
        )



@login_required
def profile_details(request, profile_id):
    """Get details snippet for a profile."""
    profile = get_object_or_404(model.Profile, pk=profile_id)
    return TemplateResponse(
        request,
        "manage/environment/profile_list/_profile_details.html",
        {
            "profile": profile
            }
        )



@permission_required("environments.manage_environments")
@category_element_ajax_add_edit
def profile_add(request):
    """Add an environment profile."""
    if request.method == "POST":
        form = forms.AddProfileForm(request.POST, user=request.user)
        profile = form.save_if_valid()
        if profile is not None:
            messages.success(
                request, "Profile '{0}' added.".format(
                    profile.name)
                )
            return redirect("manage_profiles")
    else:
        form = forms.AddProfileForm(user=request.user)
    return TemplateResponse(
        request,
        "manage/environment/add_profile.html",
        {
            "form": form
            }
        )



@permission_required("environments.manage_environments")
@lists.filter("environments", filterset_class=EnvironmentFilterSet)
@lists.actions(
    model.Environment,
    ["remove_from_profile"],
    permission="environments.manage_environments",
    fall_through=True)
@ajax("manage/environment/edit_profile/_envs_list.html")
def profile_edit(request, profile_id):
    profile = get_object_or_404(model.Profile, pk=profile_id)

    # @@@ should use a form, and support both ajax and non
    if request.is_ajax() and request.method == "POST":
        if "save-profile-name" in request.POST:
            new_name = request.POST.get("profile-name")
            data = {}
            if not new_name:
                messages.error(request, "Please enter a profile name.")
                data["success"] = False
            else:
                profile.name = new_name
                profile.save(user=request.user)
                messages.success(request, "Profile name saved!")
                data["success"] = True

            return HttpResponse(
                json.dumps(data),
                content_type="application/json")

        elif "add-environment" in request.POST:
            element_ids = request.POST.getlist("element-element")
            if not element_ids:
                messages.error(
                    request, "Please select some environment elements.")
            else:
                env = model.Environment.objects.create(
                    profile=profile, user=request.user)
                env.elements.add(*element_ids)

    return TemplateResponse(
        request,
        "manage/environment/edit_profile.html",
        {
            "profile": profile,
            "environments": profile.environments.all(),
            }
        )



@permission_required("core.manage_products")
@lists.filter("environments", filterset_class=EnvironmentFilterSet)
@ajax("manage/environment/productversion/_envs_list.html")
def productversion_environments_edit(request, productversion_id):
    productversion = get_object_or_404(
        model.ProductVersion, pk=productversion_id)

    # @@@ should use a form, and support both ajax and non
    if request.is_ajax() and request.method == "POST":
        if "add-environment" in request.POST:
            element_ids = request.POST.getlist("element-element")
            if not element_ids:
                messages.error(
                    request, "Please select some environment elements.")
            else:
                env = model.Environment.objects.create(user=request.user)
                env.elements.add(*element_ids)
                productversion.environments.add(env)
        elif "action-remove" in request.POST:
            env_id = request.POST.get("action-remove")
            productversion.environments.remove(env_id)

    return TemplateResponse(
        request,
        "manage/environment/productversion.html",
        {
            "productversion": productversion,
            "environments": productversion.environments.all(),
            }
        )



@login_required
def element_autocomplete(request):
    text = request.GET.get("text")
    elements = []
    if text is not None:
        elements = model.Element.objects.filter(
            name__icontains=text)
    suggestions = []
    for e in elements:
        start = e.name.lower().index(text.lower())
        pre = e.name[:start]
        post = e.name[start+len(text):]
        suggestions.append({
                "preText": pre,
                "typedText": text,
                "postText": post,
                "id": e.id,
                "name": e.name,
                "type": "element",
                })
    return HttpResponse(
        json.dumps(
            {
                "suggestions": suggestions
                }
            ),
        content_type="application/json",
        )



@login_required
@ajax("manage/environment/narrow/_envs_list.html")
def narrow_environments(request, object_type, object_id):
    if object_type == "run":
        model_class = model.Run
        redirect_to = "manage_runs"
    elif object_type == "caseversion":
        model_class = model.CaseVersion
        redirect_to = "manage_cases"
    else:
        raise Http404
    obj = get_object_or_404(model_class, pk=object_id)

    current_env_ids = set(obj.environments.values_list("id", flat=True))

    if request.method == "POST":
        env_ids = set(map(int, request.POST.getlist("environments")))

        remove = current_env_ids.difference(env_ids)
        add = env_ids.difference(current_env_ids)

        obj.environments.add(*add)
        obj.environments.remove(*remove)

        messages.success(request, u"Saved environments for '{0}'".format(obj))

        return redirect(redirect_to)

    return TemplateResponse(
        request,
        "manage/environment/narrowing.html",
        {
            "environments": obj.productversion.environments.all(),
            "selected_env_ids": current_env_ids,
            "filters": EnvironmentFilterSet().bind(), # for JS filtering
            "obj": obj,
            })
