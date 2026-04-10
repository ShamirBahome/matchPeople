# KinLink (peer_connect)

Hackathon / student MVP: match people for **peer support** (lived experience topics + optional admin verification) and **social discovery** (languages, hobbies, age, gender, optional distance).

**Not** therapy, emergency care, or a production-ready safety stack. See `templates/crisis.html` for crisis lines.

## Quick start

```bash
cd peer_connect
cp .env.example .env
make install
make run
```

Open http://127.0.0.1:5050

### Demo data

With `ALLOW_SEED=1` in `.env`, visit **http://127.0.0.1:5050/dev/seed** once.

- Admin: `admin@peerconnect.local` / `admin123` → `/admin` to verify supporter topics  
- Demo users: `alex@demo.com`, `sam@demo.com`, `jordan@demo.com` / `demo123`

## GitHub

Create an empty repo, then:

```bash
cd peer_connect
git init
git add .
git commit -m "Initial KinLink MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

## Production

Use `make gunicorn` behind HTTPS (e.g. nginx). Disable `ALLOW_SEED`, use a strong `SECRET_KEY`, and add moderation, reporting, ToS, and privacy policy before any real users.
