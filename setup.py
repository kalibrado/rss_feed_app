#!/usr/bin/env python3
"""
Setup script for RSS Feed App
Creates database tables and admin user
"""

import logging
import sys
from sqlalchemy.exc import IntegrityError

from database import init_db, get_db_context
from database.models import User, SystemConfig
from auth import hash_password
from config import Config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_admin_user(username: str = "admin", email: str = "admin@rssapp.local", password: str = "admin123"):
    """Create initial admin user"""
    
    with get_db_context() as db:
        # Check if admin exists
        existing = db.query(User).filter(User.username == username).first()
        
        if existing:
            logger.warning(f"Admin user '{username}' already exists")
            return existing
        
        # Create admin
        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
            is_active=True,
            preferences={}
        )
        
        db.add(admin)
        
        try:
            db.commit()
            db.refresh(admin)
            logger.info(f"✓ Admin user created: {username}")
            logger.info(f"   Email: {email}")
            logger.info(f"   Password: {password}")
            logger.warning("⚠️  CHANGE DEFAULT PASSWORD IN PRODUCTION!")
            return admin
        
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to create admin: {e}")
            return None


def create_default_config():
    """Create default system configuration"""
    
    with get_db_context() as db:
        default_configs = [
            {
                "key": "fetcher_global",
                "value": {
                    "max_workers": Config.MAX_WORKERS,
                    "timeout": Config.REQUEST_TIMEOUT,
                    "enabled_methods": ["jina", "cloudscraper", "playwright"]
                },
                "description": "Global fetcher configuration"
            },
            {
                "key": "scheduler",
                "value": {
                    "refresh_enabled": True,
                    "auto_delete_enabled": True,
                    "check_interval_minutes": 5
                },
                "description": "Scheduler settings"
            },
            {
                "key": "ai_providers",
                "value": {
                    "openai": {
                        "enabled": True,
                        "models": ["gpt-4", "gpt-3.5-turbo"]
                    },
                    "claude": {
                        "enabled": True,
                        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
                    }
                },
                "description": "Available AI providers and models"
            }
        ]
        
        for conf_data in default_configs:
            existing = db.query(SystemConfig).filter(SystemConfig.key == conf_data["key"]).first()
            
            if existing:
                logger.info(f"Config '{conf_data['key']}' already exists")
                continue
            
            config = SystemConfig(**conf_data)
            db.add(config)
        
        try:
            db.commit()
            logger.info("✓ Default system configuration created")
        except IntegrityError:
            db.rollback()
            logger.warning("Some configs already exist")


def main():
    """Main setup function"""
    
    logger.info("=" * 80)
    logger.info("RSS FEED APP - SETUP")
    logger.info("=" * 80)
    
    # Step 1: Create tables
    logger.info("Step 1: Creating database tables...")
    try:
        init_db()
        logger.info("✓ Database tables created")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        sys.exit(1)
    
    # Step 2: Create admin user
    logger.info("\nStep 2: Creating admin user...")
    create_admin_user()
    
    # Step 3: Create default config
    logger.info("\nStep 3: Creating default configuration...")
    create_default_config()
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ Setup completed successfully!")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("  1. Change admin password in production")
    logger.info("  2. Configure .env file")
    logger.info("  3. Run: python main.py")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()