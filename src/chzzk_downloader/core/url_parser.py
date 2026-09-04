"""치지직 VOD URL 정리 및 검증 모듈."""

import re

# 치지직 VOD URL 정규식 패턴
# 예: https://chzzk.naver.com/video/15016450
CHZZK_VOD_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?chzzk\.naver\.com/video/(\d+)(?:[?#].*)?$",
    re.IGNORECASE,
)


def parse_chzzk_vod_url(raw_url: str) -> str | None:
    """사용자가 입력한 URL을 정리하고 치지직 VOD ID(videoNo)를 추출합니다.

    Args:
        raw_url: 사용자가 입력한 원본 URL 문자열.

    Returns:
        추출된 VOD ID(숫자 문자열) 또는 유효하지 않은 경우 None.
    """
    if not raw_url:
        return None

    cleaned_url = raw_url.strip()
    if not cleaned_url:
        return None

    match = CHZZK_VOD_PATTERN.match(cleaned_url)
    if not match:
        return None

    return match.group(1)
