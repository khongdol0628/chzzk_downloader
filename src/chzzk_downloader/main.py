"""애플리케이션 진입점."""

import sys

from PyQt6.QtWidgets import QApplication

from chzzk_downloader.gui.main_window import MainWindow


def main() -> None:
    """애플리케이션을 실행합니다."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
