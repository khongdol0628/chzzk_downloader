"""T0109. VOD 다운로드 설정 및 진입 제어 단위/통합 테스트."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from chzzk_downloader.core.filename_generator import (
    generate_vod_filename,
    resolve_duplicate_filename,
    sanitize_filename,
)
from chzzk_downloader.core.settings_manager import (
    get_current_settings,
    update_current_settings,
)
from chzzk_downloader.core.ytdlp import VodFormatInfo, VodInfo
from chzzk_downloader.gui.main_window import MainWindow
from chzzk_downloader.gui.settings_window import SettingsWindow
from chzzk_downloader.gui.switch_widget import SwitchWidget
from chzzk_downloader.gui.task_card import TaskCardWidget, TaskStatus


@pytest.fixture
def temp_settings_env(tmp_path, monkeypatch):
    """임시 디렉터리에 격리된 settings.json 환경을 제공하는 fixture."""
    test_settings_dir = tmp_path / ".chzzk_downloader"
    test_settings_file = test_settings_dir / "settings.json"

    def mock_get_settings_file_path():
        return test_settings_file

    monkeypatch.setattr(
        "chzzk_downloader.core.settings_manager.get_settings_file_path",
        mock_get_settings_file_path,
    )
    update_current_settings(
        download_dir=str(tmp_path / "chzzk_downloaded"),
        default_quality="최고 화질",
        file_extension=".mp4",
        vod_auto_download=True,
    )
    return test_settings_file


@pytest.fixture
def main_window(qtbot, temp_settings_env):
    """메인 창 fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window


# 1. 파일명 생성 및 중복 해결 단위 테스트
def test_sanitize_filename_converts_colon():
    """콜론을 전각 콜론으로 치환하고 금지 문자를 정제하는지 검증."""
    raw = '방송: 다시보기? <1> / 테스트 * | "호환"'
    sanitized = sanitize_filename(raw)
    assert ":" not in sanitized
    assert "：" in sanitized  # 전각 콜론
    assert "?" not in sanitized
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "/" not in sanitized
    assert "*" not in sanitized
    assert "|" not in sanitized
    assert '"' not in sanitized


def test_generate_vod_filename_with_and_without_live_date():
    """live_open_date 유무에 따른 파일명 명명 규칙 검증."""
    info_with_date = VodInfo(
        video_no="12345",
        video_title="테스트: 라이브",
        channel_name="스트리머A",
        live_open_date="2024-05-06",
    )
    name1 = generate_vod_filename(info_with_date, ext=".mp4")
    assert "date：2024-05-06" in name1
    assert "스트리머A" in name1

    info_without_date = VodInfo(
        video_no="67890",
        video_title="일반 영상",
        channel_name="스트리머B",
        live_open_date="",
    )
    name2 = generate_vod_filename(info_without_date, ext=".ts")
    assert name2 == "[스트리머B] 일반 영상 (67890).ts"


def test_resolve_duplicate_filename(tmp_path):
    """동일 파일이 존재할 경우 (1), (2) 넘버링된 고유 경로 반환 검증."""
    base_file = tmp_path / "video.mp4"
    base_file.touch()

    res1 = resolve_duplicate_filename(base_file)
    assert res1.name == "video (1).mp4"

    res1.touch()
    res2 = resolve_duplicate_filename(base_file)
    assert res2.name == "video (2).mp4"


# 2. 토글 스위치 위젯 단위 테스트
def test_switch_widget_toggle(qtbot):
    """SwitchWidget 클릭 시 상태 전환 및 toggled 시그널 방출 검증."""
    switch = SwitchWidget(checked=True)
    qtbot.addWidget(switch)
    assert switch.isChecked() is True

    signal_received = []
    switch.toggled.connect(lambda v: signal_received.append(v))

    qtbot.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert switch.isChecked() is False
    assert signal_received == [False]

    switch.setChecked(True)
    assert switch.isChecked() is True
    assert signal_received == [False, True]


# 3. SettingsWindow 토글 스위치 및 영속화 검증
def test_settings_window_vod_auto_download_toggle(qtbot, temp_settings_env):
    """SettingsWindow에서 VOD 자동 다운로드 스위치 조작 시 settings.json에 영속화되는지 검증."""
    window = SettingsWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.auto_switch.isChecked() is True
    assert get_current_settings().vod_auto_download is True

    qtbot.mouseClick(window.auto_switch, Qt.MouseButton.LeftButton)
    assert window.auto_switch.isChecked() is False
    assert get_current_settings().vod_auto_download is False

    # 새 인스턴스로 다시 로드 시 저장된 값 복원 검증
    window2 = SettingsWindow()
    qtbot.addWidget(window2)
    assert window2.auto_switch.isChecked() is False


