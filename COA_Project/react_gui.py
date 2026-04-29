#!/usr/bin/env python3
"""
React dashboard entry — starts the Flask API for the Vite/React UI.

Usage:
  1) Terminal A:  python react_gui.py
  2) Terminal B:  cd web && npm install && npm run dev
  3) Browser:     http://localhost:5173
"""

from web_api import create_app

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  C.O.A React UI — API server")
    print("=" * 60)
    print("  API:  http://127.0.0.1:5050")
    print("  UI:   cd web && npm install && npm run dev")
    print("        → http://localhost:5173")
    print("=" * 60 + "\n")
    create_app().run(host="127.0.0.1", port=5050, debug=False, threaded=True)
