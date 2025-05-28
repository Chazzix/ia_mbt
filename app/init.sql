-- Création de la table clients
CREATE TABLE clients (
 id SERIAL PRIMARY KEY,
 societe VARCHAR(255) NOT NULL
);

-- Création de la table contact
CREATE TABLE contact (
 id SERIAL PRIMARY KEY,
 nom VARCHAR(255) NOT NULL,
 prenom VARCHAR(255) NOT NULL,
 mail VARCHAR(255) NOT NULL,
 telephone VARCHAR(20),
 client_id INTEGER REFERENCES clients(id)
);

-- Création de la table bon_intervention
CREATE TABLE bon_intervention (
 id SERIAL PRIMARY KEY,
 intervenant VARCHAR(255) NOT NULL,
 client_id INTEGER REFERENCES clients(id),
 contact_id INTEGER REFERENCES contact(id),
 duree_inter VARCHAR(50),
 date_deb DATE,
 date_fin DATE,
 obj_presta TEXT,
 contenu_intervention TEXT,
 num_mission VARCHAR(50),
 date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger de cohérence
CREATE OR REPLACE FUNCTION check_contact_client_coherence()
RETURNS TRIGGER AS $$
BEGIN
 IF (SELECT client_id FROM contact WHERE id = NEW.contact_id) != NEW.client_id THEN
 RAISE EXCEPTION 'Le contact % n''appartient pas au client %', NEW.contact_id, NEW.client_id;
 END IF;
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_contact_client_coherence
BEFORE INSERT OR UPDATE ON bon_intervention
FOR EACH ROW EXECUTE FUNCTION check_contact_client_coherence();

-- Vue
CREATE VIEW bon_intervention_view AS
SELECT 
 bi.id,
 bi.intervenant,
 c.societe,
 ct.nom AS nom_contact,
 ct.mail AS mail_contact,
 bi.duree_inter,
 bi.date_deb,
 bi.date_fin,
 bi.obj_presta,
 bi.contenu_intervention,
 bi.num_mission,
 bi.date_creation
FROM 
 bon_intervention bi
JOIN 
 clients c ON bi.client_id = c.id
JOIN 
 contact ct ON bi.contact_id = ct.id;