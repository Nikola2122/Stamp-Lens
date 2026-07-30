from django.db import models
from django.contrib.postgres.fields import ArrayField

from recognition.models import StampRecognition


class StampResearch(models.Model):
    stamp_recognition = models.OneToOneField(
        StampRecognition,
        on_delete=models.CASCADE,
        related_name="research",
    )
    search_query = models.CharField(max_length=500)
    source_title = models.CharField(max_length=500)
    source_url = models.URLField(max_length=2000)
    description = models.TextField()
    organic_results = models.JSONField(default=list, blank=True)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.source_title


class StampResearchQA(models.Model):
    stamp_research = models.OneToOneField(
        StampResearch,
        on_delete=models.CASCADE,
        related_name="question_answers",
    )
    questions = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True,
    )
    answers = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q&A for {self.stamp_research}"
