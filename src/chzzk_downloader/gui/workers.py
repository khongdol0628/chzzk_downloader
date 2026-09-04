"""비동기 백그라운드 작업자 모듈."""

from PyQt6.QtCore import QThread, pyqtSignal

from chzzk_downloader.core.api import VodApiError, VodInfo, fetch_vod_info


class VodCheckWorker(QThread):
    """VOD 정보 비동기 조회를 위한 QThread 작업자."""

    finished_success = pyqtSignal(VodInfo)
    finished_failed = pyqtSignal(str)

    def __init__(self, video_no: str, parent=None) -> None:
        super().__init__(parent)
        self.video_no = video_no

    def run(self) -> None:
        """백그라운드 스레드에서 VOD API를 호출합니다."""
        try:
            info = fetch_vod_info(self.video_no)
            self.finished_success.emit(info)
        except VodApiError as e:
            self.finished_failed.emit(str(e))
        except Exception as e:
            self.finished_failed.emit(f"예기치 못한 오류: {e}")
