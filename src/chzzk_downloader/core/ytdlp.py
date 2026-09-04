"""yt-dlp 기반 VOD 메타데이터 조회 모듈."""

from dataclasses import dataclass, field
from typing import Any, cast

import yt_dlp
from yt_dlp.utils import DownloadError


class YtDlpError(Exception):
    """yt-dlp 관련 기본 예외."""


class VodNotFoundError(YtDlpError):
    """VOD 영상이 존재하지 않거나 삭제/비공개 상태일 때 발생하는 예외."""


class YtDlpNotInstalledError(YtDlpError):
    """yt-dlp 라이브러리를 불러올 수 없을 때 발생하는 예외."""


@dataclass
class VodFormatInfo:
    """VOD 개별 화질/스트림 정보."""

    format_id: str
    resolution: str = ""
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    tbr: float | None = None
    url: str = ""


@dataclass
class VodInfo:
    """yt-dlp로 추출한 VOD 메타데이터 모델."""

    video_no: str
    video_title: str
    channel_name: str
    thumbnail_url: str = ""
    duration: int = 0
    formats: list[VodFormatInfo] = field(default_factory=list)


def get_ytdlp_version() -> str:
    """현재 설치된 yt-dlp 버전을 반환합니다."""
    try:
        ver_module = getattr(yt_dlp, "version", None)
        version_str = getattr(ver_module, "__version__", None) if ver_module else None
        if not version_str:
            raise YtDlpNotInstalledError("yt-dlp 버전을 확인할 수 없습니다.")
        return str(version_str)
    except YtDlpNotInstalledError:
        raise
    except Exception as err:
        raise YtDlpNotInstalledError(
            f"yt-dlp 버전을 확인할 수 없습니다: {err}"
        ) from err


def extract_vod_info(url: str, ydl_opts: dict[str, Any] | None = None) -> VodInfo:
    """yt-dlp를 사용하여 VOD 메타데이터를 추출합니다.

    Args:
        url: 치지직 VOD URL
        ydl_opts: 추가 yt-dlp 옵션 (쿠키 등)

    Returns:
        VodInfo: 추출된 영상 메타데이터 모델

    Raises:
        VodNotFoundError: 영상이 존재하지 않거나 삭제/비공개인 경우
        YtDlpError: 네트워크 오류 또는 yt-dlp 처리 오류 발생 시
    """
    opts: dict[str, Any] = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if ydl_opts:
        opts.update(ydl_opts)

    try:
        with yt_dlp.YoutubeDL(cast(Any, opts)) as ydl:
            data = ydl.extract_info(url, download=False)
    except DownloadError as err:
        err_msg = str(err).lower()
        if (
            "404" in err_msg
            or "not found" in err_msg
            or "존재하지" in err_msg
            or "this video is unavailable" in err_msg
        ):
            raise VodNotFoundError("동영상 정보가 존재하지 않습니다.") from err
        raise YtDlpError(f"yt-dlp 영상 정보 추출 실패: {err}") from err
    except Exception as err:
        raise YtDlpError(f"yt-dlp 실행 오류: {err}") from err

    if not data:
        raise VodNotFoundError("동영상 정보를 가져올 수 없습니다.")

    formats_list: list[VodFormatInfo] = []
    raw_formats = data.get("formats")
    if isinstance(raw_formats, list):
        for fmt in raw_formats:
            if not isinstance(fmt, dict):
                continue
            format_id = str(fmt.get("format_id") or "")
            formats_list.append(
                VodFormatInfo(
                    format_id=format_id,
                    resolution=str(fmt.get("resolution") or ""),
                    width=fmt.get("width"),
                    height=fmt.get("height"),
                    fps=fmt.get("fps"),
                    tbr=fmt.get("tbr"),
                    url=str(fmt.get("url") or ""),
                )
            )

    channel_name = str(data.get("channel") or data.get("uploader") or "알 수 없음")
    video_no = str(data.get("id") or "")
    video_title = str(data.get("title") or "제목 없음")
    thumbnail_url = str(data.get("thumbnail") or "")
    duration = int(data.get("duration") or 0)

    return VodInfo(
        video_no=video_no,
        video_title=video_title,
        channel_name=channel_name,
        thumbnail_url=thumbnail_url,
        duration=duration,
        formats=formats_list,
    )
