"""T0101. 메인 창 기본 레이아웃 및 입력 구성요소 단위 테스트."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QPushButton

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


def test_input_area_layout_order(main_window):
    """입력 영역 배치 순서가 [붙여넣기] [URL 입력칸] [다운로드] 순인지 검증."""
    assert hasattr(main_window, "paste_btn")
    assert hasattr(main_window, "url_input")
    assert hasattr(main_window, "download_btn")

    central = main_window.centralWidget()
    assert central is not None
    central_layout = central.layout()
    assert central_layout is not None
    item1 = central_layout.itemAt(1)
    assert item1 is not None
    input_layout = item1.layout()
    assert isinstance(input_layout, QHBoxLayout)

    # 수평 배치 순서: 0번 paste_btn, 1번 url_input, 2번 download_btn
    item0 = input_layout.itemAt(0)
    item1 = input_layout.itemAt(1)
    item2 = input_layout.itemAt(2)
    assert item0 is not None and item0.widget() == main_window.paste_btn
    assert item1 is not None and item1.widget() == main_window.url_input
    assert item2 is not None and item2.widget() == main_window.download_btn


def test_paste_button_behavior(main_window, qtbot):
    """붙여넣기 버튼 속성 및 클립보드 텍스트 반영 동작 검증."""
    assert main_window.paste_btn.text() == "📋"
    assert main_window.paste_btn.toolTip() == "붙여넣기"
    assert main_window.paste_btn.isEnabled()

    clipboard = QApplication.clipboard()
    assert clipboard is not None
    test_text = "https://chzzk.naver.com/video/987654"
    clipboard.setText(test_text)

    # 붙여넣기 버튼 클릭
    qtbot.mouseClick(main_window.paste_btn, Qt.MouseButton.LeftButton)
    assert main_window.url_input.text() == test_text


def test_url_input_placeholder_clear_button_and_typing(main_window, qtbot):
    """URL 입력칸의 플레이스홀더, 삭제(Clear) 아이콘 활성화, 텍스트 입력 검증."""
    assert hasattr(main_window, "url_input")
    assert main_window.url_input.placeholderText() == "치지직 VOD URL을 입력하세요"
    assert main_window.url_input.isEnabled()
    # 삭제(Clear) 버튼 활성화 검증
    assert main_window.url_input.isClearButtonEnabled() is True

    # 텍스트 입력 테스트
    test_url = "https://chzzk.naver.com/video/12345"
    qtbot.keyClicks(main_window.url_input, test_url)
    assert main_window.url_input.text() == test_url

    # 클리어 동작 검증
    main_window.url_input.clear()
    assert main_window.url_input.text() == ""


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
    all_buttons = main_window.findChildren(QPushButton)
    button_texts = [btn.text() for btn in all_buttons]

    # 오직 '설정', '다운로드', '📋'(붙여넣기) 버튼만 존재해야 함
    assert set(button_texts) == {"설정", "다운로드", "📋"}

    # 미구현 관련 필드가 없는지 확인
    assert not hasattr(main_window, "channel_list")
    assert not hasattr(main_window, "notification_area")
    assert not hasattr(main_window, "system_status")
