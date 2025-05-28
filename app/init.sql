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
 intervenant_id INTEGER REFERENCES intervenants(id),
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

-- Création de la table intervenants
CREATE TABLE intervenants (
 id SERIAL PRIMARY KEY,
 intervenant VARCHAR(255) NOT NULL,
 mail VARCHAR(255) NOT NULL
);

-- Ajout des clients
INSERT INTO clients (societe)
VALUES
('Absys - Grp Angelotti'),
('AHSM'),
('ALPI 40'),
('ASSIA'),
('Beneteau'),
('Bouygues ES'),
('BPCE'),
('Bridge Bank Groupe'),
('BUTACHIMIE'),
('CA Lamballe Terre Mer'),
('CC Bievre'),
('CCI Normandie'),
('CD18'),
('CD51'),
('CD54'),
('CD60'),
('CD90'),
('CH Aix en Provence'),
('CH ALES'),
('CH Angouleme'),
('CH Arpajon'),
('CH Auch'),
('CH Avignon'),
('CH Bourges'),
('CH Cambrai'),
('CH Chateaubriant'),
('CH Cholet'),
('CH Cote Basque'),
('CH de LA FLECHE'),
('CH DES SABLES D''OLONNES - CH COTE DE LUMIERE'),
('CH Dourdan'),
('CH Draguignan'),
('CH Dreux'),
('CH Falaise'),
('CH PLAISIR'),
('CH Redon'),
('CH Saint Dizier'),
('CH Sainte Gemmes'),
('CH Soissons'),
('CH St Omer'),
('CH SUD SEINE ET MARNE 77'),
('CH Valmadon'),
('CHIC CM'),
('CHRU Nancy'),
('CHS Guillaume REGNIER'),
('CHS Savoie'),
('CHU Angers'),
('CHU Brest'),
('CHU Grenoble'),
('CHU Martinique'),
('CHU Nice'),
('CHU Rennes'),
('CIPECMA'),
('Conseil Constitutionnel'),
('Corsica Linea'),
('Cristal Habitat'),
('CUGN'),
('DIATEM'),
('EDILIANS'),
('ELSAN'),
('ENSAD'),
('EPSVE'),
('ESCP Paris'),
('Eviden'),
('Fareva'),
('FCM'),
('Fleury Michon'),
('FPV Industries'),
('GHRMSA'),
('GHT ARMOR'),
('GHT PSY - EPSM Lille'),
('GHU Paris'),
('GIMA 49'),
('Groupe CAT (DXC)'),
('Groupe Oxyane'),
('Herault Logement'),
('HERMES HTH'),
('HSTV'),
('INSERM'),
('IQERA'),
('Kermene'),
('Labeyrie'),
('LABOCEA'),
('Le Gouessant'),
('LNA'),
('M2A - Ville de Mulhouse'),
('M2A Habitat'),
('Mairie de Castanet'),
('Mairie de Colmar'),
('Mairie de Marseille'),
('Mairie Loos'),
('Mairie Menton'),
('MBDA'),
('MBT Consulting'),
('Monoprix'),
('MSPB'),
('Noreade'),
('Olive Consulting'),
('OVALT'),
('Petit Forestier'),
('Polyclinique de Courlancy'),
('Polyclinique St Privat'),
('PourTarek'),
('Rothshield'),
('Safic Alcan'),
('SDIS01'),
('SDIS60'),
('SDIS66'),
('SeaFrigo'),
('Sonepar-Intuitum'),
('SOPRA STERIA'),
('SWM'),
('Systancia'),
('Toulouse Metropole Habitat'),
('UNEOS'),
('Universite Poitiers - IRIAF'),
('Ville de Loos'),
('Ville de Saint Quentin'),
('Ville de Vannes');

-- Ajout intervenants
INSERT INTO intervenants (intervenant, mail)
VALUES
('Mounir BOUGOUFFA', 'mbougouffa@mbt-consulting.com'),
('Yannis CHAZOT', 'ychazot@mbt-consulting.com');

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