#!/bin/bas

# Database preparation
## GlobalServerData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS GlobalUserData (
    global_userid TEXT PRIMARY KEY,
    fullname TEXT NOT NULL,
    emailaddr TEXT NOT NULL UNIQUE,
    passwd TEXT NOT NULL UNIQUE,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL
);"

## GlobalServerData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS GlobalServerData (
    global_serverid text PRIMARY KEY,
    nickname TEXT,
    color TEXT
);"

## ServerSessionData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS ServerSessionData (
    global_servcorrid text PRIMARY KEY UNIQUE,
    global_serverid text REFERENCES GlobalServerData(global_serverid),
    ip INET NOT NULL,
    ont TEXT NOT NULL UNIQUE,
    deviceinfo text NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL
);"

## UserSessionData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS UserSessionData (
    global_usrcorrid TEXT PRIMARY KEY UNIQUE,
    global_userid TEXT UNIQUE REFERENCES GlobalUserData(global_userid),
    ip INET NOT NULL,
    deviceinfo TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL
);"

## tobbszoros kapcsolati tabla
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS JunctionUserDataGlobalServerData (
    global_userid text REFERENCES GlobalUserData(global_userid),
    global_serverid text REFERENCES GlobalServerData(global_serverid),
    admin BOOLEAN NOT NULL
);"