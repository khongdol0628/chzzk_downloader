"""치지직 VOD API 클라이언트 단위 테스트."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from chzzk_downloader.core.api import (
    VodApiError,
    VodInfo,
    VodNotFoundError,
    fetch_vod_info,
)


def _create_mock_response(status_code: int, data: dict):
    """mock urlopen 응답 객체를 생성하는 헬퍼 함수."""
    body_bytes = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = status_code
    mock_resp.read.return_value = body_bytes
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


def test_fetch_vod_info_success():
    """정상 API 응답 시 VodInfo 객체가 올바르게 생성되는지 검증."""
    mock_payload = {
        "code": 200,
        "message": None,
        "content": {
            "videoNo": 15016450,
            "videoTitle": "테스트 방송 VOD 다시보기",
            "channel": {"channelName": "테스트스트리머"},
            "duration": 3600,
            "thumbnailImageUrl": "https://example.com/thumb.jpg",
        },
    }

    with patch("urllib.request.urlopen", return_value=_create_mock_response(200, mock_payload)):
        info = fetch_vod_info("15016450")
        assert isinstance(info, VodInfo)
        assert info.video_no == "15016450"
        assert info.video_title == "테스트 방송 VOD 다시보기"
        assert info.channel_name == "테스트스트리머"
        assert info.duration == 3600
        assert info.thumbnail_url == "https://example.com/thumb.jpg"


def test_fetch_vod_info_http_404():
    """HTTP 404 응답 시 VodNotFoundError가 발생하는지 검증."""
    http_error = urllib.error.HTTPError(
        url="https://api.chzzk.naver.com/service/v3/videos/99999",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=io.BytesIO(json.dumps({"code": 404, "message": "동영상 정보가 존재하지 않습니다."}).encode("utf-8")),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(VodNotFoundError, match="존재하지 않습니다"):
            fetch_vod_info("99999")


def test_fetch_vod_info_http_500():
    """HTTP 500 등 서버 오류 시 VodApiError가 발생하는지 검증."""
    http_error = urllib.error.HTTPError(
        url="https://api.chzzk.naver.com/service/v3/videos/123",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(b""),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(VodApiError, match="HTTP 500"):
            fetch_vod_info("123")


def test_fetch_vod_info_network_error():
    """네트워크 연결 단절 시 VodApiError가 발생하는지 검증."""
    url_error = urllib.error.URLError("Connection refused")

    with patch("urllib.request.urlopen", side_effect=url_error):
        with pytest.raises(VodApiError, match="네트워크 오류"):
            fetch_vod_info("123")


def test_fetch_vod_info_api_error_code():
    """JSON 응답의 code가 200이 아닐 때 적절한 예외가 발생하는지 검증."""
    mock_payload = {
        "code": 400,
        "message": "잘못된 요청입니다.",
        "content": None,
    }

    with patch("urllib.request.urlopen", return_value=_create_mock_response(200, mock_payload)):
        with pytest.raises(VodApiError, match="잘못된 요청입니다"):
            fetch_vod_info("123")
