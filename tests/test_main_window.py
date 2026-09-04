"""T0101. 실행 가능한 최소 메인 창 단위 테스트."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

from chzzk_downloader.gui.main_window import MainWindow


@pytest.fixture
def main_window(qtbot):
    """메인 창 인스턴스를 생성하고 qtbot에 등록하는 fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_main_window_initialization(main_window):
    """메인 창이 에러 없이 생성되고 기본 타이틀을 가지는지 검증."""
    assert main_window.windowTitle() == "치지직 VOD 다운로더"
    assert main_window.isVisible() is False


def test_settings_button(main_window, qtbot):
    """상단 설정 버튼이 존재하고 클릭 가능한지 검증."""
    assert hasattr(main_window, "settings_btn")
    assert main_window.settings_btn.text() == "설정"
    assert main_window.settings_btn.isEnabled()

    # 클릭 시 오류가 발생하지 않는지 확인
    qtbot.mouseClick(main_window.settings_btn, Qt.MouseButton.LeftButton)


def test_url_input_placeholder_and_typing(main_window, qtbot):
    """URL 입력칸의 플레이스홀더 확인 및 텍스트 입력 가능 여부 검증."""
    assert hasattr(main_window, "url_input")
    assert main_window.url_input.placeholderText() == "치지직 VOD URL을 입력하세요"
    assert main_window.url_input.isEnabled()

    # 텍스트 입력 테스트
    test_url = "https://chzzk.naver.com/video/12345"
    qtbot.keyClicks(main_window.url_input, test_url)
    assert main_window.url_input.text() == test_url


def test_download_button(main_window, qtbot):
    """다운로드 버튼이 존재하고 클릭 가능한지 검증."""
    assert hasattr(main_window, "download_btn")
    assert main_window.download_btn.text() == "다운로드"
    assert main_window.download_btn.isEnabled()

    # 클릭 시 오류가 발생하지 않는지 확인
    qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)


def test_task_list_empty_state(main_window):
    """작업 목록 영역이 초기 상태에서 '작업 없음'을 표시하는지 검증."""
    assert hasattr(main_window, "task_list_widget")
    assert hasattr(main_window, "empty_label")
    assert main_window.empty_label.text() == "작업 없음"

    # 스택 위젯의 현재 표시 위젯이 empty_label인지 확인
    assert main_window.task_list_widget.stack.currentWidget() == main_window.empty_label


def test_no_unimplemented_widgets(main_window):
    """아직 구현하지 않은 채널·알림·시스템 영역이 미리 생성되지 않았는지 검증."""
    # 채널, 알림, 시스템 관련 속성이나 버튼이 없어야 함
    all_buttons = main_window.findChildren(QPushButton)
    button_texts = [btn.text() for btn in all_buttons]

    # 오직 '설정'과 '다운로드' 버튼만 존재해야 함
    assert set(button_texts) == {"설정", "다운로드"}

    # 미구현 관련 필드가 없는지 확인
    assert not hasattr(main_window, "channel_list")
    assert not hasattr(main_window, "notification_area")
    assert not hasattr(main_window, "system_status")
