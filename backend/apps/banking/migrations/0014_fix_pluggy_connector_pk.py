# backend/apps/banking/migrations/XXXX_fix_pluggy_connector_pk.py
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('banking', '0013_add_deleted_status'),  # Substitua pelo nome da migration anterior
    ]

    operations = [
        # 1. Remover a primary key constraint de pluggy_id
        migrations.RunSQL(
            "ALTER TABLE pluggy_connectors DROP CONSTRAINT IF EXISTS pluggy_connectors_pkey;",
            reverse_sql="ALTER TABLE pluggy_connectors ADD CONSTRAINT pluggy_connectors_pkey PRIMARY KEY (pluggy_id);"
        ),
        
        # 2. Adicionar coluna id
        migrations.AddField(
            model_name='pluggyconnector',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
            preserve_default=False,
        ),
        
        # 3. Preencher ids para registros existentes
        migrations.RunSQL(
            "UPDATE pluggy_connectors SET id = gen_random_uuid() WHERE id IS NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # 4. Tornar id NOT NULL
        migrations.AlterField(
            model_name='pluggyconnector',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True),
        ),
        
        # 5. Alterar pluggy_id para não ser mais primary key
        migrations.AlterField(
            model_name='pluggyconnector',
            name='pluggy_id',
            field=models.IntegerField(unique=True, db_index=True, verbose_name='Pluggy ID'),
        ),
        
        # 6. Adicionar nova primary key constraint
        migrations.RunSQL(
            "ALTER TABLE pluggy_connectors ADD CONSTRAINT pluggy_connectors_pkey PRIMARY KEY (id);",
            reverse_sql="ALTER TABLE pluggy_connectors DROP CONSTRAINT pluggy_connectors_pkey;"
        ),
    ]