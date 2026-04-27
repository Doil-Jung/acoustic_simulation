import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    # This works both in dev and in bundle
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(bundle_dir, path)

if __name__ == "__main__":
    # Ensure the app can find the core and visualization modules
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
