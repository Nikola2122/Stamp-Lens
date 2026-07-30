from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="stampresearch",
            old_name="article_title",
            new_name="source_title",
        ),
        migrations.RenameField(
            model_name="stampresearch",
            old_name="article_url",
            new_name="source_url",
        ),
        migrations.AddField(
            model_name="stampresearch",
            name="organic_results",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="stampresearch",
            name="related_questions",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
