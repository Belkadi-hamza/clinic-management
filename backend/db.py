import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cabinet_management")
DB_USER = os.getenv("DB_USER", "cabinet_management")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cabinet_management")

try:
    # Try PostgreSQL first using psycopg v3
    import psycopg  # type: ignore
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine_config = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "echo": True,  # Set to True to see SQL queries
    }

    engine = create_engine(DATABASE_URL, **engine_config)
    logger.info("✅ Database engine configured with PostgreSQL (psycopg v3)")

except ImportError:
    logger.warning("PostgreSQL dependencies not available. Using SQLite for development.")
    
    # Fallback to SQLite
    DATABASE_URL = "sqlite:///./cabinet_management.db"
    engine_config = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
        "echo": True,  # Set to True to see SQL queries
    }
    
    engine = create_engine(DATABASE_URL, **engine_config)
    logger.info("✅ Database engine configured with SQLite")

except Exception as e:
    logger.error(f"Error configuring database: {e}")
    raise

# Create sessionmaker
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Create Base for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Dependency function that yields a database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Function to create all tables
def create_tables():
    """
    Create all tables in the database.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Function to check database connection - FIXED VERSION
def check_db_connection():
    """
    Check if database connection is working.
    Returns True if successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            # Use text() to create a proper SQL expression
            result = conn.execute(text("SELECT 1"))
            data = result.scalar()
            if data == 1:
                logger.info("✅ Database connection check: SUCCESS")
                return True
            else:
                logger.error("❌ Database connection check: UNEXPECTED RESULT")
                return False
    except Exception as e:
        logger.error(f"❌ Database connection check: FAILED - {e}")
        return False

# Function to get database info
def get_db_info():
    """
    Get database connection information.
    """
    return {
        "database_url": str(engine.url),
        "database_type": "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite",
        "host": DB_HOST,
        "port": DB_PORT,
        "database": DB_NAME,
        "user": DB_USER,
    }

# Function to get database health - FIXED VERSION
def get_database_health():
    """
    Get database health information for monitoring.
    """
    try:
        with engine.connect() as conn:
            if "sqlite" in str(engine.url):
                # SQLite health check
                result = conn.execute(text("SELECT sqlite_version()"))
                db_version = f"SQLite {result.scalar()}"
                
                # Get database file info
                import os
                db_file = "./cabinet_management.db"
                db_size = "N/A"
                if os.path.exists(db_file):
                    db_size = f"{os.path.getsize(db_file)} bytes"
                
                return {
                    "status": "healthy",
                    "database_version": db_version,
                    "database_name": "cabinet_management.db",
                    "database_type": "SQLite",
                    "database_size": db_size,
                    "connection_count": 1,  # SQLite doesn't have connection counts
                    "timestamp": str(__import__('datetime').datetime.now())
                }
            else:
                # PostgreSQL health check
                result = conn.execute(text("SELECT version(), current_database(), current_user"))
                db_info = result.fetchone()
                
                # Get connection count
                conn_count_result = conn.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE datname = :db_name"),
                    {"db_name": DB_NAME}
                )
                connection_count = conn_count_result.scalar()
                
                # Get database size
                size_result = conn.execute(
                    text("SELECT pg_size_pretty(pg_database_size(:db_name))"),
                    {"db_name": DB_NAME}
                )
                db_size = size_result.scalar()
                
                return {
                    "status": "healthy",
                    "database_version": db_info[0],
                    "database_name": db_info[1],
                    "current_user": db_info[2],
                    "connection_count": connection_count,
                    "database_size": db_size,
                    "database_type": "PostgreSQL",
                    "timestamp": str(__import__('datetime').datetime.now())
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_type": "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite",
            "timestamp": str(__import__('datetime').datetime.now())
        }

# Context manager for database sessions
class DatabaseSession:
    """
    Context manager for database sessions.
    """
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
            logger.error(f"Database session error: {exc_val}")
        else:
            self.db.commit()
        self.db.close()