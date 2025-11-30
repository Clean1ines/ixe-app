from datetime import datetime

from src.domain.value_objects.scraping.subject_info import SubjectInfo
from src.domain.value_objects.scraping.scraping_result import ScrapingResult

from .data_structures import LoopResult


class ResultComposer:
    def compose_final_result(
        self,
        subject_info: SubjectInfo,
        loop_result: LoopResult,
        start_time: datetime,
        end_time: datetime
    ) -> ScrapingResult:
        page_results_dict = [
            {
                "page_number": pr.page_number,
                "problems_found": pr.problems_found,
                "problems_saved": pr.problems_saved,
                "assets_downloaded": pr.assets_downloaded,
                "duration_seconds": pr.page_duration_seconds,
                "error": pr.error
            }
            for pr in loop_result.page_results
        ]

        success = len(loop_result.errors) == 0

        return ScrapingResult(
            subject_name=subject_info.official_name,
            success=success,
            total_pages=len(loop_result.page_results),
            total_problems_found=loop_result.total_problems_found,
            total_problems_saved=loop_result.total_problems_saved,
            page_results=page_results_dict,
            errors=loop_result.errors,
            start_time=start_time,
            end_time=end_time,
            metadata={
                "assets_downloaded": loop_result.total_assets_downloaded,
                "last_processed_page": loop_result.last_processed_page
            }
        )
