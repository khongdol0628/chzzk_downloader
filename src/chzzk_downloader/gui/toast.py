"""오버레이 토스트 알림 위젯."""

from enum import Enum

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class ToastType(Enum):
    """토스트 알림 종류."""

    SUCCESS = "success"
    ERROR = "error"


class ToastWidget(QFrame):
    """메인 창 내부에 오버레이 형태로 표시되는 토스트 알림 위젯."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

        self._init_ui()
        self.hide()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self.label)

        self.close_label = QLabel("✕", self)
        self.close_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px;"
        )
        layout.addWidget(self.close_label)

    def show_toast(
        self,
        message: str,
        toast_type: ToastType = ToastType.SUCCESS,
        auto_dismiss_ms: int = 0,
    ) -> None:
        """토스트를 표시합니다.

        Args:
            message: 표시할 메시지.
            toast_type: 토스트 종류 (SUCCESS 또는 ERROR).
            auto_dismiss_ms: 자동 소멸 시간(ms). 0 이하이면 수동으로 닫을 때까지 유지.
        """
        self.label.setText(message)

        if toast_type == ToastType.SUCCESS:
            bg_color = "#2E7D32"  # 녹색
        else:
            bg_color = "#C62828"  # 빨간색

        self.setStyleSheet(
            f"ToastWidget {{ background-color: {bg_color}; border-radius: 8px; }}"
            f"QLabel {{ color: white; font-size: 13px; font-weight: 500; }}"
        )

        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()

        self._timer.stop()
        if auto_dismiss_ms > 0:
            self._timer.start(auto_dismiss_ms)

    def reposition(self) -> None:
        """부모 위젯 기준으로 토스트 위치를 중앙 하단으로 재배치합니다."""
        parent_widget = self.parentWidget()
        if parent_widget is None:
            return
        max_width = max(240, int(parent_widget.width() * 0.85))
        self.setMaximumWidth(max_width)
        self.adjustSize()

        x = (parent_widget.width() - self.width()) // 2
        y = parent_widget.height() - self.height() - 24
        self.move(max(10, x), max(10, y))

    def dismiss(self) -> None:
        """토스트를 숨기고 타이머를 중지합니다."""
        self._timer.stop()
        self.hide()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """토스트 영역 클릭 시 즉시 닫힙니다."""
        self.dismiss()
        if event is not None:
            super().mousePressEvent(event)
