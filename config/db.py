"""
Database Configuration Module
Supports MySQL, SQLite, PostgreSQL with automatic engine mapping and environment variable support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import pymysql

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / '.env')

# Patch pymysql to satisfy Django MySQL backend requirements
pymysql.version_info = (2, 2, 7, "final", 0)
pymysql.install_as_MySQLdb()

# Read Database Credentials from Environment Variables
raw_engine = os.getenv('DB_ENGINE', 'mysql').strip().lower()

# Normalize DB_ENGINE to standard Django backends
ENGINE_MAP = {
    'mysql': 'django.db.backends.mysql',
    'django.db.backends.mysql': 'django.db.backends.mysql',
    'sqlite': 'django.db.backends.sqlite3',
    'sqlite3': 'django.db.backends.sqlite3',
    'django.db.backends.sqlite3': 'django.db.backends.sqlite3',
    'postgresql': 'django.db.backends.postgresql',
    'postgres': 'django.db.backends.postgresql',
    'django.db.backends.postgresql': 'django.db.backends.postgresql',
}

DB_ENGINE = ENGINE_MAP.get(raw_engine, raw_engine)
DB_NAME = os.getenv('DB_NAME', 'games')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3306')

if 'sqlite3' in DB_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / (DB_NAME if DB_NAME.endswith('.sqlite3') else f'{DB_NAME}.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
