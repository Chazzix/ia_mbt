from sqlalchemy import create_engine, MetaData, text
from eralchemy import render_er

# Connexion à une base SQLite en mémoire
engine = create_engine('sqlite:///:memory:')
metadata = MetaData()

# Charger et exécuter le SQL
with engine.connect() as conn:
    with open('.\\01-BDD_MBT\\init.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        for statement in sql.split(';'):
            if statement.strip():
                conn.execute(text(statement))

# Générer le diagramme
render_er(metadata, '.\\02-Diagramme\\erd_diagram.png')