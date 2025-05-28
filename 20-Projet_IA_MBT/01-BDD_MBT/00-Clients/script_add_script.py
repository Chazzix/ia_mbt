input_file = "Nom_Dossier_Client.txt"
output_file = "Nom_Dossier_Client_formate.txt"

# Essaye les encodages pour lecture
for encoding in ["utf-16", "latin1", "utf-8"]:
    try:
        with open(input_file, "r", encoding=encoding) as f:
            lines = f.readlines()
        break
    except UnicodeDecodeError:
        continue
else:
    raise Exception("Impossible de lire le fichier avec les encodages connus.")

# Formater chaque ligne
formatted_lines = []
for line in lines:
    clean = line.strip()
    if clean:
        formatted_lines.append(f"('{clean}'),")

# Écriture dans un nouveau fichier
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(formatted_lines))

print(f"[✓] Fichier formaté généré : {output_file}")
