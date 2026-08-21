from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from extraction.services import ExtractionError, ExtractionService
from pricing.services import PriceEstimateError, PriceEstimateService
from processingjob._redis_publisher import RedisProgressPublisher
from processingjob.models import (
    ProcessingJobStatus,
    ProcessingStep,
    ProcessingStepStatus,
    StampProcessingJob,
)
from recognition.services import RecognitionError, RecognitionService
from report.services import ReportError, ReportService
from research.services import ResearchError, ResearchService
from summarization.services import SummaryError, SummaryService


class ProcessingJobRunner:
    def __init__(
        self,
        publisher=None,
        extraction_service=None,
        recognition_service=None,
        research_service=None,
        pricing_service=None,
        summary_service=None,
        report_service=None,
    ):
        self.publisher = publisher or RedisProgressPublisher()
        self.extraction_service = extraction_service or ExtractionService()
        self.recognition_service = recognition_service or RecognitionService()
        self.research_service = research_service or ResearchService()
        self.pricing_service = pricing_service or PriceEstimateService()
        self.summary_service = summary_service or SummaryService()
        self.report_service = report_service or ReportService()

    def run(self, job_id: str) -> dict:
        job = StampProcessingJob.objects.select_related("stamp_image").get(
            pk=job_id
        )
        job.status = ProcessingJobStatus.PROCESSING
        job.started_at = timezone.now()
        job.error_message = ""
        job.save(
            update_fields=(
                "status", "started_at", "error_message", "updated_at"
            )
        )

        analysis = self._extract(job)
        if analysis is None:
            self._skip(
                job,
                (
                    ProcessingStep.RECOGNITION,
                    ProcessingStep.RESEARCH,
                    ProcessingStep.PRICING,
                    ProcessingStep.SUMMARY,
                    ProcessingStep.FINAL_REPORT,
                ),
                "Skipped because extraction failed.",
            )
            self._finish(job, ProcessingJobStatus.FAILED)
            return self._result(job)

        recognition = self._recognize(job, analysis)
        research = price = None
        if recognition is None:
            self._skip(
                job,
                (ProcessingStep.RESEARCH, ProcessingStep.PRICING),
                "Skipped because the stamp could not be recognized.",
            )
        else:
            research = self._research(job, recognition)
            price = self._price(job, recognition)

        summary = None
        if recognition is None:
            self._skip(
                job,
                (ProcessingStep.SUMMARY,),
                "Skipped because the stamp could not be recognized.",
            )
        else:
            summary = self._summarize(
                job, analysis, recognition, research, price
            )
        report = self._create_report(
            job, analysis, recognition, research, price, summary
        )
        final_status = (
            ProcessingJobStatus.SUCCEEDED_WITH_WARNINGS
            if job.warnings or report is None
            else ProcessingJobStatus.SUCCEEDED
        )
        self._finish(job, final_status)
        return self._result(job)

    def _extract(self, job):
        try:
            result = self.extraction_service.extract(job.stamp_image)
            self._publish_step(job, ProcessingStep.EXTRACTION,
                               ProcessingStepStatus.SUCCESSFUL, result.message)
            return result.stamp_analysis
        except ExtractionError as error:
            job.error_message = str(error)
            job.save(update_fields=("error_message", "updated_at"))
            self._publish_step(job, ProcessingStep.EXTRACTION,
                               ProcessingStepStatus.FAILED, str(error))
            return None

    def _recognize(self, job, analysis):
        try:
            result = self.recognition_service.recognize(analysis)
            if result.stamp_recognition is None:
                self._warn_step(
                    job,
                    ProcessingStep.RECOGNITION,
                    ProcessingStepStatus.SUCCESSFUL_WITH_WARNING,
                    result.message,
                )
                return None
            self._publish_step(job, ProcessingStep.RECOGNITION,
                               ProcessingStepStatus.SUCCESSFUL, result.message)
            return result.stamp_recognition
        except RecognitionError as error:
            self._warn_step(job, ProcessingStep.RECOGNITION,
                            ProcessingStepStatus.FAILED, str(error))
            return None

    def _research(self, job, recognition):
        try:
            result = self.research_service.research(recognition)
            if result.stamp_research is None:
                self._warn_step(
                    job, ProcessingStep.RESEARCH,
                    ProcessingStepStatus.SUCCESSFUL_WITH_WARNING,
                    result.message,
                )
                return None
            self._publish_step(job, ProcessingStep.RESEARCH,
                               ProcessingStepStatus.SUCCESSFUL, result.message)
            return result.stamp_research
        except ResearchError as error:
            self._warn_step(job, ProcessingStep.RESEARCH,
                            ProcessingStepStatus.FAILED,
                            str(error))
            return None

    def _price(self, job, recognition):
        try:
            result = self.pricing_service.estimate(recognition)
            if result.stamp_price_estimate is None:
                self._warn_step(
                    job, ProcessingStep.PRICING,
                    ProcessingStepStatus.SUCCESSFUL_WITH_WARNING,
                    result.message,
                )
                return None
            self._publish_step(job, ProcessingStep.PRICING,
                               ProcessingStepStatus.SUCCESSFUL, result.message)
            return result.stamp_price_estimate
        except PriceEstimateError as error:
            self._warn_step(job, ProcessingStep.PRICING,
                            ProcessingStepStatus.FAILED,
                            str(error))
            return None

    def _summarize(
        self, job, analysis, recognition, research, price
    ):
        try:
            result = self.summary_service.summarize(
                analysis, recognition, research, price
            )
            self._publish_step(
                job,
                ProcessingStep.SUMMARY,
                ProcessingStepStatus.SUCCESSFUL,
                result.message,
            )
            return result.stamp_summary
        except SummaryError as error:
            job.warnings = [
                *job.warnings,
                {"step": ProcessingStep.SUMMARY, "message": str(error)},
            ]
            job.save(update_fields=("warnings", "updated_at"))
            self._publish_step(
                job,
                ProcessingStep.SUMMARY,
                ProcessingStepStatus.FAILED,
                str(error),
            )
            return None

    def _create_report(self, job, analysis, recognition, research, price,
                       summary):
        try:
            result = self.report_service.create(
                stamp_analysis=analysis,
                stamp_recognition=recognition,
                stamp_research=research,
                stamp_price_estimate=price,
                stamp_summary=summary,
            )
            job.report = result.stamp_report
            job.save(update_fields=("report", "updated_at"))
            status = (
                ProcessingStepStatus.SUCCESSFUL_WITH_WARNING
                if job.warnings else ProcessingStepStatus.SUCCESSFUL
            )
            self._publish_step(job, ProcessingStep.FINAL_REPORT,
                               status, result.message)
            return result.stamp_report
        except ReportError as error:
            self._warn_step(job, ProcessingStep.FINAL_REPORT,
                            ProcessingStepStatus.FAILED, str(error))
            return None

    def _warn_step(self, job, step, status, message):
        job.warnings = [*job.warnings, {"step": step, "message": message}]
        job.save(update_fields=("warnings", "updated_at"))
        self._publish_step(job, step, status, message)

    def _skip(self, job, steps, message):
        for step in steps:
            self._publish_step(job, step, ProcessingStepStatus.SKIPPED, message)

    def _publish_step(self, job, step, status, message):
        job.current_step = step
        job.step_statuses = {**job.step_statuses, step: status}
        job.save(update_fields=("current_step", "step_statuses", "updated_at"))
        self.publisher.publish(job.redis_channel, {
            "step": step,
            "state": status,
        })

    def _finish(self, job, status):
        job.status = status
        job.finished_at = timezone.now()
        job.save(update_fields=("status", "finished_at", "updated_at"))
        self.publisher.publish(job.redis_channel, {
            "finished": True,
            "status": status,
        })

    @staticmethod
    def _result(job):
        return {
            "job_id": str(job.id),
            "status": job.status,
            "report_id": job.report_id,
            "step_statuses": job.step_statuses,
        }


@shared_task(name="processingjob.execute")
def execute_processing_job(job_id: str) -> dict:
    return ProcessingJobRunner().run(job_id)
