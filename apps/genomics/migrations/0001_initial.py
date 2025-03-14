# Generated by Django 4.2 on 2025-03-06 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GenomicData",
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
                ("variants", models.TextField()),
                ("sequenced_samples", models.IntegerField(default=0)),
                ("risk_alleles", models.TextField()),
                ("date_analyzed", models.DateTimeField(auto_now_add=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="genomic_data",
                        to="users.userprofile",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Genomic Data",
            },
        ),
        migrations.AddIndex(
            model_name="genomicdata",
            index=models.Index(
                fields=["patient"], name="genomics_ge_patient_e0e463_idx"
            ),
        ),
    ]
