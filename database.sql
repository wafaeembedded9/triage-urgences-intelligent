CREATE DATABASE medicaal_triage_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medicaal_triage_ai;

-- ========================================
-- 1. TABLE DES UTILISATEURS (médecins et infirmieers)
-- ========================================
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    role ENUM('medecin', 'infirmier') NOT NULL,
    service VARCHAR(100) DEFAULT 'Urgences',
    numero_licence VARCHAR(50) NULL,
    actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    derniere_connexion TIMESTAMP NULL,
         
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_actif (actif)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 2. TABLE DES PATIENTS
-- ========================================
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE DEFAULT '1990-01-01',
    sexe ENUM('M', 'F') NOT NULL,
    telephone VARCHAR(20) DEFAULT '',
    numero_dossier VARCHAR(50) UNIQUE NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
         
    INDEX idx_nom_prenom (nom, prenom),
    INDEX idx_numero_dossier (numero_dossier),
    INDEX idx_sexe (sexe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 3. TABLE DES TRIAGES (Structure FINALE et CORRECTE)
-- ========================================
CREATE TABLE triages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    utilisateur_id INT NOT NULL,
         
    -- Données démographiques du patient
    age INT NOT NULL,
    sexe_code INT NOT NULL, -- 0=F, 1=M
         
    -- Données médicales principales (NOMS CORRECTS selon app.py)
    chest_pain_type INT NOT NULL,
    blood_pressure INT NOT NULL,  -- CORRECT (pas blood_pressur dans BD)
    cholesterol INT NOT NULL,
    max_heart_rate INT NOT NULL,
    exercise_angina INT NOT NULL,
    plasma_glucose FLOAT NOT NULL,
    skin_thickness FLOAT NOT NULL,
    insulin FLOAT NOT NULL,
    bmi FLOAT NOT NULL,
    diabetes_pedigree FLOAT NOT NULL,
    hypertension INT NOT NULL,
    heart_disease INT NOT NULL,
    residence_type VARCHAR(50) NOT NULL,
    smoking_status VARCHAR(50) NOT NULL,
         
    -- Résultats du triage IA
    niveau_triage ENUM('red', 'orange', 'yellow', 'green') NOT NULL,
    score_urgence FLOAT NOT NULL,
    probabilites JSON,
    priorite INT DEFAULT 999,
         
    -- Gestion du flux de patients
    statut ENUM('en_attente', 'en_cours', 'termine') DEFAULT 'en_attente',
    medecin_charge_id INT NULL,
         
    -- Horodatage complet
    date_triage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_prise_en_charge TIMESTAMP NULL,
    date_fin_prise_en_charge TIMESTAMP NULL,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
         
    -- Clés étrangères avec contraintes
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (medecin_charge_id) REFERENCES utilisateurs(id) ON DELETE SET NULL,
         
    -- Index pour les performances (TRÈS IMPORTANT)
    INDEX idx_niveau_triage (niveau_triage),
    INDEX idx_statut (statut),
    INDEX idx_date_triage (date_triage),
    INDEX idx_priorite_score (priorite, score_urgence),
    INDEX idx_patient_id (patient_id),
    INDEX idx_utilisateur_id (utilisateur_id),
    INDEX idx_medecin_charge (medecin_charge_id),
    INDEX idx_composite_attente (statut, priorite, score_urgence, date_triage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 4. INSERTION DES UTILISATEURS DE TEST
-- ========================================

-- Mot de passe: 123456 (hashé avec Werkzeug)
INSERT INTO utilisateurs (username, email, password_hash, nom, prenom, role, service, numero_licence, actif) 
VALUES 
-- Médecin senior
('dr_alami', 'medecin@hopital.ma', 'pbkdf2:sha256:260000$8vTd5QoG1X2w4vbJ$2f77e4b5fa2c8b7e0b6b5d5a95e5c8f9a1e2d3c4b5a6f7e8d9c0b1a2e3f4d5c6', 'Alami', 'Dr Ahmed', 'medecin', 'Urgences', 'MD2024001', TRUE),

-- Infirmière expérimentée
('inf_bennani', 'infirmier@hopital.ma', 'pbkdf2:sha256:260000$8vTd5QoG1X2w4vbJ$2f77e4b5fa2c8b7e0b6b5d5a95e5c8f9a1e2d3c4b5a6f7e8d9c0b1a2e3f4d5c6', 'Bennani', 'Fatima', 'infirmier', 'Urgences', 'INF2024001', TRUE),

-- Compte de test général
('testuser', 'test@hopital.ma', 'pbkdf2:sha256:260000$8vTd5QoG1X2w4vbJ$2f77e4b5fa2c8b7e0b6b5d5a95e5c8f9a1e2d3c4b5a6f7e8d9c0b1a2e3f4d5c6', 'Test', 'User', 'medecin', 'Urgences', 'TEST001', TRUE),

-- Médecin junior pour les tests
('dr_idrissi', 'medecin2@hopital.ma', 'pbkdf2:sha256:260000$8vTd5QoG1X2w4vbJ$2f77e4b5fa2c8b7e0b6b5d5a95e5c8f9a1e2d3c4b5a6f7e8d9c0b1a2e3f4d5c6', 'Idrissi', 'Dr Youssef', 'medecin', 'Urgences', 'MD2024002', TRUE),

-- Infirmier pour les tests
('inf_tazi', 'infirmier2@hopital.ma', 'pbkdf2:sha256:260000$8vTd5QoG1X2w4vbJ$2f77e4b5fa2c8b7e0b6b5d5a95e5c8f9a1e2d3c4b5a6f7e8d9c0b1a2e3f4d5c6', 'Tazi', 'Omar', 'infirmier', 'Urgences', 'INF2024002', TRUE);

-- ========================================
-- 5. INSERTION DES PATIENTS DE TEST
-- ========================================
INSERT INTO patients (nom, prenom, date_naissance, sexe, telephone, numero_dossier) VALUES
('Alami', 'Mohamed', '1980-05-15', 'M', '0612345678', 'P202501001'),
('Bennani', 'Khadija', '1975-08-22', 'F', '0623456789', 'P202501002'),
('El Ouafi', 'Ahmed', '1990-12-10', 'M', '0634567890', 'P202501003'),
('Tazi', 'Aicha', '1985-03-18', 'F', '0645678901', 'P202501004'),
('Chakir', 'Omar', '1992-07-25', 'M', '0656789012', 'P202501005'),
('Idrissi', 'Zineb', '1988-11-30', 'F', '0667890123', 'P202501006'),
('Radi', 'Youssef', '1995-04-12', 'M', '0678901234', 'P202501007'),
('Senhaji', 'Nadia', '1987-09-28', 'F', '0689012345', 'P202501008'),
('Fassi', 'Hassan', '1983-06-14', 'M', '0690123456', 'P202501009'),
('Lahlou', 'Samira', '1991-01-03', 'F', '0601234567', 'P202501010');

-- ========================================
-- 6. INSERTION DE DONNÉES DE TEST RÉALISTES
-- ========================================

-- Triages de test avec des données médicales réalistes
INSERT INTO triages (
    patient_id, utilisateur_id, age, sexe_code, chest_pain_type, blood_pressure, 
    cholesterol, max_heart_rate, exercise_angina, plasma_glucose, skin_thickness, 
    insulin, bmi, diabetes_pedigree, hypertension, heart_disease, residence_type, 
    smoking_status, niveau_triage, score_urgence, priorite, statut, date_triage
) VALUES 
-- Cas critique - Homme 65 ans, douleur thoracique sévère
(1, 1, 65, 1, 3, 180, 280, 120, 1, 140, 25, 85, 28.5, 0.8, 1, 1, 'Urban', 'smokes', 'red', 95, 1, 'en_attente', '2025-01-29 08:30:00'),

-- Cas urgent - Femme 55 ans, hypertension sévère  
(2, 2, 55, 0, 2, 170, 260, 140, 1, 160, 30, 95, 31.2, 1.2, 1, 0, 'Urban', 'formerly smoked', 'orange', 82, 2, 'en_attente', '2025-01-29 09:15:00'),

-- Cas modéré - Homme jeune avec facteurs de risque
(3, 1, 35, 1, 1, 140, 220, 160, 0, 110, 20, 70, 26.8, 0.4, 0, 0, 'Rural', 'never smoked', 'yellow', 58, 3, 'en_cours', '2025-01-29 10:00:00'),

-- Cas stable - Femme jeune, contrôle de routine
(4, 3, 28, 0, 0, 120, 180, 175, 0, 95, 18, 60, 23.5, 0.3, 0, 0, 'Urban', 'never smoked', 'green', 25, 4, 'termine', '2025-01-29 11:30:00'),

-- Cas urgent - Homme âgé, diabète décompensé
(5, 2, 72, 1, 2, 160, 240, 110, 1, 280, 35, 150, 29.8, 1.5, 1, 1, 'Urban', 'formerly smoked', 'orange', 78, 2, 'en_attente', '2025-01-29 12:45:00'),

-- Cas critique - Femme, AVC suspecté
(6, 4, 68, 0, 3, 200, 300, 90, 1, 180, 40, 120, 32.1, 1.8, 1, 1, 'Rural', 'never smoked', 'red', 92, 1, 'en_cours', '2025-01-29 13:20:00'),

-- Cas modéré - Homme d'âge moyen
(7, 1, 45, 1, 1, 135, 200, 155, 0, 105, 22, 75, 25.9, 0.6, 0, 0, 'Urban', 'smokes', 'yellow', 52, 3, 'termine', '2025-01-29 14:10:00'),

-- Cas stable - Jeune femme
(8, 3, 25, 0, 0, 110, 170, 180, 0, 85, 15, 45, 21.8, 0.2, 0, 0, 'Urban', 'never smoked', 'green', 20, 4, 'termine', '2025-01-29 15:00:00'),

-- Cas urgent - Homme fumeur avec douleur thoracique
(9, 2, 58, 1, 2, 155, 250, 125, 1, 130, 28, 88, 27.6, 0.9, 1, 0, 'Rural', 'smokes', 'orange', 75, 2, 'en_attente', '2025-01-29 16:30:00'),

-- Cas modéré - Femme avec hypertension légère
(10, 4, 42, 0, 1, 145, 210, 150, 0, 115, 25, 80, 26.3, 0.5, 1, 0, 'Urban', 'formerly smoked', 'yellow', 48, 3, 'en_cours', '2025-01-29 17:15:00');

-- ========================================
-- 7. MISE À JOUR DES PRISES EN CHARGE
-- ========================================

-- Assigner des médecins aux patients en cours/terminés
UPDATE triages SET medecin_charge_id = 1, date_prise_en_charge = DATE_ADD(date_triage, INTERVAL 10 MINUTE) 
WHERE id IN (3, 6, 7, 10);

UPDATE triages SET medecin_charge_id = 4, date_prise_en_charge = DATE_ADD(date_triage, INTERVAL 5 MINUTE)
WHERE id IN (4, 8);

-- Marquer les cas terminés avec date de fin
UPDATE triages SET date_fin_prise_en_charge = DATE_ADD(date_prise_en_charge, INTERVAL 45 MINUTE)
WHERE statut = 'termine';

-- ========================================
-- 8. VÉRIFICATION DES DONNÉES
-- ========================================

-- Afficher le résumé des données insérées
SELECT 'UTILISATEURS' as TableName, COUNT(*) as Count FROM utilisateurs
UNION ALL
SELECT 'PATIENTS', COUNT(*) FROM patients  
UNION ALL
SELECT 'TRIAGES', COUNT(*) FROM triages;

-- Afficher la distribution des niveaux de triage
SELECT niveau_triage, COUNT(*) as count, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM triages), 1) as pourcentage
FROM triages 
GROUP BY niveau_triage 
ORDER BY FIELD(niveau_triage, 'red', 'orange', 'yellow', 'green');

