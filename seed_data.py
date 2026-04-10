"""Sample tags and users for demos. Run with ALLOW_SEED=1 then visit /dev/seed, or use seed() inside app context."""
from __future__ import annotations

from models import (
    ConnectionRequest,
    ExperienceTag,
    Profile,
    SupporterExperience,
    User,
    db,
)


def seed() -> None:
    if ExperienceTag.query.count():
        print("Already seeded.")
        return

    tags = [
        ("divorce", "Divorce / separation", "Navigating end of a marriage or long-term partnership."),
        ("bereavement_spouse", "Loss of a spouse/partner", "Grief after losing a partner."),
        ("bereavement_parent", "Loss of a parent", "Grief after losing a parent."),
        ("loneliness", "Long-term loneliness", "Extended isolation or difficulty connecting."),
        ("caregiver_burnout", "Caregiver burnout", "Supporting a sick or aging family member."),
        ("job_loss", "Job loss / career crisis", "Unemployment or major career change."),
        ("immigration", "Immigration / displacement", "Moving countries, culture shock, displacement."),
        ("mental_health", "Mental health journey", "Living with anxiety, depression, or related challenges."),
    ]
    for slug, label, desc in tags:
        db.session.add(ExperienceTag(slug=slug, label=label, description=desc))

    db.session.commit()

    admin = User(email="admin@peerconnect.local", is_admin=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.flush()
    db.session.add(
        Profile(
            user_id=admin.id,
            display_name="Admin",
            bio="Platform admin — verify lived-experience claims in /admin.",
            age=30,
            gender="Other",
            city="Online",
            languages="English",
            hobbies="Community",
            open_to_social=False,
            open_to_support_others=False,
            seeking_peer_support=False,
        )
    )

    u1 = User(email="alex@demo.com")
    u1.set_password("demo123")
    db.session.add(u1)
    db.session.flush()
    db.session.add(
        Profile(
            user_id=u1.id,
            display_name="Alex",
            bio="I went through a difficult divorce two years ago. Happy to listen and share what helped me.",
            age=34,
            gender="Non-binary",
            city="Toronto",
            latitude=43.6532,
            longitude=-79.3832,
            languages="English,French",
            hobbies="Hiking,Reading,Cooking",
            seeking_help_with="",
            open_to_social=True,
            open_to_support_others=True,
            seeking_peer_support=False,
        )
    )

    u2 = User(email="sam@demo.com")
    u2.set_password("demo123")
    db.session.add(u2)
    db.session.flush()
    db.session.add(
        Profile(
            user_id=u2.id,
            display_name="Sam",
            bio="Recently widowed; looking for people who understand. Also want to make local friends.",
            age=52,
            gender="Female",
            city="Toronto",
            latitude=43.66,
            longitude=-79.39,
            languages="English",
            hobbies="Gardening,Walking",
            seeking_help_with="Grief, loneliness",
            open_to_social=True,
            open_to_support_others=False,
            seeking_peer_support=True,
        )
    )

    u3 = User(email="jordan@demo.com")
    u3.set_password("demo123")
    db.session.add(u3)
    db.session.flush()
    db.session.add(
        Profile(
            user_id=u3.id,
            display_name="Jordan",
            bio="New to the city; love board games and coffee.",
            age=26,
            gender="Male",
            city="Toronto",
            latitude=43.64,
            longitude=-79.40,
            languages="English,Spanish",
            hobbies="Board games,Coffee,Music",
            open_to_social=True,
            open_to_support_others=False,
            seeking_peer_support=False,
        )
    )

    db.session.commit()

    divorce = ExperienceTag.query.filter_by(slug="divorce").first()
    bereaved = ExperienceTag.query.filter_by(slug="bereavement_spouse").first()
    if divorce:
        s1 = SupporterExperience(user_id=u1.id, tag_id=divorce.id, is_verified=True)
        db.session.add(s1)
    if bereaved:
        s2 = SupporterExperience(user_id=u2.id, tag_id=bereaved.id, is_verified=True)
        db.session.add(s2)

    db.session.commit()
    print("Seeded experience tags, admin (admin@peerconnect.local / admin123), and demo users (password demo123).")


def seed_requests_demo() -> None:
    """Optional second step for inbox UI."""
    if ConnectionRequest.query.count():
        return
    u1 = User.query.filter_by(email="alex@demo.com").first()
    u2 = User.query.filter_by(email="sam@demo.com").first()
    if u1 and u2:
        db.session.add(
            ConnectionRequest(
                from_user_id=u2.id,
                to_user_id=u1.id,
                kind="support",
                message="Would you be open to chatting about coping after separation?",
            )
        )
        db.session.commit()
        print("Added sample connection request.")
