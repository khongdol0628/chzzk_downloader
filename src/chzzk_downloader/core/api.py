"""치지직 VOD API 클라이언트 모듈."""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from chzzk_downloader.config import CHZZK_API_BASE_URL, DEFAULT_USER_AGENT


class VodApiError(Exception):
    """VOD API 호출 또는 응답 오류."""


class VodNotFoundError(VodApiError):
    """존재하지 않거나 삭제된 VOD."""


@dataclass
class VodInfo:
    """치지직 VOD 메타데이터 정보."""

    video_no: str
    video_title: str
    channel_name: str = ""
    duration: int = 0
    thumbnail_url: str = ""


def fetch_vod_info(video_no: str, timeout: float = 10.0) -> VodInfo:
    """치지직 API를 호출하여 VOD 메타데이터 정보를 조회합니다.

    Args:
        video_no: VOD 고유 식별 번호.
        timeout: HTTP 요청 제한 시간(초).

    Returns:
        조회된 VodInfo 객체.

    Raises:
        VodNotFoundError: VOD가 존재하지 않는 경우 (404 등).
        VodApiError: 네트워크 연결 실패 또는 API 응답 오류인 경우.
    """
    url = f"{CHZZK_API_BASE_URL}/service/v3/videos/{video_no}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise VodNotFoundError("동영상 정보가 존재하지 않습니다.") from e
        raise VodApiError(f"HTTP {e.code} 오류") from e
    except urllib.error.URLError as e:
        raise VodApiError(f"네트워크 오류: {e.reason}") from e
    except Exception as e:
        raise VodApiError(f"요청 실패: {e}") from e

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as e:
        raise VodApiError("API 응답 JSON 파싱 실패") from e

    code = data.get("code")
    if code == 404:
        raise VodNotFoundError(
            data.get("message") or "동영상 정보가 존재하지 않습니다."
        )
    if code != 200:
        message = data.get("message") or f"오류 코드 {code}"
        raise VodApiError(f"치지직 API 오류: {message}")

    content = data.get("content")
    if not isinstance(content, dict):
        raise VodApiError("유효하지 않은 응답 데이터 구조")

    title = content.get("videoTitle")
    if not title:
        raise VodApiError("동영상 제목 정보가 없습니다.")

    channel = content.get("channel") or {}
    channel_name = channel.get("channelName", "")
    duration = content.get("duration", 0)
    thumbnail_url = content.get("thumbnailImageUrl", "")

    return VodInfo(
        video_no=str(content.get("videoNo", video_no)),
        video_title=title,
        channel_name=channel_name,
        duration=duration,
        thumbnail_url=thumbnail_url,
    )
