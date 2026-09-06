"""환경설정 Modeless 창 모듈 (T0106)."""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chzzk_downloader.core.cookie_manager import (
    clear_cookies,
    export_cookie_file,
    get_cookie_status_summary,
    load_cookie_file,
)
from chzzk_downloader.gui.cookie_viewer_dialog import CookieViewerDialog


class SettingsWindow(QDialog):
    """메인 창과 독립적으로 조작 가능한 Modeless 환경설정 창."""

    cookies_updated = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("환경설정")
        self.resize(520, 320)
        self.setModal(False)  # Modeless 창으로 메인 창 상호작용 허용

        self._init_ui()
        self.refresh_status()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. 네이버 / 치지직 쿠키 설정 그룹
        self.cookie_group = QGroupBox("네이버 / 치지직 쿠키 관리", self)
        group_layout = QVBoxLayout(self.cookie_group)
        group_layout.setContentsMargins(12, 14, 12, 14)
        group_layout.setSpacing(10)

        desc_label = QLabel(
            "성인 인증(19+) 및 비공개/구독 VOD 다운로드를 위해 네이버 로그인 쿠키가 필요합니다.",
            self.cookie_group,
        )
        desc_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        desc_label.setWordWrap(True)
        group_layout.addWidget(desc_label)

        # 상태 라벨
        self.status_label = QLabel("상태: 등록된 쿠키 없음", self.cookie_group)
        self.status_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        group_layout.addWidget(self.status_label)

        # 액션 버튼 행: [네이버 로그인] [보기 / 직접 입력] [불러오기 ▾] [내보내기] [초기화]
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.login_btn = QPushButton("네이버 로그인", self.cookie_group)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #03c75a; color: white; border: none; "
            "border-radius: 4px; padding: 4px 12px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: #02b150; }"
        )
        self.login_btn.clicked.connect(self._on_naver_login_clicked)
        btn_row.addWidget(self.login_btn)

        self.view_btn = QPushButton("보기 / 직접 입력", self.cookie_group)
        self.view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_btn.clicked.connect(self._on_view_clicked)
        btn_row.addWidget(self.view_btn)

        self.import_btn = QPushButton("파일 불러오기", self.cookie_group)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.clicked.connect(self._on_import_file)
        btn_row.addWidget(self.import_btn)

        self.export_btn = QPushButton("내보내기", self.cookie_group)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._on_export_clicked)
        btn_row.addWidget(self.export_btn)

        self.clear_btn = QPushButton("초기화", self.cookie_group)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet("color: #ef4444;")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        layout.addWidget(self.cookie_group)
        layout.addStretch()

        # 하단 닫기 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.close_btn = QPushButton("닫기", self)
        self.close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.close_btn)
        layout.addLayout(bottom_layout)

    def refresh_status(self) -> None:
        """현재 쿠키 상태에 따라 라벨과 스타일을 갱신합니다."""
        from chzzk_downloader.core.cookie_manager import (
            SessionStatus,
            get_last_session_status,
        )

        status, _ = get_last_session_status()
        summary = get_cookie_status_summary()
        self.status_label.setText(f"상태: {summary}")

        if status == SessionStatus.EXPIRED:
            self.status_label.setStyleSheet(
                "color: #ef4444; font-size: 12px; font-weight: bold;"
            )
            self.export_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
        elif "확인" in summary or status == SessionStatus.VALID:
            self.status_label.setStyleSheet(
                "color: #10b981; font-size: 12px; font-weight: bold;"
            )
            self.export_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
        else:
            self.status_label.setStyleSheet(
                "color: #9ca3af; font-size: 12px; font-weight: bold;"
            )
            self.export_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)

    def _on_naver_login_clicked(self) -> None:
        """내장 브라우저 네이버 로그인 창을 엽니다."""
        from chzzk_downloader.gui.naver_login_dialog import NaverLoginDialog

        self._login_dialog = NaverLoginDialog(self)
        self._login_dialog.login_success.connect(self._on_naver_login_success)
        self._login_dialog.exec()
        self._login_dialog.deleteLater()
        self._login_dialog = None

    def _on_naver_login_success(self, msg: str) -> None:
        """네이버 로그인 완료 시 상태를 갱신하고 변경 시그널을 방출합니다."""
        self.refresh_status()
        self.cookies_updated.emit()

    def _on_view_clicked(self) -> None:
        """쿠키 보기 및 직접 입력 모달 다이얼로그를 엽니다."""
        dialog = CookieViewerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_status()
            self.cookies_updated.emit()

    def _on_import_file(self) -> None:
        """Netscape 형식의 쿠키 파일(*.txt)을 파일 탐색기에서 선택해 불러옵니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Netscape 쿠키 파일 선택",
            "",
            "Netscape HTTP Cookie Files (*.txt);;모든 파일 (*.*)",
        )
        if file_path:
            ok, msg = load_cookie_file(Path(file_path))
            if ok:
                QMessageBox.information(self, "불러오기 완료", msg)
                self.refresh_status()
                self.cookies_updated.emit()
            else:
                QMessageBox.warning(self, "불러오기 실패", msg)

    def _on_export_clicked(self) -> None:
        """현재 저장된 쿠키를 파일로 내보냅니다."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "쿠키 파일 내보내기",
            "cookies.txt",
            "Netscape HTTP Cookie Files (*.txt);;모든 파일 (*.*)",
        )
        if file_path:
            ok, msg = export_cookie_file(Path(file_path))
            if ok:
                QMessageBox.information(self, "내보내기 완료", msg)
            else:
                QMessageBox.warning(self, "내보내기 실패", msg)

    def _on_clear_clicked(self) -> None:
        """등록된 쿠키를 초기화합니다."""
        reply = QMessageBox.question(
            self,
            "쿠키 초기화",
            "저장된 쿠키를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = clear_cookies()
            if ok:
                self.refresh_status()
                self.cookies_updated.emit()
                QMessageBox.information(
                    self, "초기화 완료", "등록된 쿠키가 삭제되었습니다."
                )
            else:
                QMessageBox.warning(self, "초기화 실패", msg)
