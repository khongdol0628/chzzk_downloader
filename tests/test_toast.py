"""오버레이 토스트 위젯 단위 테스트."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from chzzk_downloader.gui.toast import ToastType, ToastWidget


@pytest.fixture
def toast_widget(qtbot):
    """테스트용 부모 위젯 및 ToastWidget 생성 fixture."""
    parent = QWidget()
    qtbot.addWidget(parent)
    parent.resize(400, 300)
    parent.show()
    toast = ToastWidget(parent)
    toast._parent_ref = parent
    return toast


def test_toast_initial_state(toast_widget):
    """초기 상태에서 토스트가 숨김 상태인지 검증."""
    assert toast_widget.isHidden() is True
    assert toast_widget._timer.isActive() is False


def test_toast_show_success_with_auto_dismiss(toast_widget, qtbot):
    """성공 토스트 표시 시 지정된 시간 후 자동으로 사라지는지 검증."""
    toast_widget.show_toast("성공 메시지", ToastType.SUCCESS, auto_dismiss_ms=100)
    assert toast_widget.isHidden() is False
    assert toast_widget.label.text() == "성공 메시지"
    assert toast_widget._timer.isActive() is True

    # 100ms 경과 후 자동 소멸 대기
    qtbot.waitUntil(lambda: toast_widget.isHidden(), timeout=500)
    assert toast_widget._timer.isActive() is False


def test_toast_show_error_persists_without_auto_dismiss(toast_widget, qtbot):
    """auto_dismiss_ms=0인 경우 타이머 없이 계속 유지되는지 검증."""
    toast_widget.show_toast("실패 메시지", ToastType.ERROR, auto_dismiss_ms=0)
    assert toast_widget.isHidden() is False
    assert toast_widget.label.text() == "실패 메시지"
    assert toast_widget._timer.isActive() is False

    # 잠시 대기해도 닫히지 않음
    qtbot.wait(150)
    assert toast_widget.isHidden() is False


def test_toast_click_to_dismiss(toast_widget, qtbot):
    """토스트 영역 클릭 시 즉시 닫히는지 검증."""
    toast_widget.show_toast("클릭 테스트", ToastType.ERROR, auto_dismiss_ms=0)
    assert toast_widget.isHidden() is False

    # 토스트 위젯 클릭
    qtbot.mouseClick(toast_widget, Qt.MouseButton.LeftButton)
    assert toast_widget.isHidden() is True

