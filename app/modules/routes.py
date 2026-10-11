"""Modules blueprint — add/edit/delete modules.

All routes are scoped to the logged-in user: a user can only see, edit or
delete their own modules (enforced via the shared ownership check in
app.ownership).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Module
from app.ownership import get_owned_module_or_404

modules_bp = Blueprint("modules", __name__, url_prefix="/modules")


@modules_bp.route("/")
@login_required
def list_modules():
    modules = Module.query.filter_by(user_id=current_user.id).order_by(Module.created_at).all()
    return render_template("modules/list.html", modules=modules)


@modules_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_module():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Module name is required.", "error")
            return redirect(url_for("modules.new_module"))

        module = Module(user_id=current_user.id, name=name, description=description)
        db.session.add(module)
        db.session.commit()
        flash(f'Module "{name}" created.', "success")
        return redirect(url_for("modules.list_modules"))

    return render_template("modules/form.html", module=None)


@modules_bp.route("/<int:module_id>/edit", methods=["GET", "POST"])
@login_required
def edit_module(module_id):
    module = get_owned_module_or_404(module_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Module name is required.", "error")
            return redirect(url_for("modules.edit_module", module_id=module_id))

        module.name = name
        module.description = description
        db.session.commit()
        flash(f'Module "{name}" updated.', "success")
        return redirect(url_for("modules.list_modules"))

    return render_template("modules/form.html", module=module)


@modules_bp.route("/<int:module_id>/delete", methods=["POST"])
@login_required
def delete_module(module_id):
    module = get_owned_module_or_404(module_id)
    name = module.name
    db.session.delete(module)  # cascades to tasks (and their study_sessions)
    db.session.commit()
    flash(f'Module "{name}" and all its tasks were deleted.', "success")
    return redirect(url_for("modules.list_modules"))
