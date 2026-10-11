"""Shared Flask extension instances.

Kept in their own module (rather than inside app/__init__.py) so blueprint
modules can import `db`, `bcrypt`, `login_manager` without circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
