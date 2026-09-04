"""T0102. URL 입력 정리, VOD 판별, 컨텍스트 메뉴 및 토스트 알림 단위/통합 테스트."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QApplication

from chzzk_downloader.config import SUCCESS_TOAST_DURATION_MS
from chzzk_downloader.core.api import VodInfo, VodNotFoundError
from chzzk_downloader.gui.main_window import MainWindow


@pytest.fixture
def main_window(qtbot):
    """메인 창 인스턴스를 생성하고 표시하는 fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window


def test_empty_url_does_not_show_toast(main_window, qtbot):
    """URL 입력칸이 비어있거나 공백만 있을 때는 토스트를 띄우지 않고 무시하는지 검증."""
    # 1. 빈 문자열 클릭
    main_window.url_input.setText("")
    qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
    assert main_window.toast.isHidden() is True

    # 2. 공백 문자열 클릭
    main_window.url_input.setText("   \t\n  ")
    qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
    assert main_window.toast.isHidden() is True

    # 3. 빈 문자열 상태에서 Enter 키 입력
    main_window.url_input.setText("")
    qtbot.keyClick(main_window.url_input, Qt.Key.Key_Return)
    assert main_window.toast.isHidden() is True


def test_invalid_url_shows_error_toast_and_clears_input(main_window, qtbot):
    """잘못된 URL 입력 시 네트워크 호출 없이 '지원하지 않는 URL' 토스트가 뜨고 입력칸이 비워지는지 검증."""
    with patch("chzzk_downloader.gui.main_window.VodCheckWorker") as mock_worker:
        main_window.url_input.setText("https://invalid-url.com/abc")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 백그라운드 워커가 생성/실행되지 않아야 함
        mock_worker.assert_not_called()

        # 입력칸이 비워졌는지 검증
        assert main_window.url_input.text() == ""

        # 지원하지 않는 URL 에러 토스트 표시 검증
        assert main_window.toast.isHidden() is False
        assert "지원하지 않는 URL" in main_window.toast.label.text()
        assert main_window.toast._timer.isActive() is False  # 명시적 클릭 시까지 유지


def test_invalid_url_toast_dismissed_on_click(main_window, qtbot):
    """잘못된 URL로 발생한 토스트를 클릭했을 때 사라지는지 검증."""
    main_window.url_input.setText("not_a_valid_url")
    qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
    assert main_window.toast.isHidden() is False

    # 토스트 클릭 시 사라짐
    qtbot.mouseClick(main_window.toast, Qt.MouseButton.LeftButton)
    assert main_window.toast.isHidden() is True


def test_new_download_request_dismisses_previous_toast(main_window, qtbot):
    """새로운 다운로드 버튼 클릭 시 이전 토스트가 즉시 사라지는지 검증."""
    # 1. 먼저 잘못된 URL로 에러 토스트 띄우기
    main_window.url_input.setText("invalid_url_1")
    qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
    assert main_window.toast.isHidden() is False

    # 2. 다른 정상 URL 입력 후 클릭 시 이전 토스트 dismiss 후 새로운 상태 반영 확인
    mock_vod = VodInfo(
        video_no="15016450",
        video_title="실제 테스트 방송",
        channel_name="테스트채널",
    )
    with patch("chzzk_downloader.gui.workers.fetch_vod_info", return_value=mock_vod):
        main_window.url_input.setText("https://chzzk.naver.com/video/15016450")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        assert main_window.url_input.text() == ""
        assert not main_window.toast.isHidden()
        assert "+" in main_window.toast.label.text()
        assert "15016450" in main_window.toast.label.text()
        assert main_window.toast._timer.isActive() is True


def test_valid_url_success_flow_and_input_cleared(main_window, qtbot):
    """정상 VOD URL 입력 시 입력칸 비움, '+ [URL]' 토스트 2초 타이머 노출 검증."""
    mock_vod = VodInfo(
        video_no="15016450",
        video_title="치지직 테스트 방송 다시보기",
        channel_name="채널A",
    )

    with patch("chzzk_downloader.gui.workers.fetch_vod_info", return_value=mock_vod):
        test_url = "https://chzzk.naver.com/video/15016450"
        main_window.url_input.setText(f"  {test_url} \n")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 1. URL 입력칸이 즉시 비워지는지 검증
        assert main_window.url_input.text() == ""

        # 2. 토스트에 '+'와 입력 URL이 표시되는지 검증
        assert main_window.toast.isHidden() is False
        text = main_window.toast.label.text()
        assert "+" in text
        assert test_url in text

        # 3. 2초 자동 소멸 타이머 설정 여부 검증
        assert main_window.toast._timer.isActive() is True
        assert main_window.toast._timer.interval() == SUCCESS_TOAST_DURATION_MS

        # 4. 워커 완료 대기 후에도 기존 '+ [URL]' 토스트가 덮어씌워지지 않고 유지되는지 검증
        qtbot.waitUntil(lambda: main_window.download_btn.isEnabled(), timeout=2000)
        assert "+" in main_window.toast.label.text()
        assert test_url in main_window.toast.label.text()


