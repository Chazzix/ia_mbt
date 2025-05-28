import psycopg2
import os

def test_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        print("✅ Connexion à la base réussie !")

        cur = conn.cursor()
        cur.execute("SELECT * FROM clients LIMIT 5;")
        rows = cur.fetchall()
        print("📦 Données récupérées :")
        for row in rows:
            print(row)

        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Erreur lors de la connexion à la base :", e)

if __name__ == "__main__":
    test_db_connection()