-- Afficher les statuts
SELECT statut, COUNT(*) as count FROM triages GROUP BY statut;

-- ========================================
-- 9. PROCÉDURES STOCKÉES UTILES (OPTIONNEL)
-- ========================================

DELIMITER //

-- Procédure pour obtenir les statistiques d'un utilisateur
CREATE PROCEDURE GetUserStats(IN user_id INT)
BEGIN
    SELECT 
        COUNT(*) as total_triages,
        COUNT(CASE WHEN niveau_triage = 'red' THEN 1 END) as critiques,
        COUNT(CASE WHEN niveau_triage = 'orange' THEN 1 END) as urgents,
        COUNT(CASE WHEN niveau_triage = 'yellow' THEN 1 END) as moderes,
        COUNT(CASE WHEN niveau_triage = 'green' THEN 1 END) as stables,
        AVG(score_urgence) as score_moyen,
        MIN(date_triage) as premier_triage,
        MAX(date_triage) as dernier_triage
    FROM triages 
    WHERE utilisateur_id = user_id;
END //

-- Procédure pour obtenir la file d'attente prioritaire
CREATE PROCEDURE GetPriorityQueue()
BEGIN
    SELECT 
        t.id as triage_id,
        t.niveau_triage, 
        t.date_triage, 
        t.score_urgence,
        t.priorite,
        p.nom, 
        p.prenom,
        p.sexe,
        t.age,
        u.nom as evaluateur_nom,
        u.prenom as evaluateur_prenom,
        u.role as evaluateur_role,
        t.statut
    FROM triages t
    JOIN patients p ON t.patient_id = p.id
    JOIN utilisateurs u ON t.utilisateur_id = u.id
    WHERE t.statut = 'en_attente'
    ORDER BY t.priorite ASC, t.score_urgence DESC, t.date_triage ASC;
END //

DELIMITER ;

-- Message de confirmation
SELECT '✅ BASE DE DONNÉES CRÉÉE AVEC SUCCÈS!' as Status,
       'Utilisez les comptes test pour vous connecter' as Instructions,
       'medecin@hopital.ma / 123456 ou infirmier@hopital.ma / 123456' as Credentials;
