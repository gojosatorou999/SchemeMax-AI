"""
api/index.py — Vercel serverless entrypoint for SchemeMax AI.

Vercel's Python runtime expects a WSGI-compatible app object named `app`.
We import the Flask app factory from the project root.
"""
import sys
import os

# Ensure project root is on the path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
