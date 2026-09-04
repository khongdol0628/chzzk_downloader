"""메인 윈도우 모듈."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
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

from chzzk_downloader.config import SUCCESS_TOAST_DURATION_MS
from chzzk_downloader.core.api import VodInfo
from chzzk_downloader.core.url_parser import parse_chzzk_vod_url
from chzzk_downloader.gui.toast import ToastType, ToastWidget
from chzzk_downloader.gui.workers import VodCheckWorker


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
    """실행 가능한 최소 메인 창 (T0101, T0102)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("치지직 VOD 다운로더")
        self.resize(640, 480)

        self._worker: VodCheckWorker | None = None
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

        # 2. URL 입력칸 및 다운로드 버튼 (수평 배치: [붙여넣기] [URL 입력칸] [다운로드])
        input_layout = QHBoxLayout()

        self.paste_btn = QPushButton("📋", self)
        self.paste_btn.setToolTip("붙여넣기")
        self.paste_btn.clicked.connect(self._on_paste_clicked)

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("치지직 VOD URL을 입력하세요")
        self.url_input.setClearButtonEnabled(True)

        self.download_btn = QPushButton("다운로드", self)
        self.download_btn.clicked.connect(self._on_download_clicked)
        self.url_input.returnPressed.connect(self.download_btn.click)

        input_layout.addWidget(self.paste_btn)
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.download_btn)
        main_layout.addLayout(input_layout)

        # 3. 작업 목록 영역 (URL 입력칸 하단)
        self.task_list_widget = TaskListWidget(self)
        self.task_list = self.task_list_widget.list_widget
        self.empty_label = self.task_list_widget.empty_label
        main_layout.addWidget(self.task_list_widget)

        # 4. 오버레이 토스트 위젯
        self.toast = ToastWidget(self)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "toast") and self.toast.isVisible():
            self.toast.reposition()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
        super().closeEvent(event)

    def _on_settings_clicked(self) -> None:
        """설정 버튼 클릭 핸들러 (향후 티켓에서 세부 구현)."""
        pass

    def _on_paste_clicked(self) -> None:
        """붙여넣기 버튼 클릭 핸들러: 클립보드 텍스트를 URL 입력칸에 설정."""
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            text = clipboard.text()
            if text:
                self.url_input.setText(text)

    def _on_download_clicked(self) -> None:
        """다운로드 버튼 클릭 핸들러 (T0102: URL 판별 및 비동기 VOD 정보 조회)."""
        # 새로운 요청 시작 시 기존 토스트 즉시 닫기
        self.toast.dismiss()

        raw_url = self.url_input.text().strip()
        if not raw_url:
            # 빈 입력일 때는 검증 및 토스트 노출 없이 무시
            return

        video_no = parse_chzzk_vod_url(raw_url)

        if not video_no:
            self.toast.show_toast(
                "지원하지 않는 URL",
                ToastType.ERROR,
                auto_dismiss_ms=0,
            )
            return

        self.download_btn.setEnabled(False)
        self._worker = VodCheckWorker(video_no, parent=self)
        self._worker.finished_success.connect(self._on_vod_check_success)
        self._worker.finished_failed.connect(self._on_vod_check_failed)
        self._worker.finished.connect(lambda: self.download_btn.setEnabled(True))
        self._worker.start()

    def _on_vod_check_success(self, info: VodInfo) -> None:
        """VOD 정보 조회 성공 시 2초 자동 소멸 토스트를 표시합니다."""
        message = f"VOD 정보 확인 성공\n{info.video_title} (ID: {info.video_no})"
        self.toast.show_toast(
            message,
            ToastType.SUCCESS,
            auto_dismiss_ms=SUCCESS_TOAST_DURATION_MS,
        )

    def _on_vod_check_failed(self, error_msg: str) -> None:
        """VOD 정보 조회 실패 시 클릭으로 닫는 실패 토스트를 표시합니다."""
        message = f"VOD 확인 실패: {error_msg}"
        self.toast.show_toast(
            message,
            ToastType.ERROR,
            auto_dismiss_ms=0,
        )
