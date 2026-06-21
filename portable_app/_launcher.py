import sys
import os
import webbrowser
import time
import threading

def open_browser(port):
    time.sleep(3)
    webbrowser.open(f"http://localhost:{port}")

def main():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    
    app_main = os.path.join(base, "app_main.py")
    port = 8501
    
    # Auto-open browser
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Streamlit을 직접 호출 (subprocess 사용하면 sys.executable이 EXE를 가리켜 무한루프)
    sys.argv = [
        "streamlit", "run", app_main,
        "--global.developmentMode", "false",
        "--server.port", str(port),
        "--browser.gatherUsageStats", "false",
        "--server.headless", "true",
    ]
    
    from streamlit.web.cli import main as st_main
    st_main()

if __name__ == "__main__":
    main()