# 4. 카드 1번 위치 문구 검증: 읽는 중… URL
def test_task_card_title_reading_url(qtbot):
    """분석 중 카드 생성 시 1번 위치 문구가 '읽는 중… {URL}'로 표시되는지 검증."""
    test_url = "https://chzzk.naver.com/video/15016450"
    card = TaskCardWidget(raw_url=test_url, status=TaskStatus.ANALYZING)
    qtbot.addWidget(card)

    assert card.title_label.text() == f"읽는 중… {test_url}"


# 5. VOD 자동 다운로드 OFF 시 4번 위치 대기 컨트롤 및 개별 설정 검증
def test_vod_auto_download_off_shows_waiting_controls(main_window, qtbot):
    """VOD 자동 다운로드가 OFF일 때 분석 완료 후 READY 상태 유지 및 4번 위치 대기 컨트롤 노출 검증."""
    update_current_settings(vod_auto_download=False)

    mock_vod = VodInfo(
        video_no="15016450",
        video_title="대기 테스트 방송",
        channel_name="스트리머A",
        duration=3600,
        formats=[
            VodFormatInfo(format_id="1080p", height=1080, fps=60.0),
            VodFormatInfo(format_id="720p", height=720, fps=30.0),
            VodFormatInfo(format_id="480p", height=480, fps=30.0),
        ],
        live_open_date="2024-05-06",
    )

    with patch("chzzk_downloader.gui.workers.extract_vod_info", return_value=mock_vod):
        test_url = "https://chzzk.naver.com/video/15016450"
        main_window.url_input.setText(test_url)
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: main_window.download_btn.isEnabled(), timeout=2000)

        card = main_window.task_list_widget.get_all_cards()[0]

        # 1. 카드는 READY 상태로 유지됨
        assert card.status == TaskStatus.READY

        # 2. 4번 위치 대기 컨테이너 노출 및 화질/확장자/폴더/시작 버튼 확인
        assert card.ready_container.isHidden() is False
        assert card.downloading_container.isHidden() is True
        assert card.quality_combo.currentText() == "1080p60"  # 최고화질 기본 선택
        assert card.ext_label.text() == ".mp4"
        assert card.folder_btn.isHidden() is False
        assert card.start_btn.isHidden() is False

        # 3. 화질 변경 테스트
        card.quality_combo.setCurrentText("720p")
        assert card.selected_quality == "720p"

        # 4. 폴더 변경 테스트 (QFileDialog 모킹)
        custom_folder = "C:/custom/download/path"
        with patch(
            "PyQt6.QtWidgets.QFileDialog.getExistingDirectory",
            return_value=custom_folder,
        ):
            card.folder_btn.click()
            assert card.custom_download_dir == Path(custom_folder).resolve()


# 6. 시작 아이콘(▶) 클릭 시 다운로드 시작 및 파일 중복 처리(옵션 A) 검증
def test_start_download_and_file_duplicate_handling(qtbot, tmp_path):
    """파일 중복 시 덮어쓰기 / 이름변경 / 취소 분기 및 UI 상태 전이 검증."""
    save_dir = tmp_path / "downloads"
    save_dir.mkdir()
    update_current_settings(download_dir=str(save_dir), vod_auto_download=False)

    mock_vod = VodInfo(
        video_no="15016450",
        video_title="테스트 영상",
        channel_name="스트리머A",
        duration=1800,
    )
    card = TaskCardWidget(
        raw_url="https://chzzk.naver.com/video/15016450",
        status=TaskStatus.READY,
        vod_info=mock_vod,
    )
    qtbot.addWidget(card)

    expected_file = save_dir / generate_vod_filename(mock_vod, ext=".mp4")

    # 1. 파일이 없을 때 -> 즉시 DOWNLOADING 전이
    assert expected_file.exists() is False
    card.trigger_start_download()
    assert card.status == TaskStatus.DOWNLOADING
    assert card.target_path == expected_file
    assert card.ready_container.isHidden() is True
    assert card.downloading_container.isHidden() is False
    assert card.recording_label.text() == "녹화 중…"
    assert card.spinner._timer.isActive() is True

    # 2. 동일 파일 생성
    expected_file.touch()
    card.status = TaskStatus.READY
    card._update_display()

    # 2-1. 중복 파일 존재 시: '취소' 선택
    with patch.object(card, "_prompt_duplicate_resolution", return_value="cancel"):
        ok = card.trigger_start_download()
        assert ok is False
        assert card.status == TaskStatus.READY

    # 2-2. 중복 파일 존재 시: '이름 변경' 선택
    with patch.object(card, "_prompt_duplicate_resolution", return_value="rename"):
        ok = card.trigger_start_download()
        assert ok is True
        assert card.status == TaskStatus.DOWNLOADING
        assert card.target_path is not None
        assert card.target_path.name == f"{expected_file.stem} (1).mp4"

    # 2-3. 중복 파일 존재 시: '덮어쓰기' 선택
    card.status = TaskStatus.READY
    card._update_display()
    with patch.object(card, "_prompt_duplicate_resolution", return_value="overwrite"):
        ok = card.trigger_start_download()
        assert ok is True
        assert card.status == TaskStatus.DOWNLOADING
        assert card.target_path == expected_file


