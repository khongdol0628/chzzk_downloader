"""다운로드 작업 카드(Task Card) 위젯 모듈."""

import urllib.request
from enum import Enum
from typing import Any

from PyQt6 import sip
from PyQt6.QtCore import QEvent, QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QEnterEvent, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chzzk_downloader.config import DEFAULT_USER_AGENT
from chzzk_downloader.core.url_parser import parse_chzzk_vod_url
from chzzk_downloader.core.ytdlp import VodInfo


class TaskStatus(Enum):
    """작업 카드 상태 열거형."""

    ANALYZING = "ANALYZING"
    READY = "READY"
    FAILED_INVALID = "FAILED_INVALID"
    FAILED_LOGIN_REQUIRED = "FAILED_LOGIN_REQUIRED"


def format_duration(seconds: int) -> str:
    """초 단위 재생 시간을 HH:MM:SS 또는 MM:SS 형식으로 변환합니다."""
    if seconds <= 0:
        return "00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class ThumbnailLoaderThread(QThread):
    """썸네일 이미지를 백그라운드에서 비동기로 다운로드하는 스레드."""

    loaded = pyqtSignal(bytes)

    def __init__(self, url: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.url = url

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = resp.read()
            self.loaded.emit(data)
        except Exception:
            pass


class TaskCardWidget(QFrame):
    """작업 목록에 표시되는 VOD 개별 작업 카드 위젯 (시계 방향 4분면 레이아웃)."""

    delete_requested = pyqtSignal()
    request_open_cookies = pyqtSignal()

    def __init__(
        self,
        raw_url: str,
        status: TaskStatus = TaskStatus.ANALYZING,
        vod_info: VodInfo | None = None,
        video_no: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.raw_url = raw_url
        self.status = status
        self.vod_info = vod_info
        self.video_no = (
            video_no
            or (vod_info.video_no if vod_info else "")
            or (parse_chzzk_vod_url(raw_url) or "")
        )
        self.error_message: str = ""
        self.is_deleted: bool = False
        self._thumb_loader: ThumbnailLoaderThread | None = None

        self._init_ui()
        self._update_display()
        self._apply_style()

        if self.vod_info and self.vod_info.thumbnail_url:
            self._load_thumbnail(self.vod_info.thumbnail_url)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(400, 88)

    def _init_ui(self) -> None:
        self.setObjectName("TaskCardWidget")
        self.setMinimumHeight(88)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(12)

        # 좌측: 썸네일 박스 (120x68px, 16:9)
        self.thumb_label = QLabel(self)
        self.thumb_label.setFixedSize(120, 68)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setScaledContents(True)
        self.thumb_label.setStyleSheet(
            "background-color: #2a2a2a; color: #888888; border-radius: 4px; font-weight: bold; font-size: 12px;"
        )
        self.thumb_label.setText("VOD")
        main_layout.addWidget(self.thumb_label)

        # 우측: 4분면 정보 영역
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 2, 0, 2)
        info_layout.setSpacing(4)

        # 상단 행: 1번 위치(좌상단 타이틀) + 2번 위치(우상단 액션 아이콘)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        # 1번 위치 (좌상단): 작업명 / 상태 표시 라벨 (좌측 정렬 줄바꿈 지원)
        self.title_label = QLabel(self)
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.title_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        top_row.addWidget(self.title_label, stretch=1)

        # 2번 위치 (우상단): 회색조 액션 아이콘 그룹 (삭제 ✕ 버튼)
        # 마우스 진입(Hover) 시 노출되나, 숨김 시에도 공간을 예약(setRetainSizeWhenHidden)하여
        # 1번 위치 텍스트의 줄바꿈 위치가 흔들리지 않도록 유지
        self.delete_btn = QPushButton("✕", self)
        self.delete_btn.setToolTip("목록에서 제거")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sp = self.delete_btn.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.delete_btn.setSizePolicy(sp)
        self.delete_btn.hide()
        self.delete_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #888888; border: none; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(239, 68, 68, 0.2); color: #ef4444; border-radius: 3px; }"
        )
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        top_row.addWidget(self.delete_btn)

        info_layout.addLayout(top_row)
        info_layout.addStretch()

        # 하단 행: 4번 위치(좌하단 인증 액션) + 3번 위치(우하단 상태 요약)
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)

        # 4번 위치 (좌하단): 인증 필요 시 노출되는 액션 영역
        self.auth_container = QWidget(self)
        auth_layout = QHBoxLayout(self.auth_container)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.setSpacing(6)

        self.cookie_btn = QPushButton("쿠키 설정", self.auth_container)
        self.cookie_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cookie_btn.setStyleSheet(
            "QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 3px; padding: 2px 8px; font-size: 11px; }"
            "QPushButton:hover { background-color: #2563eb; }"
        )
        self.login_btn = QPushButton("네이버 로그인", self.auth_container)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #03c75a; color: white; border: none; border-radius: 3px; padding: 2px 8px; font-size: 11px; }"
            "QPushButton:hover { background-color: #02b150; }"
        )
        self.cookie_btn.clicked.connect(self.request_open_cookies.emit)
        self.login_btn.clicked.connect(self.request_open_cookies.emit)
        auth_layout.addWidget(self.cookie_btn)
        auth_layout.addWidget(self.login_btn)
        self.auth_container.hide()

        bottom_row.addWidget(self.auth_container)
        bottom_row.addStretch()

        # 3번 위치 (우하단): 재생 시간, 화질, 진행/실패 상태 라벨
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        bottom_row.addWidget(self.status_label)

        info_layout.addLayout(bottom_row)
        main_layout.addLayout(info_layout, stretch=1)

    def enterEvent(self, event: QEnterEvent | None) -> None:  # noqa: N802
        super().enterEvent(event)
        self.delete_btn.show()

    def leaveEvent(self, event: QEvent | None) -> None:  # noqa: N802
        super().leaveEvent(event)
        self.delete_btn.hide()

    def deleteLater(self) -> None:  # noqa: N802
        self.is_deleted = True
        if self._thumb_loader is not None and self._thumb_loader.isRunning():
            try:
                self._thumb_loader.loaded.disconnect()
            except Exception:
                pass
            self._thumb_loader.quit()
            self._thumb_loader.wait()
        super().deleteLater()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        self.is_deleted = True
        if self._thumb_loader is not None and self._thumb_loader.isRunning():
            try:
                self._thumb_loader.loaded.disconnect()
            except Exception:
                pass
            self._thumb_loader.quit()
            self._thumb_loader.wait()
        super().closeEvent(event)

    def _load_thumbnail(self, url: str) -> None:
        """비동기로 썸네일 이미지를 다운로드하여 라벨에 표시합니다."""
        if not url or self.is_deleted:
            return
        if self._thumb_loader is not None and self._thumb_loader.isRunning():
            try:
                self._thumb_loader.loaded.disconnect()
            except Exception:
                pass
            self._thumb_loader.quit()
            self._thumb_loader.wait()
        self._thumb_loader = ThumbnailLoaderThread(url, parent=self)
        self._thumb_loader.loaded.connect(self._on_thumbnail_loaded)
        self._thumb_loader.start()

    def _on_thumbnail_loaded(self, img_bytes: bytes) -> None:
        """다운로드된 썸네일 바이트를 QPixmap으로 변환하여 표시합니다."""
        if self.is_deleted or sip.isdeleted(self):
            return
        if not hasattr(self, "thumb_label") or sip.isdeleted(self.thumb_label):
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(img_bytes):
            scaled = pixmap.scaled(
                120,
                68,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setText("")

    def _update_display(self) -> None:
        """현재 상태에 따라 UI 텍스트 및 가시성을 갱신합니다."""
        if self.status == TaskStatus.ANALYZING:
            self.title_label.setText(f"분석 중... ({self.raw_url})")
            self.status_label.setText("분석 중...")
            self.auth_container.hide()
            self.thumb_label.setText("분석 중")
        elif self.status == TaskStatus.READY:
            if self.vod_info:
                self.title_label.setText(self.vod_info.display_name)
                # 화질 정보 및 재생 시간
                best_quality = ""
                if self.vod_info.formats:
                    valid_fmts = [f for f in self.vod_info.formats if f.height]
                    if valid_fmts:
                        best_fmt = max(valid_fmts, key=lambda f: f.height or 0)
                        fps_str = (
                            f"{int(best_fmt.fps)}"
                            if best_fmt.fps and best_fmt.fps > 30
                            else ""
                        )
                        best_quality = f"{best_fmt.height}p{fps_str}"
                dur_str = format_duration(self.vod_info.duration)
                self.status_label.setText(
                    f"{best_quality} | {dur_str}" if best_quality else dur_str
                )
            self.auth_container.hide()
            if not (self.vod_info and self.vod_info.thumbnail_url):
                self.thumb_label.setText("VOD")
        elif self.status == TaskStatus.FAILED_LOGIN_REQUIRED:
            self.title_label.setText(f"Login required; Please login: {self.raw_url}")
            self.status_label.setText("로그인 필요")
            self.auth_container.show()
            self.thumb_label.setText("인증 필요")
        elif self.status == TaskStatus.FAILED_INVALID:
            self.title_label.setText(f"Invalid: {self.raw_url}")
            self.status_label.setText(self.error_message or "분석 실패")
            self.auth_container.hide()
            self.thumb_label.setText("✕")

    def _apply_style(self) -> None:
        """상태에 따라 카드의 테두리 및 배경 하이라이트를 적용합니다."""
        if self.status in (
            TaskStatus.FAILED_INVALID,
            TaskStatus.FAILED_LOGIN_REQUIRED,
        ):
            # 빨간색 시각적 하이라이트 스타일
            self.setStyleSheet(
                "#TaskCardWidget {"
                "  background-color: rgba(239, 68, 68, 0.12);"
                "  border: 1px solid #ef4444;"
                "  border-radius: 6px;"
                "}"
            )
            self.title_label.setStyleSheet(
                "color: #ef4444; font-size: 13px; font-weight: 600;"
            )
            self.thumb_label.setStyleSheet(
                "background-color: rgba(239, 68, 68, 0.2); color: #ef4444; border-radius: 4px; font-weight: bold; font-size: 12px;"
            )
        else:
            # 기본 정상 카드 스타일
            self.setStyleSheet(
                "#TaskCardWidget {"
                "  background-color: #1e1e1e;"
                "  border: 1px solid #333333;"
                "  border-radius: 6px;"
                "}"
                "#TaskCardWidget:hover {"
                "  border: 1px solid #4b5563;"
                "  background-color: #252525;"
                "}"
            )
            self.title_label.setStyleSheet(
                "color: #f3f4f6; font-size: 13px; font-weight: 600;"
            )
            self.thumb_label.setStyleSheet(
                "background-color: #2a2a2a; color: #888888; border-radius: 4px; font-weight: bold; font-size: 12px;"
            )

    def update_with_vod_info(self, info: VodInfo) -> None:
        """yt-dlp VOD 분석 완료 시 메타데이터를 반영하여 준비 완료 상태로 갱신합니다."""
        self.status = TaskStatus.READY
        self.vod_info = info
        self._update_display()
        self._apply_style()
        if info.thumbnail_url:
            self._load_thumbnail(info.thumbnail_url)

    def set_failed(self, status: TaskStatus, error_message: str = "") -> None:
        """분석 실패 또는 오류 상태로 카드를 갱신하고 빨간색 하이라이트를 적용합니다."""
        self.status = status
        self.error_message = error_message
        self._update_display()
        self._apply_style()
