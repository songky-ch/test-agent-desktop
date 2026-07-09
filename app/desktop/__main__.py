import sys
from pathlib import Path

from app.desktop.main_window import QApplication, MainWindow


def main() -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is required to start the desktop UI")
    app = QApplication(sys.argv)
    window = MainWindow(Path.cwd())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
