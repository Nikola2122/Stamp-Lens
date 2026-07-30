import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0002_extend_stamp_research"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="stampresearch",
            name="related_questions",
        ),
        migrations.CreateModel(
            name="StampResearchQA",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "questions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "answers",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "stamp_research",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="question_answers",
                        to="research.stampresearch",
                    ),
                ),
            ],
        ),
    ]
