from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

required_keys = [('db_host',str)]
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)
assert all(key in CONFIG and isinstance(CONFIG[key], vartype) and (vartype is str and CONFIG[key] != '') for key, vartype in required_keys)

engine = create_engine(CONFIG['db_host'], pool_size=30)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()