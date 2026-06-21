"""
Streamlit 멀티페이지 앱을 PyInstaller로 EXE 패키징하는 스크립트.

사용법: python build_exe.py
결과물: dist/AcousticSimulator/ 폴더
"""
import subprocess
import sys
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "portable_app")
DIST_NAME = "AcousticSimulator"


def ensure_pyinstaller():
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def create_launcher():
    """Streamlit 실행 런처 스크립트 생성"""
    launcher = os.path.join(APP_DIR, "_launcher.py")
    with open(launcher, 'w', encoding='utf-8') as f:
        f.write('''import sys
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
''')
    return launcher


def find_streamlit_dir():
    """Streamlit 패키지 위치 찾기"""
    import streamlit
    return os.path.dirname(streamlit.__file__)


def build():
    ensure_pyinstaller()
    launcher = create_launcher()
    streamlit_dir = find_streamlit_dir()
    
    # PyInstaller 명령 구성
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", DIST_NAME,
        "--noconfirm",
        # 앱 파일들
        f"--add-data={os.path.join(APP_DIR, 'app_main.py')}{os.pathsep}.",
        f"--add-data={os.path.join(APP_DIR, 'pages')}{os.pathsep}pages",
        f"--add-data={os.path.join(APP_DIR, 'core')}{os.pathsep}core",
        f"--add-data={os.path.join(APP_DIR, 'visualization')}{os.pathsep}visualization",
        f"--add-data={os.path.join(APP_DIR, 'dataset', 'models')}{os.pathsep}dataset/models",
        f"--add-data={os.path.join(APP_DIR, 'dataset', 'spectrum_data')}{os.pathsep}dataset/spectrum_data",
        # Streamlit 전체 (static files, config 등 포함 필수)
        f"--add-data={streamlit_dir}{os.pathsep}streamlit",
        # 패키지 메타데이터 (importlib.metadata에서 버전 조회에 필요)
        "--copy-metadata=streamlit",
        "--copy-metadata=altair",
        "--copy-metadata=pandas",
        "--copy-metadata=numpy",
        "--copy-metadata=pyarrow",
        # 히든 임포트
        "--hidden-import=streamlit",
        "--hidden-import=streamlit.runtime.scriptrunner",
        "--hidden-import=streamlit.web.cli",
        "--hidden-import=onnxruntime",
        "--hidden-import=scipy",
        "--hidden-import=scipy.signal",
        "--hidden-import=scipy.interpolate",
        "--hidden-import=scipy.special",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_agg",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=altair",
        "--hidden-import=jinja2",
        "--hidden-import=toml",
        "--hidden-import=validators",
        "--hidden-import=gitdb",
        "--hidden-import=pydeck",
        "--hidden-import=pyarrow",
        # 콘솔 표시 (디버깅용, 배포 시 --noconsole로 변경)
        "--console",
        # PyTorch 제외 (ONNX Runtime만 사용하므로 불필요, ~2GB 절약)
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=torchaudio",
        "--exclude-module=torch.cuda",
        "--exclude-module=onnxscript",
        "--exclude-module=onnx",
        "--exclude-module=triton",
        "--exclude-module=tensorboard",
        "--exclude-module=IPython",
        "--exclude-module=notebook",
        "--exclude-module=pytest",
        # 진입점
        launcher,
    ]
    
    print("=" * 60)
    print(f"Building {DIST_NAME}...")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode == 0:
        dist_dir = os.path.join(BASE_DIR, "dist", DIST_NAME)
        print("\n" + "=" * 60)
        print(f"Build SUCCESS!")
        print(f"Output: {dist_dir}")
        print(f"Run:    {os.path.join(dist_dir, DIST_NAME + '.exe')}")
        print("=" * 60)
    else:
        print(f"\nBuild FAILED with code {result.returncode}")


if __name__ == "__main__":
    build()
