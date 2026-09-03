"""메인 윈도우 모듈."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class TaskListWidget(QWidget):
    """작업 목록 및 빈 상태 안내를 관리하는 위젯."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget(self)
        self.empty_label = QLabel("작업 없음", self)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-size: 14px;")

        self.list_widget = QListWidget(self)

        self.stack.addWidget(self.empty_label)
        self.stack.addWidget(self.list_widget)
        self.stack.setCurrentWidget(self.empty_label)

        layout.addWidget(self.stack)

    def refresh_state(self) -> None:
        """아이템 유무에 따라 표시 위젯을 전환합니다."""
        if self.list_widget.count() == 0:
            self.stack.setCurrentWidget(self.empty_label)
        else:
            self.stack.setCurrentWidget(self.list_widget)


class MainWindow(QMainWindow):
    """실행 가능한 최소 메인 창 (T0101)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("치지직 VOD 다운로더")
        self.resize(640, 480)

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. 상단 영역: 설정 버튼
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.settings_btn = QPushButton("설정", self)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        header_layout.addWidget(self.settings_btn)
        main_layout.addLayout(header_layout)

        # 2. URL 입력칸 및 다운로드 버튼 (수평 배치)
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("치지직 VOD URL을 입력하세요")
        self.url_input.setClearButtonEnabled(True)

        self.download_btn = QPushButton("다운로드", self)
        self.download_btn.clicked.connect(self._on_download_clicked)

        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.download_btn)
        main_layout.addLayout(input_layout)

        # 3. 작업 목록 영역 (URL 입력칸 하단)
        self.task_list_widget = TaskListWidget(self)
        self.task_list = self.task_list_widget.list_widget
        self.empty_label = self.task_list_widget.empty_label
        main_layout.addWidget(self.task_list_widget)

    def _on_settings_clicked(self) -> None:
        """설정 버튼 클릭 핸들러 (향후 티켓에서 세부 구현)."""
        pass

    def _on_download_clicked(self) -> None:
        """다운로드 버튼 클릭 핸들러 (향후 티켓에서 세부 구현)."""
        pass

