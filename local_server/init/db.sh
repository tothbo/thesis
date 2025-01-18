#!/bin/bash

# Database preparation

## Stats
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS Statistics (
    id SERIAL PRIMARY KEY,
    broker TEXT NOT NULL,
    entitytype TEXT NOT NULL,
    entityid TEXT NOT NULL,
    teltx TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);"

## CameraLink
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS CameraLink (
    local_correlid TEXT PRIMARY KEY,  
    rtsp_host TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL
);"

## UserData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS UserData (
    local_userid SERIAL PRIMARY KEY,
    global_userid TEXT,
    name TEXT NOT NULL,
    fid BYTEA,
    static_unq TEXT,
    dynamic_unq TEXT,
    last_logged TIMESTAMP NOT NULL
);"

## NumberPlateData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS NumPlateData (
    numplateid SERIAL PRIMARY KEY,
    numplate TEXT NOT NULL,
    nickname TEXT,
    last_logged TIMESTAMP NOT NULL
);"

## DoorData
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS DoorData (
    local_correlid TEXT PRIMARY KEY,
    ipaddr INET UNIQUE NOT NULL,
    ont TEXT UNIQUE,
    nickname TEXT NOT NULL,
    location TEXT,
    color TEXT,
    authorized BOOLEAN NOT NULL,
    created TIMESTAMP DEFAULT NOW(),
    modified TIMESTAMP NOT NULL,
    camera_link TEXT REFERENCES CameraLink(local_correlid) ON DELETE SET NULL ON UPDATE CASCADE
);"

## Permissions
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS Permissions (
    id SERIAL PRIMARY KEY,
    group_name TEXT NOT NULL UNIQUE,
    user_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    numplate_enabled BOOLEAN NOT NULL DEFAULT FALSE
);"


## tobbszoros kapcsolati tablak
psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS JunctionPermissionUserData (
    ref_id INTEGER REFERENCES Permissions(id) ON DELETE CASCADE,
    ref_local_userid INTEGER REFERENCES UserData(local_userid) ON DELETE CASCADE,
    PRIMARY KEY (ref_id, ref_local_userid)
);"

psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS JunctionPermissionNumPlateData (
    ref_id INTEGER REFERENCES Permissions(id) ON DELETE CASCADE,
    ref_numplateid INTEGER REFERENCES NumPlateData(numplateid) ON DELETE CASCADE,
    PRIMARY KEY (ref_id, ref_numplateid)
);"

psql -U postgres -d main -c "CREATE TABLE IF NOT EXISTS JunctionPermissionsDoorData (
    ref_id INTEGER REFERENCES Permissions(id) ON DELETE CASCADE,
    ref_local_correlid TEXT REFERENCES DoorData(local_correlid) ON DELETE CASCADE,
    PRIMARY KEY (ref_id, ref_local_correlid)
);"
