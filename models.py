from __future__ import annotations

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()


class ExperienceTag(db.Model):
    __tablename__ = "experience_tags"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    label = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))

    supporters = db.relationship("SupporterExperience", back_populates="tag", lazy=True)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", back_populates="user", uselist=False)
    supporter_tags = db.relationship("SupporterExperience", back_populates="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, default="")
    age = db.Column(db.Integer)
    gender = db.Column(db.String(40))
    city = db.Column(db.String(120), default="")
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    languages = db.Column(db.String(500), default="English")
    hobbies = db.Column(db.String(500), default="")
    seeking_help_with = db.Column(db.Text, default="")
    open_to_social = db.Column(db.Boolean, default=True)
    open_to_support_others = db.Column(db.Boolean, default=False)
    seeking_peer_support = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    def languages_list(self) -> list[str]:
        if not self.languages:
            return []
        return [x.strip() for x in self.languages.split(",") if x.strip()]

    def hobbies_list(self) -> list[str]:
        if not self.hobbies:
            return []
        return [x.strip() for x in self.hobbies.split(",") if x.strip()]


class SupporterExperience(db.Model):
    __tablename__ = "supporter_experiences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey("experience_tags.id"), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(500))

    user = db.relationship("User", back_populates="supporter_tags")
    tag = db.relationship("ExperienceTag", back_populates="supporters")

    __table_args__ = (db.UniqueConstraint("user_id", "tag_id", name="uq_user_tag"),)


class ConnectionRequest(db.Model):
    __tablename__ = "connection_requests"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])
