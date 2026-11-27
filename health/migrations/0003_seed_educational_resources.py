from django.db import migrations


RESOURCES = [
    {
        "title": "Uso de medicamentos: orientações",
        "topic": "Medicamentos",
        "summary": "Material informativo sobre cuidados no uso de medicamentos. Consulte a fonte e siga a prescrição e as orientações do profissional que acompanha você.",
        "kind": "article",
        "source_name": "Biblioteca Virtual em Saúde · Ministério da Saúde",
        "url": "https://bvsms.saude.gov.br/uso-de-medicamentos-orientacoes/",
        "read_minutes": 5,
    },
    {
        "title": "Hipertensão (pressão alta)",
        "topic": "Coração e circulação",
        "summary": "Página de referência do Ministério da Saúde com informações gerais sobre hipertensão e acompanhamento no SUS.",
        "kind": "article",
        "source_name": "Ministério da Saúde",
        "url": "https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/h/hipertensao",
        "read_minutes": 6,
    },
    {
        "title": "Diabetes mellitus",
        "topic": "Metabolismo",
        "summary": "Informações públicas sobre diabetes e a importância de conversar com uma equipe de saúde para acompanhamento individual.",
        "kind": "article",
        "source_name": "Ministério da Saúde",
        "url": "https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/diabetes",
        "read_minutes": 6,
    },
    {
        "title": "Vídeos e programas sobre saúde",
        "topic": "Vídeos educativos",
        "summary": "Explore materiais audiovisuais informativos produzidos pelo Canal Saúde, da Fiocruz, e pesquise assuntos de seu interesse.",
        "kind": "video",
        "source_name": "Canal Saúde · Fiocruz",
        "url": "https://www.gov.br/pt-br/servicos/obter-material-audiovisual-informativo-sobre-saude",
        "read_minutes": None,
    },
]


def seed_resources(apps, schema_editor):
    Resource = apps.get_model("health", "EducationalResource")
    for resource in RESOURCES:
        Resource.objects.get_or_create(title=resource["title"], defaults=resource)


def remove_seeded_resources(apps, schema_editor):
    Resource = apps.get_model("health", "EducationalResource")
    Resource.objects.filter(title__in=[item["title"] for item in RESOURCES]).delete()


class Migration(migrations.Migration):
    dependencies = [("health", "0002_educationalresource_healthcondition_healthprofile_and_more")]
    operations = [migrations.RunPython(seed_resources, remove_seeded_resources)]
