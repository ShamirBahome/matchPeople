from __future__ import annotations

from functools import wraps

import os

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from config import Config
from models import (
    ConnectionRequest,
    ExperienceTag,
    Profile,
    SupporterExperience,
    User,
    db,
    bcrypt,
)
from utils_geo import haversine_km, language_overlap


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()

    def login_required(f):
        @wraps(f)
        def w(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in first.", "warning")
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return w

    def admin_required(f):
        @wraps(f)
        def w(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in.", "warning")
                return redirect(url_for("login"))
            u = db.session.get(User, session["user_id"])
            if not u or not (u.is_admin or u.email.lower() == app.config["ADMIN_EMAIL"]):
                flash("Admins only.", "error")
                return redirect(url_for("home"))
            return f(*args, **kwargs)

        return w

    @app.context_processor
    def ctx():
        u = None
        if "user_id" in session:
            u = db.session.get(User, session["user_id"])
        return {"current_user": u}

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/crisis")
    def crisis():
        return render_template("crisis.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            display_name = request.form.get("display_name", "").strip()
            if not email or not password or not display_name:
                flash("Email, password, and display name are required.", "error")
                return render_template("register.html")
            if User.query.filter_by(email=email).first():
                flash("That email is already registered.", "error")
                return render_template("register.html")
            u = User(email=email)
            u.set_password(password)
            db.session.add(u)
            db.session.flush()
            p = Profile(
                user_id=u.id,
                display_name=display_name,
                open_to_social=request.form.get("open_to_social") == "on",
                open_to_support_others=request.form.get("open_to_support_others") == "on",
                seeking_peer_support=request.form.get("seeking_peer_support") == "on",
            )
            db.session.add(p)
            db.session.commit()
            session["user_id"] = u.id
            flash("Welcome! Complete your profile to get better matches.", "success")
            return redirect(url_for("profile_edit"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            u = User.query.filter_by(email=email).first()
            if u and u.check_password(password):
                session["user_id"] = u.id
                flash("Signed in.", "success")
                return redirect(url_for("home"))
            flash("Invalid email or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("Signed out.", "info")
        return redirect(url_for("home"))

    @app.route("/profile")
    @login_required
    def profile():
        u = db.session.get(User, session["user_id"])
        p = u.profile if u else None
        if not p:
            return redirect(url_for("profile_edit"))
        tags = SupporterExperience.query.filter_by(user_id=u.id).all()
        return render_template("profile_view.html", profile=p, supporter_tags=tags)

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def profile_edit():
        u = db.session.get(User, session["user_id"])
        if not u.profile:
            u.profile = Profile(user_id=u.id, display_name=u.email.split("@")[0])
            db.session.add(u.profile)
            db.session.commit()
        p = u.profile
        tags = ExperienceTag.query.order_by(ExperienceTag.label).all()
        if request.method == "POST":
            p.display_name = request.form.get("display_name", p.display_name).strip() or p.display_name
            p.bio = request.form.get("bio", "")
            age_s = request.form.get("age", "").strip()
            p.age = int(age_s) if age_s.isdigit() else None
            p.gender = request.form.get("gender", "").strip() or None
            p.city = request.form.get("city", "").strip()
            lat_s, lng_s = request.form.get("latitude", "").strip(), request.form.get("longitude", "").strip()
            try:
                p.latitude = float(lat_s) if lat_s else None
                p.longitude = float(lng_s) if lng_s else None
            except ValueError:
                flash("Latitude/longitude must be numbers (optional).", "error")
                return render_template("profile_edit.html", profile=p, tags=tags, selected_slugs=[])
            p.languages = request.form.get("languages", "English").strip()
            p.hobbies = request.form.get("hobbies", "").strip()
            p.seeking_help_with = request.form.get("seeking_help_with", "").strip()
            p.open_to_social = request.form.get("open_to_social") == "on"
            p.open_to_support_others = request.form.get("open_to_support_others") == "on"
            p.seeking_peer_support = request.form.get("seeking_peer_support") == "on"

            SupporterExperience.query.filter_by(user_id=u.id).delete()
            for t in tags:
                if request.form.get(f"exp_{t.slug}") == "on":
                    db.session.add(
                        SupporterExperience(user_id=u.id, tag_id=t.id, is_verified=False)
                    )
            db.session.commit()
            flash("Profile saved.", "success")
            return redirect(url_for("profile"))

        selected = {x.tag.slug for x in SupporterExperience.query.filter_by(user_id=u.id)}
        return render_template("profile_edit.html", profile=p, tags=tags, selected_slugs=selected)

    @app.route("/discover/support")
    @login_required
    def discover_support():
        tag_id = request.args.get("tag_id", type=int)
        me = db.session.get(User, session["user_id"])
        q = (
            User.query.join(Profile)
            .join(SupporterExperience)
            .filter(User.id != me.id)
            .filter(Profile.open_to_support_others.is_(True))
        )
        if tag_id:
            q = q.filter(SupporterExperience.tag_id == tag_id)
        rows = q.distinct().all()
        scored = []
        for u in rows:
            sups = SupporterExperience.query.filter_by(user_id=u.id).all()
            verified = any(s.is_verified for s in sups)
            scored.append((verified, u))
        scored.sort(key=lambda x: (not x[0], x[1].profile.display_name.lower()))
        users = [x[1] for x in scored]
        all_tags = ExperienceTag.query.order_by(ExperienceTag.label).all()
        return render_template(
            "discover_support.html",
            users=users,
            all_tags=all_tags,
            tag_id=tag_id,
        )

    @app.route("/discover/social")
    @login_required
    def discover_social():
        me = db.session.get(User, session["user_id"])
        mp = me.profile
        gender_f = request.args.get("gender", "").strip()
        lang_f = request.args.get("language", "").strip()
        min_age = request.args.get("min_age", type=int)
        max_age = request.args.get("max_age", type=int)
        max_km = request.args.get("max_km", type=float)

        q = User.query.join(Profile).filter(User.id != me.id).filter(Profile.open_to_social.is_(True))
        if gender_f:
            q = q.filter(Profile.gender == gender_f)
        if min_age is not None:
            q = q.filter(Profile.age.isnot(None), Profile.age >= min_age)
        if max_age is not None:
            q = q.filter(Profile.age.isnot(None), Profile.age <= max_age)
        if lang_f:
            q = q.filter(Profile.languages.ilike(f"%{lang_f}%"))

        candidates = q.all()
        results = []
        for u in candidates:
            p = u.profile
            if not p:
                continue
            overlap = language_overlap(mp.languages_list(), p.languages_list())
            if lang_f and lang_f.lower() not in {x.lower() for x in p.languages_list()}:
                continue
            dist = None
            if (
                max_km is not None
                and mp.latitude is not None
                and mp.longitude is not None
                and p.latitude is not None
                and p.longitude is not None
            ):
                dist = haversine_km(mp.longitude, mp.latitude, p.longitude, p.latitude)
                if dist > max_km:
                    continue
            hobby_overlap = sorted(
                set(h.lower() for h in mp.hobbies_list())
                & set(h.lower() for h in p.hobbies_list())
            )
            score = len(hobby_overlap) * 2 + len(overlap)
            results.append((score, dist, u, overlap, hobby_overlap))

        results.sort(key=lambda x: (-x[0], x[1] if x[1] is not None else 1e9))
        return render_template(
            "discover_social.html",
            rows=results,
            gender_f=gender_f,
            lang_f=lang_f,
            min_age=min_age,
            max_age=max_age,
            max_km=max_km,
        )

    @app.route("/user/<int:user_id>")
    @login_required
    def user_public(user_id: int):
        u = db.session.get(User, user_id)
        if not u or not u.profile:
            flash("User not found.", "error")
            return redirect(url_for("home"))
        sups = SupporterExperience.query.filter_by(user_id=u.id).join(ExperienceTag).all()
        return render_template("user_public.html", user=u, profile=u.profile, supporter_tags=sups)

    @app.route("/connect", methods=["POST"])
    @login_required
    def connect():
        to_id = request.form.get("to_user_id", type=int)
        kind = request.form.get("kind", "social")
        message = request.form.get("message", "").strip()
        me_id = session["user_id"]
        if not to_id or to_id == me_id:
            flash("Invalid request.", "error")
            return redirect(url_for("home"))
        if kind not in ("social", "support"):
            kind = "social"
        exists = ConnectionRequest.query.filter(
            ConnectionRequest.from_user_id == me_id,
            ConnectionRequest.to_user_id == to_id,
            ConnectionRequest.status == "pending",
        ).first()
        if exists:
            flash("You already have a pending request with this person.", "warning")
            return redirect(url_for("user_public", user_id=to_id))
        db.session.add(
            ConnectionRequest(
                from_user_id=me_id,
                to_user_id=to_id,
                kind=kind,
                message=message,
            )
        )
        db.session.commit()
        flash("Connection request sent.", "success")
        return redirect(url_for("inbox"))

    @app.route("/inbox")
    @login_required
    def inbox():
        me = session["user_id"]
        incoming = (
            ConnectionRequest.query.filter_by(to_user_id=me)
            .order_by(ConnectionRequest.created_at.desc())
            .all()
        )
        outgoing = (
            ConnectionRequest.query.filter_by(from_user_id=me)
            .order_by(ConnectionRequest.created_at.desc())
            .all()
        )
        return render_template("inbox.html", incoming=incoming, outgoing=outgoing)

    @app.route("/inbox/action/<int:req_id>", methods=["POST"])
    @login_required
    def inbox_action(req_id: int):
        r = db.session.get(ConnectionRequest, req_id)
        if not r or r.to_user_id != session["user_id"]:
            flash("Not found.", "error")
            return redirect(url_for("inbox"))
        action = request.form.get("action")
        if action == "accept":
            r.status = "accepted"
        elif action == "decline":
            r.status = "declined"
        db.session.commit()
        flash("Updated.", "success")
        return redirect(url_for("inbox"))

    @app.route("/admin")
    @admin_required
    def admin_home():
        pending = (
            SupporterExperience.query.filter_by(is_verified=False)
            .join(User)
            .join(ExperienceTag)
            .order_by(SupporterExperience.id)
            .all()
        )
        return render_template("admin.html", pending=pending)

    @app.route("/admin/verify/<int:sid>", methods=["POST"])
    @admin_required
    def admin_verify(sid: int):
        s = db.session.get(SupporterExperience, sid)
        if s:
            s.is_verified = True
            db.session.commit()
            flash("Experience marked verified.", "success")
        return redirect(url_for("admin_home"))

    @app.route("/dev/seed")
    def dev_seed():
        if os.getenv("ALLOW_SEED", "") != "1":
            abort(404)
        from seed_data import seed

        seed()
        flash("Demo data loaded.", "success")
        return redirect(url_for("home"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5050)