# 7. 다운로드 중지 버튼(■) 및 확인 모달 검증
def test_stop_download_confirmation(qtbot, tmp_path):
    """중지 버튼 클릭 시 모달 승인/거부에 따른 안전 중단 검증."""
    mock_vod = VodInfo(
        video_no="15016450", video_title="중지 테스트", channel_name="스트리머A"
    )
    card = TaskCardWidget(
        raw_url="https://chzzk.naver.com/video/15016450",
        status=TaskStatus.DOWNLOADING,
        vod_info=mock_vod,
    )
    qtbot.addWidget(card)

    # 1. 중지 확인 모달에서 '아니오(No)' 선택 -> 다운로드 유지
    with patch(
        "PyQt6.QtWidgets.QMessageBox.question",
        return_value=QMessageBox.StandardButton.No,
    ):
        card.stop_btn.click()
        assert card.status == TaskStatus.DOWNLOADING

    # 2. 중지 확인 모달에서 '예(Yes)' 선택 -> READY 복귀
    with patch(
        "PyQt6.QtWidgets.QMessageBox.question",
        return_value=QMessageBox.StandardButton.Yes,
    ):
        card.stop_btn.click()
        assert card.status == TaskStatus.READY
        assert card.ready_container.isHidden() is False
        assert card.downloading_container.isHidden() is True
        assert card.spinner._timer.isActive() is False


# 8. 동일 VOD 재입력 시 확인 모달 및 클린 리셋 무결성 검증
def test_redownload_same_vod_clean_reset(main_window, qtbot):
    """작업 목록에 카드가 남아있는 상태에서 동일 URL 재입력 시 확인 모달 및 클린 리셋 검증."""
    mock_vod = VodInfo(
        video_no="15016450", video_title="재다운로드 테스트", channel_name="스트리머A"
    )

    with patch("chzzk_downloader.gui.workers.extract_vod_info", return_value=mock_vod):
        test_url = "https://chzzk.naver.com/video/15016450"
        main_window.url_input.setText(test_url)
        qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: main_window.download_btn.isEnabled(), timeout=2000)

        card = main_window.task_list_widget.get_all_cards()[0]

        # 1. 취소 선택 시 -> 카드 유지, 입력창 비움, 추가 동작 없음
        with patch.object(
            main_window, "_confirm_redownload_dialog", return_value=False
        ):
            main_window.url_input.setText(test_url)
            qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)

            assert main_window.url_input.text() == ""
            assert main_window.task_list_widget.list_widget.count() == 1

        # 2. 확인 선택 시 -> 클린 리셋 후 재분석/재다운로드 정상 진행
        with patch.object(main_window, "_confirm_redownload_dialog", return_value=True):
            with patch.object(
                card, "reset_for_redownload", wraps=card.reset_for_redownload
            ) as mock_reset:
                main_window.url_input.setText(test_url)
                qtbot.mouseClick(main_window.download_btn, Qt.MouseButton.LeftButton)
                assert mock_reset.called is True

                qtbot.waitUntil(
                    lambda: main_window.download_btn.isEnabled(), timeout=2000
                )
                # 재다운로드 완료 후 목록 개수 1개 유지 및 정상 상태 확인
                assert main_window.task_list_widget.list_widget.count() == 1
                assert card.status in (TaskStatus.READY, TaskStatus.DOWNLOADING)
