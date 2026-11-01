#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  SmartPark AI - Local Intelligent Parking Facility"
echo "========================================================"

if [ -f "smartpark-env/bin/activate" ]; then
    source smartpark-env/bin/activate
elif [ -f "smartpark-env/Scripts/activate" ]; then
    source smartpark-env/Scripts/activate
fi

python -c "from database.models import init_db; init_db(); print('Database ready.')"

echo ""
echo "Starting SmartPark AI Local Server on http://127.0.0.1:8000 ..."
echo "Default Guard: guard_admin / GuardPass@2026"
echo ""

python app.py

