Student MVP: match people for **peer support** (lived experience topics + optional admin verification) and **social discovery** (languages, hobbies, age, gender, optional distance).

**Not** therapy, emergency care, or a production-ready safety stack. See `templates/crisis.html` for crisis lines.

Open http://127.0.0.1:5050

### Demo data

With `ALLOW_SEED=1` in `.env`, visit **http://127.0.0.1:5050/dev/seed** once.

- Admin: `admin@peerconnect.local` / `admin123` → `/admin` to verify supporter topics  
- Demo users: `alex@demo.com`, `sam@demo.com`, `jordan@demo.com` / `demo123`

## GitHub

Remote: [https://github.com/ShamirBahome/matchPeople.git](https://github.com/ShamirBahome/matchPeople.git)

```bash
cd matchPeople
git remote -v
git push -u origin main
```

## Production

Use `make gunicorn` behind HTTPS (e.g. nginx). Disable `ALLOW_SEED`, use a strong `SECRET_KEY`, and add moderation, reporting, ToS, and privacy policy before any real users.
