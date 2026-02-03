# 📰 RSS Feed App

Modern RSS aggregator with AI-powered summaries, built with FastAPI and PostgreSQL.

## 🚀 Features

### Core Features
- ✅ **Multi-user support** with authentication (JWT)
- ✅ **Feed management** with custom refresh intervals
- ✅ **Auto-delete** old articles after configurable days
- ✅ **Content extraction** with multiple fetching methods (Jina, Cloudscraper, Playwright)
- ✅ **Image extraction** (article images, site logos, favicons)
- ✅ **Tag extraction** from HTML and RSS
- ✅ **AI-powered summaries** (OpenAI, Claude, provider-agnostic)
- ✅ **Admin panel** for system configuration
- ✅ **Scheduled jobs** for automatic feed refresh and cleanup

### Technical Stack
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: HTMX + Alpine.js (server-side HTML)
- **Auth**: JWT with bcrypt
- **Scheduling**: APScheduler
- **Deployment**: Docker + Nginx + Uvicorn

---

## 📋 Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (for deployment)

---

## 🛠️ Quick Start (Development)

### 1. Clone and setup

```bash
git clone <repo>
cd rss_feed_app
cp .env.example .env
```

### 2. Configure `.env`

```bash
# Edit .env with your settings
nano .env

# Key settings:
DATABASE_URL=postgresql://rss_user:rss_password@localhost:5432/rss_feed_db
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### 3. Install dependencies

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Setup database

```bash
# Create PostgreSQL database
createdb rss_feed_db

# Run setup (creates tables + admin user)
python setup.py
```

**Default admin credentials:**
- Username: `admin`
- Password: `admin123`
- **⚠️ CHANGE IN PRODUCTION!**

### 5. Run application

```bash
python main.py
```

Visit: http://localhost:8000

---

## 🐳 Docker Deployment (Production)

### 1. Build and run with Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Edit .env for production
nano .env

# Build and start services
docker-compose up -d
```

### 2. Run initial setup

```bash
# Inside the app container
docker exec -it rss_feed_app python setup.py
```

### 3. Access application

- **App**: http://localhost:8000
- **Nginx**: http://localhost (port 80)

---

## 🗄️ Database Migrations

Using Alembic for schema changes:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

---

## 📁 Project Structure

```
rss_feed_app/
├── alembic/               # Database migrations
│   ├── versions/
│   └── env.py
├── api/
│   ├── routes/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── feeds.py       # Feed management (TODO)
│   │   └── articles.py    # Article management (TODO)
│   └── core/              # Core logic
│       ├── fetchers/      # Content fetching
│       ├── extractors.py  # Content extraction
│       └── processor.py   # Entry processing
├── auth/                  # Authentication utilities
│   ├── utils.py           # JWT + password hashing
│   └── dependencies.py    # FastAPI dependencies
├── database/              # SQLAlchemy models
│   ├── models.py          # User, Feed, Article, etc.
│   └── session.py         # DB session management
├── web/                   # Frontend (HTMX + Alpine.js)
│   ├── templates/
│   └── router.py
├── static/                # CSS, JS
├── config.py              # Configuration
├── schemas.py             # Pydantic schemas
├── main.py                # Application entry point
├── setup.py               # Initial setup script
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker orchestration
└── README.md
```

---

## 🔐 Security

### Production Checklist

- [ ] Change `SECRET_KEY` in `.env` (use `openssl rand -hex 32`)
- [ ] Change default admin password
- [ ] Use HTTPS (configure Nginx SSL)
- [ ] Enable rate limiting in Nginx
- [ ] Set strong database password
- [ ] Restrict database access to localhost/VPN
- [ ] Enable firewall (ufw/iptables)
- [ ] Regular backups of PostgreSQL
- [ ] Keep dependencies updated

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available options.

**Key settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `SECRET_KEY` | (required) | JWT signing key |
| `MAX_WORKERS` | 20 | Parallel workers for fetching |
| `USE_JINA` | true | Enable Jina.ai fetcher |
| `USE_PLAYWRIGHT` | true | Enable Playwright (heavy) |

### Admin Panel

Access at `/admin` (requires admin role)

Configure:
- Global fetcher settings
- Worker limits
- Scheduler intervals
- Enabled features

---

## 📊 API Documentation

### Authentication

**Register:**
```bash
POST /api/auth/register
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123"
}
```

**Login:**
```bash
POST /api/auth/login
{
  "username": "user",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Get current user:**
```bash
GET /api/auth/me
Authorization: Bearer <token>
```

### Feeds (TODO)

```bash
GET    /api/feeds              # List user's feeds
POST   /api/feeds              # Add new feed
GET    /api/feeds/{id}         # Get feed details
PUT    /api/feeds/{id}         # Update feed
DELETE /api/feeds/{id}         # Delete feed
POST   /api/feeds/{id}/refresh # Trigger manual refresh
```

### Articles (TODO)

```bash
GET    /api/articles                    # List articles
GET    /api/articles/{id}               # Get article
PUT    /api/articles/{id}               # Update (mark read/starred)
POST   /api/articles/{id}/summarize     # Generate AI summary
```

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

---

## 📈 Performance

### Database Optimization

- Indexes on frequently queried columns
- Connection pooling (20 base + 40 overflow)
- Pagination for large result sets

### Fetching Optimization

- Parallel workers (default: 20)
- Cascade fallback (Jina → Cloudscraper → Playwright)
- Rate limiting per fetcher

### Expected Performance

- **Users**: 100-200 concurrent
- **Articles**: Up to 400k total
- **Fetch speed**: ~10-20 articles/second (depends on sites)

---

## 🐛 Troubleshooting

### Database connection errors

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

### Playwright issues

```bash
# Install browsers
python -m playwright install chromium

# Test Playwright
python -m playwright install --help
```

### Migration errors

```bash
# Reset migrations (DESTRUCTIVE!)
alembic downgrade base
alembic upgrade head
```

---

## 📝 TODO / Roadmap

### Phase 1: Foundations ✅
- [x] Database models
- [x] Authentication (JWT)
- [x] Docker setup
- [ ] Initial migration

### Phase 2: Feed Management
- [ ] CRUD endpoints for feeds
- [ ] Manual refresh endpoint
- [ ] Feed validation

### Phase 3: Scheduler
- [ ] APScheduler setup
- [ ] Auto-refresh jobs
- [ ] Auto-delete jobs
- [ ] Job logging

### Phase 4: Frontend (HTMX)
- [ ] User dashboard
- [ ] Feed management UI
- [ ] Article reader
- [ ] Admin panel UI

### Phase 5: AI Integration
- [ ] OpenAI provider
- [ ] Claude provider
- [ ] Summary generation
- [ ] Summary caching

### Phase 6: Polish
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation
- [ ] Performance tuning

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

---

## 📄 License

MIT License - see LICENSE file

---

## 👤 Author

Built with ❤️ by Kalibrado

---

## 🙏 Acknowledgments

- FastAPI team
- SQLAlchemy team
- HTMX & Alpine.js communities
- Jina.ai for their reader API