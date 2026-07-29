import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("extraction", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stampanalysis",
            name="stamp_image",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="analyses",
                to="ingestion.stampimage",
            ),
        ),
    ]
