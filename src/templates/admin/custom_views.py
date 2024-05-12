from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask import redirect, url_for, session, flash
from flask_login import current_user


class customFileAdmin(FileAdmin):
    can_delete_dirs = False
    can_mkdir = False

    @expose()
    def index(self):
        if current_user.is_authenticated and current_user.is_admin:
            return super(customFileAdmin, self).index_view()
        else:
            return redirect(url_for("auth_bp.login"))


class customModelView(ModelView):
    form_excluded_columns = [
        "password",
    ]
    column_exclude_list = [
        "password",
    ]

    @expose()
    def index(self):
        if current_user.is_authenticated and current_user.is_admin:
            return super(customModelView, self).index_view()
        else:
            return redirect(url_for("auth_bp.login"))


class MyAdminIndexView(AdminIndexView):
    @expose()
    def index(self):
        if current_user.is_authenticated and current_user.is_admin:
            return super(MyAdminIndexView, self).index()
        else:
            return redirect(url_for("auth_bp.login"))
