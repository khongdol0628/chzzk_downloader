"""T0102 메인 창 VOD 판별 및 오버레이 토스트 통합 테스트."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt

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


def test_invalid_url_shows_error_toast_without_network_call(main_window, qtbot):
    """잘못된 URL 입력 시 네트워크 호출 없이 '지원하지 않는 URL' 토스트가 뜨는지 검증."""
    with patch("chzzk_downloader.gui.main_window.VodCheckWorker") as mock_worker:
        main_window.url_input.setText("https://invalid-url.com/abc")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 백그라운드 워커가 생성/실행되지 않아야 함
        mock_worker.assert_not_called()

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

    # 2. 다른 URL 입력 후 클릭 시 이전 토스트 dismiss 후 새로운 상태 반영 확인
    mock_vod = VodInfo(
        video_no="15016450",
        video_title="실제 테스트 방송",
        channel_name="테스트채널",
    )
    with patch("chzzk_downloader.gui.workers.fetch_vod_info", return_value=mock_vod):
        main_window.url_input.setText("https://chzzk.naver.com/video/15016450")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 워커 종료 대기
        qtbot.waitUntil(
            lambda: not main_window.toast.isHidden()
            and "VOD 정보 확인 성공" in main_window.toast.label.text(),
            timeout=2000,
        )
        assert "실제 테스트 방송" in main_window.toast.label.text()
        assert "15016450" in main_window.toast.label.text()
        assert main_window.toast._timer.isActive() is True


def test_valid_url_success_flow(main_window, qtbot):
    """정상 VOD URL 입력 시 비동기 조회 후 성공 토스트가 2초 타이머로 뜨는지 검증."""
    mock_vod = VodInfo(
        video_no="15016450",
        video_title="치지직 테스트 방송 다시보기",
        channel_name="채널A",
    )

    with patch("chzzk_downloader.gui.workers.fetch_vod_info", return_value=mock_vod):
        main_window.url_input.setText("  https://chzzk.naver.com/video/15016450 \n")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        # 비동기 워커가 돌고 있으므로 버튼이 일시 비활성화되었다가 복구되는지 확인
        qtbot.waitUntil(lambda: main_window.download_btn.isEnabled(), timeout=2000)

        # 성공 토스트 내용 검증
        assert main_window.toast.isHidden() is False
        text = main_window.toast.label.text()
        assert "VOD 정보 확인 성공" in text
        assert "치지직 테스트 방송 다시보기" in text
        assert "15016450" in text

        # 2초 자동 소멸 타이머 설정 여부 검증
        assert main_window.toast._timer.isActive() is True
        assert main_window.toast._timer.interval() == SUCCESS_TOAST_DURATION_MS


def test_valid_url_not_found_failure_flow(main_window, qtbot):
    """존재하지 않는 VOD URL 입력 시 실패 토스트가 유지되는지 검증."""
    with patch(
        "chzzk_downloader.gui.workers.fetch_vod_info",
        side_effect=VodNotFoundError("동영상 정보가 존재하지 않습니다."),
    ):
        main_window.url_input.setText("https://chzzk.naver.com/video/99999999")
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

        qtbot.waitUntil(lambda: not main_window.toast.isHidden(), timeout=2000)
        text = main_window.toast.label.text()
        assert "VOD 확인 실패" in text
        assert "동영상 정보가 존재하지 않습니다." in text
        assert main_window.toast._timer.isActive() is False  # 클릭 전까지 소멸되지 않음


def test_url_input_enter_key_triggers_download(main_window, qtbot):
    """URL 입력창 활성화 상태에서 Enter 키 입력 시 다운로드 버튼이 트리거되는지 검증."""
    with patch("chzzk_downloader.gui.main_window.VodCheckWorker"):
        main_window.url_input.setText("invalid_url_enter_test")
        qtbot.keyClick(main_window.url_input, Qt.Key.Key_Return)

        # Enter 입력으로 다운로드 로직이 수행되어 에러 토스트가 뜨는지 확인
        assert main_window.toast.isHidden() is False
        assert "지원하지 않는 URL" in main_window.toast.label.text()