def test_valid_url_not_found_failure_flow(main_window, qtbot):
    """존재하지 않는 VOD URL 입력 시 실패 토스트가 유지되는지 검증."""
    with patch(
        "chzzk_downloader.gui.workers.fetch_vod_info",
        side_effect=VodNotFoundError("동영상 정보가 존재하지 않습니다."),
    ):
        main_window.url_input.setText("https://chzzk.naver.com/video/99999999")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 입력칸은 비워짐
        assert main_window.url_input.text() == ""

        # 워커 종료 후 실패 토스트로 전환 및 클릭 전까지 유지 검증
        qtbot.waitUntil(
            lambda: "VOD 확인 실패" in main_window.toast.label.text(), timeout=2000
        )
        assert "동영상 정보가 존재하지 않습니다." in main_window.toast.label.text()
        assert main_window.toast._timer.isActive() is False


def test_url_input_enter_key_triggers_download(main_window, qtbot):
    """URL 입력창 활성화 상태에서 Enter 키 입력 시 다운로드 트리거 및 입력칸 비움 검증."""
    with patch("chzzk_downloader.gui.main_window.VodCheckWorker"):
        main_window.url_input.setText("invalid_url_enter_test")
        qtbot.keyClick(main_window.url_input, Qt.Key.Key_Return)

        # Enter 입력으로 입력칸이 비워지고 에러 토스트가 뜨는지 확인
        assert main_window.url_input.text() == ""
        assert main_window.toast.isHidden() is False
        assert "지원하지 않는 URL" in main_window.toast.label.text()


def test_url_input_context_menu_items_and_paste_download(main_window, qtbot):
    """URL 입력칸 우클릭 컨텍스트 메뉴 항목 구성 및 '붙여넣고 다운로드' 동작 검증."""
    menu = main_window._create_url_context_menu()
    actions = [action.text() for action in menu.actions() if not action.isSeparator()]

    expected_actions = [
        "실행 취소",
        "다시 실행",
        "잘라내기",
        "복사",
        "붙여넣기",
        "붙여넣고 다운로드",
        "삭제",
        "모두 선택",
    ]
    assert actions == expected_actions

    # '붙여넣고 다운로드' 동작 테스트
    clipboard = QApplication.clipboard()
    assert clipboard is not None
    test_url = "https://chzzk.naver.com/video/15016450"
    clipboard.setText(test_url)

    mock_vod = VodInfo(
        video_no="15016450",
        video_title="컨텍스트 메뉴 테스트",
        channel_name="채널B",
    )
    with patch("chzzk_downloader.gui.workers.fetch_vod_info", return_value=mock_vod):
        # 붙여넣고 다운로드 실행
        main_window._on_paste_and_download()

        # 입력칸이 클리어되고 토스트가 떴는지 검증
        assert main_window.url_input.text() == ""
        assert not main_window.toast.isHidden()
        assert "+" in main_window.toast.label.text()
        assert test_url in main_window.toast.label.text()


def test_url_input_context_menu_delete_action(main_window):
    """컨텍스트 메뉴의 '삭제' 기능이 선택된 텍스트만 삭제하는지 검증."""
    main_window.url_input.setText("hello world")
    # 'world' 부분 선택 (인덱스 6부터 길이 5)
    main_window.url_input.setSelection(6, 5)

    menu = main_window._create_url_context_menu()
    delete_action = next(a for a in menu.actions() if a.text() == "삭제")
    assert delete_action.isEnabled() is True

    delete_action.trigger()
    assert main_window.url_input.text() == "hello "


def test_url_input_show_context_menu_non_modal(main_window):
    """우클릭 시 메뉴가 non-modal(popup)로 호출되는지 검증."""
    main_window._show_url_context_menu(QPoint(10, 10))
    assert main_window._url_context_menu is not None
    assert main_window._url_context_menu.isVisible()
    main_window._url_context_menu.close()
