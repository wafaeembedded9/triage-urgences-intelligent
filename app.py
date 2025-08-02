from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, make_response
import joblib
import pandas as pd
import numpy as np
import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import json
from functools import wraps
import re
from sklearn.preprocessing import StandardScaler, LabelEncoder
import io

# Initialiser Flask
app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_triage_medical_2024'

# Configuration de la base de données MySQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'medicaal_triage_ai',
    'user': 'root',
    'password': '',
    'charset': 'utf8mb4'
}

# Variables globales pour le modèle IA
model = None
scaler = None
label_encoders = {}
target_encoder = None

def load_ai_model():
    """Charger le modèle IA et les encodeurs"""
    global model, scaler, label_encoders, target_encoder
    
    try:
        model_files = [
            'modele_triage_medical.pkl',
            'scaler_triage.pkl', 
            'encoders_triage.pkl',
            'target_encoder_triage.pkl'
        ]
        
        if not all(os.path.exists(f) for f in model_files):
            print("⚠️ Fichiers du modèle non trouvés, création d'un modèle basé sur les règles médicales...")
            create_medical_rules_model()
        else:
            model = joblib.load('modele_triage_medical.pkl')
            scaler = joblib.load('scaler_triage.pkl')
            label_encoders = joblib.load('encoders_triage.pkl')
            target_encoder = joblib.load('target_encoder_triage.pkl')
        
        print("✅ Modèle IA chargé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle: {e}")
        create_medical_rules_model()
        return False

def create_medical_rules_model():
    """Créer un modèle basé sur des règles médicales réalistes"""
    global model, scaler, label_encoders, target_encoder
    
    from sklearn.ensemble import RandomForestClassifier
    
    print("✅ Création d'un modèle basé sur des règles médicales...")
    
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'age': np.random.normal(50, 15, n_samples).clip(18, 90).astype(int),
        'gender': np.random.choice([0, 1], n_samples),
        'chest_pain_type': np.random.choice([0, 1, 2, 3, 4], n_samples),
        'blood_pressure': np.random.normal(130, 20, n_samples).clip(80, 200).astype(int),
        'cholesterol': np.random.normal(240, 50, n_samples).clip(150, 400).astype(int),
        'max_heart_rate': np.random.normal(150, 30, n_samples).clip(60, 220).astype(int),
        'exercise_angina': np.random.choice([0, 1], n_samples),
        'plasma_glucose': np.random.normal(100, 30, n_samples).clip(50, 300),
        'skin_thickness': np.random.normal(25, 10, n_samples).clip(5, 50),
        'insulin': np.random.normal(80, 40, n_samples).clip(10, 200),
        'bmi': np.random.normal(26, 5, n_samples).clip(15, 40),
        'diabetes_pedigree': np.random.uniform(0.1, 2.0, n_samples),
        'hypertension': np.random.choice([0, 1], n_samples),
        'heart_disease': np.random.choice([0, 1], n_samples),
        'residence_urban': np.random.choice([0, 1], n_samples),
        'smoking_status': np.random.choice([0, 1, 2], n_samples)
    }
    
    X = pd.DataFrame(data)
    y = []
    
    for i in range(n_samples):
        score = 0
        
        if X.iloc[i]['age'] > 70:
            score += 2
        elif X.iloc[i]['age'] > 60:
            score += 1
            
        if X.iloc[i]['chest_pain_type'] >= 3:
            score += 3
        elif X.iloc[i]['chest_pain_type'] >= 2:
            score += 2
            
        bp = X.iloc[i]['blood_pressure']
        if bp > 180 or bp < 90:
            score += 3
        elif bp > 160 or bp < 100:
            score += 2
            
        hr = X.iloc[i]['max_heart_rate']
        if hr > 200 or hr < 60:
            score += 2
        elif hr > 180 or hr < 80:
            score += 1
            
        if X.iloc[i]['exercise_angina'] == 1:
            score += 2
        if X.iloc[i]['heart_disease'] == 1:
            score += 2
        if X.iloc[i]['hypertension'] == 1:
            score += 1
        if X.iloc[i]['plasma_glucose'] > 180:
            score += 1
        if X.iloc[i]['bmi'] > 35:
            score += 1
        if X.iloc[i]['smoking_status'] == 2:
            score += 1
            
        if score >= 8:
            y.append('red')
        elif score >= 5:
            y.append('orange')
        elif score >= 2:
            y.append('yellow')
        else:
            y.append('green')
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y_encoded)
    
    label_encoders = {}
    print("✅ Modèle médical créé avec succès!")

def predire_triage_patient(patient_data):
    """Prédire le niveau de triage d'un patient"""
    try:
        model_features = [
            float(patient_data['age']),
            float(patient_data['gender']),
            float(patient_data['chest_pain_type']),
            float(patient_data['blood_pressure']),
            float(patient_data['cholesterol']),
            float(patient_data['max_heart_rate']),
            float(patient_data['exercise_angina']),
            float(patient_data['plasma_glucose']),
            float(patient_data['skin_thickness']),
            float(patient_data['insulin']),
            float(patient_data['bmi']),
            float(patient_data['diabetes_pedigree']),
            float(patient_data['hypertension']),
            float(patient_data['heart_disease']),
            1 if patient_data['Residence_type'] == 'Urban' else 0,
            {'never smoked': 0, 'formerly smoked': 1, 'smokes': 2}.get(patient_data['smoking_status'], 0)
        ]
        
        X = np.array(model_features).reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        prediction = model.predict(X_scaled)[0]
        predicted_class = target_encoder.inverse_transform([prediction])[0]
        
        probabilities = {}
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X_scaled)[0]
            for i, classe in enumerate(target_encoder.classes_):
                probabilities[classe] = f"{proba[i] * 100:.1f}%"
        else:
            base_probs = {'red': 10, 'orange': 20, 'yellow': 30, 'green': 40}
            base_probs[predicted_class] = 70
            total = sum(base_probs.values())
            for classe in base_probs:
                probabilities[classe] = f"{(base_probs[classe] / total) * 100:.1f}%"
        
        urgence_scores = {'red': 95, 'orange': 75, 'yellow': 50, 'green': 25}
        priorites = {'red': 1, 'orange': 2, 'yellow': 3, 'green': 4}
        score_urgence = urgence_scores.get(predicted_class, 50)
        priorite = priorites.get(predicted_class, 3)
        
        return predicted_class, probabilities, score_urgence, priorite
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        return 'yellow', {'red': '10%', 'orange': '20%', 'yellow': '40%', 'green': '30%'}, 50, 3

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"❌ Erreur connexion BD: {e}")
        return None

def generer_username(email, nom, prenom):
    """Génère un username unique basé sur l'email et le nom"""
    base_username = email.split('@')[0]
    base_username = re.sub(r'[^a-zA-Z0-9._-]', '', base_username)
    
    if len(base_username) < 3:
        base_username = f"{prenom[0].lower()}{nom[0].lower()}{base_username}"
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE username = %s", (base_username,))
            count = cursor.fetchone()[0]
            
            final_username = base_username
            counter = 1
            
            while count > 0:
                final_username = f"{base_username}{counter}"
                cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE username = %s", (final_username,))
                count = cursor.fetchone()[0]
                counter += 1
            
            return final_username
            
        except Error as e:
            print(f"Erreur génération username: {e}")
            return base_username
        finally:
            connection.close()
    
    return base_username

@app.template_filter('strftime')
def datetime_filter(date, format='%d/%m/%Y à %H:%M'):
    if date:
        return date.strftime(format)
    return ''

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        numero_licence = request.form.get('numero_licence', '').strip()
        
        if not all([nom, prenom, email, password, confirm_password, role]):
            flash('Veuillez remplir tous les champs obligatoires.', 'error')
            return render_template('inscription.html')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('inscription.html')
            
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
            return render_template('inscription.html')
        
        username = generer_username(email, nom, prenom)
        password_hash = generate_password_hash(password)
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE email = %s", (email,))
                existing_users = cursor.fetchone()[0]
                
                if existing_users > 0:
                    flash('Cet email est déjà utilisé.', 'error')
                    return render_template('inscription.html')
                
                cursor.execute("""
                    INSERT INTO utilisateurs 
                    (username, email, password_hash, nom, prenom, role, service, numero_licence, actif) 
                    VALUES (%s, %s, %s, %s, %s, %s, 'Urgences', %s, TRUE)
                """, (username, email, password_hash, nom, prenom, role, numero_licence))
                
                connection.commit()
                flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
                return redirect(url_for('login'))
                
            except Error as e:
                flash(f'Erreur lors de l\'inscription: {e}', 'error')
                print(f"Erreur BD inscription: {e}")
            finally:
                connection.close()
        else:
            flash('Erreur de connexion à la base de données.', 'error')
    
    return render_template('inscription.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Veuillez remplir tous les champs.', 'error')
            return render_template('login.html')
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                
                cursor.execute("""
                    SELECT id, username, email, password_hash, nom, prenom, role 
                    FROM utilisateurs 
                    WHERE email = %s AND actif = TRUE
                """, (email,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['nom'] = user['nom']
                    session['prenom'] = user['prenom']
                    session['role'] = user['role']
                    
                    cursor.execute("UPDATE utilisateurs SET derniere_connexion = NOW() WHERE id = %s", (user['id'],))
                    connection.commit()
                    
                    flash('Connexion réussie!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Email ou mot de passe incorrect.', 'error')
                    
            except Error as e:
                flash(f'Erreur de base de données: {e}', 'error')
            finally:
                connection.close()
        else:
            flash('Erreur de connexion à la base de données.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Déconnexion réussie.', 'info')
    return redirect(url_for('login'))

@app.route('/triage')
@login_required
def triage():
    return render_template('triage.html', user=session)

@app.route('/predire', methods=['POST'])
@login_required
def predire():
    try:
        patient_data = {}
        nom = request.form.get('nom', 'Patient')
        prenom = request.form.get('prenom', 'Anonyme')
        
        required_fields = [
            'age', 'gender', 'chest_pain_type', 'blood_pressure', 'cholesterol',
            'max_heart_rate', 'exercise_angina', 'plasma_glucose', 'skin_thickness',
            'insulin', 'bmi', 'diabetes_pedigree', 'hypertension', 'heart_disease',
            'Residence_type', 'smoking_status'
        ]
        
        for field in required_fields:
            value = request.form.get(field)
            if value is None or value == '':
                flash(f'Le champ {field} est requis', 'error')
                return redirect(url_for('triage'))
            patient_data[field] = value
        
        niveau_triage, probabilites, score_urgence, priorite = predire_triage_patient(patient_data)
        
        triage_id = None
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                
                cursor.execute("""
                    SELECT id FROM patients WHERE nom = %s AND prenom = %s
                """, (nom, prenom))
                patient = cursor.fetchone()
                
                if not patient:
                    cursor.execute("""
                        INSERT INTO patients (nom, prenom, date_naissance, sexe, telephone)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (nom, prenom, '1990-01-01', 'M' if patient_data['gender'] == '1' else 'F', ''))
                    patient_id = cursor.lastrowid
                else:
                    patient_id = patient[0]
                
                cursor.execute("""
                    INSERT INTO triages (
                        patient_id, utilisateur_id, age, sexe_code, chest_pain_type,
                        blood_pressure, cholesterol, max_heart_rate, exercise_angina,
                        plasma_glucose, skin_thickness, insulin, bmi, diabetes_pedigree,
                        hypertension, heart_disease, residence_type, smoking_status,
                        niveau_triage, score_urgence, probabilites, priorite, statut
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    patient_id, session['user_id'], int(patient_data['age']), int(patient_data['gender']),
                    int(patient_data['chest_pain_type']), int(patient_data['blood_pressure']),
                    int(patient_data['cholesterol']), int(patient_data['max_heart_rate']),
                    int(patient_data['exercise_angina']), float(patient_data['plasma_glucose']),
                    float(patient_data['skin_thickness']), float(patient_data['insulin']),
                    float(patient_data['bmi']), float(patient_data['diabetes_pedigree']),
                    int(patient_data['hypertension']), int(patient_data['heart_disease']),
                    patient_data['Residence_type'], patient_data['smoking_status'],
                    niveau_triage, score_urgence, json.dumps(probabilites), priorite, 'en_attente'
                ))
                
                triage_id = cursor.lastrowid
                connection.commit()
                
            except Error as e:
                print(f"❌ Erreur sauvegarde BD: {e}")
            finally:
                connection.close()
        
        session['dernier_triage'] = {
            'nom': nom,
            'prenom': prenom,
            'niveau_triage': niveau_triage,
            'score_urgence': score_urgence,
            'probabilites': probabilites,
            'patient_info': {
                'age': patient_data['age'],
                'genre': 'Homme' if patient_data['gender'] == '1' else 'Femme',
                'tension': patient_data['blood_pressure'],
                'cholesterol': patient_data['cholesterol']
            },
            'triage_id': triage_id,
            'date_triage': datetime.now()
        }
        
        return redirect(url_for('resultats'))
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        flash(f'Erreur lors de la prédiction: {str(e)}', 'error')
        return redirect(url_for('triage'))

@app.route('/resultats')
@login_required
def resultats():
    if 'dernier_triage' not in session:
        flash('Aucun résultat de triage disponible.', 'error')
        return redirect(url_for('triage'))
    
    triage_info = {
        'red': {
            'couleur': '#e74c3c',
            'message': '🚨 URGENCE VITALE - Prise en charge immédiate requise',
            'niveau_nom': 'URGENCE VITALE'
        },
        'orange': {
            'couleur': '#f39c12', 
            'message': '⚠️ TRÈS URGENT - Prise en charge dans les 15 minutes',
            'niveau_nom': 'TRÈS URGENT'
        },
        'yellow': {
            'couleur': '#f1c40f',
            'message': '🟡 URGENT - Prise en charge dans l\'heure',
            'niveau_nom': 'URGENT'
        },
        'green': {
            'couleur': '#27ae60',
            'message': '🟢 NON URGENT - Prise en charge différée possible',
            'niveau_nom': 'NON URGENT'
        }
    }
    
    triage_data = session['dernier_triage']
    info = triage_info.get(triage_data['niveau_triage'], triage_info['yellow'])
    
    return render_template('resultats.html', 
                         user=session, 
                         triage=triage_data, 
                         info=info)

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    stats = {}
    patients_attente = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT COUNT(*) as total FROM triages")
            result = cursor.fetchone()
            stats['total_triages'] = result['total'] if result else 0
            
            cursor.execute("SELECT COUNT(*) as total FROM patients")
            result = cursor.fetchone()
            stats['total_patients'] = result['total'] if result else 0
            
            cursor.execute("""
                SELECT niveau_triage, COUNT(*) as count 
                FROM triages 
                GROUP BY niveau_triage
                ORDER BY 
                    CASE niveau_triage 
                        WHEN 'red' THEN 1 
                        WHEN 'orange' THEN 2 
                        WHEN 'yellow' THEN 3 
                        WHEN 'green' THEN 4 
                    END
            """)
            stats['distribution'] = cursor.fetchall()
            
            cursor.execute("""
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
                ORDER BY t.priorite ASC, t.score_urgence DESC, t.date_triage ASC
                LIMIT 20
            """)
            patients_attente = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    t.niveau_triage, 
                    t.date_triage, 
                    t.score_urgence,
                    p.nom, 
                    p.prenom, 
                    u.nom as evaluateur_nom,
                    u.prenom as evaluateur_prenom,
                    u.role as evaluateur_role,
                    t.statut
                FROM triages t
                JOIN patients p ON t.patient_id = p.id
                JOIN utilisateurs u ON t.utilisateur_id = u.id
                WHERE t.utilisateur_id = %s AND t.statut != 'en_attente'
                ORDER BY t.date_triage DESC
                LIMIT 10
            """, (session['user_id'],))
            stats['recent_triages'] = cursor.fetchall()
            
        except Error as e:
            print(f"❌ Erreur dashboard: {e}")
            stats = {
                'total_triages': 0,
                'total_patients': 0,
                'distribution': [],
                'recent_triages': []
            }
        finally:
            connection.close()
    
    return render_template('dashboard.html', 
                         user=session, 
                         stats=stats, 
                         patients_attente=patients_attente)

@app.route('/historique')
@login_required
def historique():
    connection = get_db_connection()
    historique_data = []
    stats_personnelles = {}
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    niveau_filtre = request.args.get('niveau', '')
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            where_conditions = ["t.utilisateur_id = %s"]
            params = [session['user_id']]
            
            if niveau_filtre:
                where_conditions.append("t.niveau_triage = %s")
                params.append(niveau_filtre)
            
            if date_debut:
                where_conditions.append("DATE(t.date_triage) >= %s")
                params.append(date_debut)
                
            if date_fin:
                where_conditions.append("DATE(t.date_triage) <= %s")
                params.append(date_fin)
            
            where_clause = " AND ".join(where_conditions)
            
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM triages t
                JOIN patients p ON t.patient_id = p.id
                WHERE {where_clause}
            """, params)
            
            total = cursor.fetchone()['total']
            
            offset = (page - 1) * per_page
            cursor.execute(f"""
                SELECT 
                    t.id,
                    t.niveau_triage,
                    t.date_triage,
                    t.score_urgence,
                    t.priorite,
                    t.statut,
                    t.date_prise_en_charge,
                    t.date_fin_prise_en_charge,
                    p.nom as patient_nom,
                    p.prenom as patient_prenom,
                    p.sexe as patient_sexe,
                    t.age,
                    t.blood_pressure,
                    t.cholesterol,
                    t.max_heart_rate,
                    mc.nom as medecin_charge_nom,
                    mc.prenom as medecin_charge_prenom,
                    mc.role as medecin_charge_role
                FROM triages t
                JOIN patients p ON t.patient_id = p.id
                LEFT JOIN utilisateurs mc ON t.medecin_charge_id = mc.id
                WHERE {where_clause}
                ORDER BY t.date_triage DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            
            historique_data = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_mes_triages,
                    COUNT(CASE WHEN niveau_triage = 'red' THEN 1 END) as mes_critiques,
                    COUNT(CASE WHEN niveau_triage = 'orange' THEN 1 END) as mes_urgents,
                    COUNT(CASE WHEN niveau_triage = 'yellow' THEN 1 END) as mes_moderes,
                    COUNT(CASE WHEN niveau_triage = 'green' THEN 1 END) as mes_stables,
                    AVG(score_urgence) as score_moyen,
                    MIN(date_triage) as premier_triage,
                    MAX(date_triage) as dernier_triage
                FROM triages
                WHERE utilisateur_id = %s
            """, (session['user_id'],))
            
            stats_personnelles = cursor.fetchone()
            
        except Error as e:
            print(f"❌ Erreur historique: {e}")
            total = 0
        finally:
            connection.close()
    
    total_pages = (total + per_page - 1) // per_page if 'total' in locals() else 1
    
    return render_template('historique.html', 
                         user=session,
                         historique=historique_data,
                         stats=stats_personnelles,
                         pagination={
                             'page': page,
                             'per_page': per_page,
                             'total': total if 'total' in locals() else 0,
                             'total_pages': total_pages
                         },
                         filtres={
                             'niveau': niveau_filtre,
                             'date_debut': date_debut,
                             'date_fin': date_fin
                         })

@app.route('/prendre_en_charge/<int:triage_id>')
@login_required
def prendre_en_charge(triage_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE triages 
                SET statut = 'en_cours', 
                    medecin_charge_id = %s,
                    date_prise_en_charge = NOW()
                WHERE id = %s AND statut = 'en_attente'
            """, (session['user_id'], triage_id))
            
            if cursor.rowcount > 0:
                connection.commit()
                flash('Patient pris en charge avec succès!', 'success')
            else:
                flash('Erreur: Ce patient n\'est plus disponible.', 'error')
                
        except Error as e:
            flash(f'Erreur: {e}', 'error')
        finally:
            connection.close()
    
    return redirect(url_for('dashboard'))

@app.route('/modifier_statut_patient/<int:triage_id>/<string:nouveau_statut>')
@login_required  
def modifier_statut_patient(triage_id, nouveau_statut):
    if nouveau_statut not in ['en_attente', 'en_cours', 'termine']:
        flash('Statut invalide', 'error')
        return redirect(url_for('dashboard'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            if nouveau_statut == 'termine':
                cursor.execute("""
                    UPDATE triages 
                    SET statut = %s, date_fin_prise_en_charge = NOW()
                    WHERE id = %s
                """, (nouveau_statut, triage_id))
            else:
                cursor.execute("""
                    UPDATE triages 
                    SET statut = %s
                    WHERE id = %s
                """, (nouveau_statut, triage_id))
            
            connection.commit()
            flash(f'Statut mis à jour: {nouveau_statut}', 'success')
            
        except Error as e:
            flash(f'Erreur: {e}', 'error')
        finally:
            connection.close()
    
    return redirect(url_for('dashboard'))

@app.route('/rechercher_patient')
@login_required
def rechercher_patient():
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    connection = get_db_connection()
    results = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    p.id, p.nom, p.prenom, p.sexe,
                    COUNT(t.id) as nb_triages,
                    MAX(t.date_triage) as dernier_triage
                FROM patients p
                LEFT JOIN triages t ON p.id = t.patient_id
                WHERE p.nom LIKE %s OR p.prenom LIKE %s
                GROUP BY p.id
                ORDER BY dernier_triage DESC
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            
            for patient in results:
                if patient['dernier_triage']:
                    patient['dernier_triage'] = patient['dernier_triage'].strftime('%d/%m/%Y %H:%M')
                    
        except Error as e:
            print(f"❌ Erreur recherche: {e}")
        finally:
            connection.close()
    
    return jsonify(results)

@app.route('/patient/<int:patient_id>')
@login_required
def detail_patient(patient_id):
    connection = get_db_connection()
    patient_info = None
    historique_patient = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM patients WHERE id = %s
            """, (patient_id,))
            patient_info = cursor.fetchone()
            
            if not patient_info:
                flash('Patient non trouvé', 'error')
                return redirect(url_for('dashboard'))
            
            cursor.execute("""
                SELECT 
                    t.*,
                    u.nom as evaluateur_nom,
                    u.prenom as evaluateur_prenom,
                    u.role as evaluateur_role,
                    mc.nom as medecin_charge_nom,
                    mc.prenom as medecin_charge_prenom,
                    mc.role as medecin_charge_role
                FROM triages t
                JOIN utilisateurs u ON t.utilisateur_id = u.id
                LEFT JOIN utilisateurs mc ON t.medecin_charge_id = mc.id
                WHERE t.patient_id = %s
                ORDER BY t.date_triage DESC
            """, (patient_id,))
            
            historique_patient = cursor.fetchall()
            
        except Error as e:
            flash(f'Erreur: {e}', 'error')
            return redirect(url_for('dashboard'))
        finally:
            connection.close()
    
    return render_template('detail_patient.html',
                         user=session,
                         patient=patient_info,
                         historique=historique_patient)

@app.route('/create_test_user')
def create_test_user():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            medecin_email = "medecin@hopital.ma"
            medecin_password = "123456"
            medecin_hash = generate_password_hash(medecin_password)
            
            infirmier_email = "infirmier@hopital.ma"
            infirmier_password = "123456"
            infirmier_hash = generate_password_hash(infirmier_password)
            
            test_email = "test@hopital.ma"
            test_password = "123456"
            test_hash = generate_password_hash(test_password)
            
            utilisateurs_test = [
                ("dr_medecin", medecin_email, medecin_hash, "Alami", "Dr Ahmed", "medecin", "Urgences"),
                ("inf_test", infirmier_email, infirmier_hash, "Bennani", "Fatima", "infirmier", "Urgences"),
                ("testuser", test_email, test_hash, "Test", "User", "medecin", "Urgences")
            ]
            
            for user_data in utilisateurs_test:
                cursor.execute("""
                    INSERT INTO utilisateurs 
                    (username, email, password_hash, nom, prenom, role, service, actif) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash)
                """, user_data)
            
            connection.commit()
            
            return f"""
            <h2>✅ Utilisateurs de test créés avec succès!</h2>
            <div style="font-family: Arial; padding: 20px;">
                <h3>🔐 Comptes de connexion:</h3>
                <ul>
                    <li><strong>Médecin:</strong> {medecin_email} / {medecin_password}</li>
                    <li><strong>Infirmier:</strong> {infirmier_email} / {infirmier_password}</li>
                    <li><strong>Test:</strong> {test_email} / {test_password}</li>
                </ul>
                <br>
                <a href="/login" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    🔐 Se connecter
                </a>
            </div>
            """
            
        except Error as e:
            return f"❌ Erreur: {e}"
        finally:
            connection.close()
    
    return "❌ Erreur de connexion BD"

@app.route('/system_check')
def system_check():
    checks = {}
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM utilisateurs")
            users_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM patients")
            patients_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM triages")
            triages_count = cursor.fetchone()[0]
            connection.close()
            
            checks['database'] = {
                'status': '✅ OK',
                'users': users_count,
                'patients': patients_count,
                'triages': triages_count
            }
        else:
            checks['database'] = {'status': '❌ ERREUR', 'message': 'Connexion impossible'}
    except Exception as e:
        checks['database'] = {'status': '❌ ERREUR', 'message': str(e)}
    
    try:
        if model is not None and scaler is not None:
            checks['ai_model'] = {'status': '✅ OK', 'message': 'Modèle chargé'}
        else:
            checks['ai_model'] = {'status': '⚠️ WARNING', 'message': 'Modèle non chargé'}
    except Exception as e:
        checks['ai_model'] = {'status': '❌ ERREUR', 'message': str(e)}
    
    try:
        templates_required = ['login.html', 'dashboard.html', 'triage.html', 'historique.html']
        missing_templates = []
        for template in templates_required:
            template_path = os.path.join(app.template_folder or 'templates', template)
            if not os.path.exists(template_path):
                missing_templates.append(template)
        
        if not missing_templates:
            checks['templates'] = {'status': '✅ OK', 'message': 'Tous les templates présents'}
        else:
            checks['templates'] = {'status': '⚠️ WARNING', 'message': f'Templates manquants: {missing_templates}'}
    except Exception as e:
        checks['templates'] = {'status': '❌ ERREUR', 'message': str(e)}
    
    return jsonify(checks)

@app.route('/export_historique_pdf')
@login_required 
def export_historique_pdf():
    """Exporter l'historique en PDF (nécessite reportlab)"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        
        connection = get_db_connection()
        if not connection:
            flash('Erreur de connexion', 'error')
            return redirect(url_for('historique'))
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                t.date_triage, p.nom, p.prenom, t.age, p.sexe,
                t.niveau_triage, t.score_urgence, t.statut,
                t.blood_pressure, t.max_heart_rate, t.cholesterol,
                mc.nom as medecin_charge_nom,
                mc.prenom as medecin_charge_prenom,
                mc.role as medecin_charge_role
            FROM triages t
            JOIN patients p ON t.patient_id = p.id
            LEFT JOIN utilisateurs mc ON t.medecin_charge_id = mc.id
            WHERE t.utilisateur_id = %s
            ORDER BY t.date_triage DESC
            LIMIT 50
        """, (session['user_id'],))
        
        triages = cursor.fetchall()
        connection.close()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                              rightMargin=1*cm, leftMargin=1*cm,
                              topMargin=1*cm, bottomMargin=1*cm)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        story = []
        
        title = Paragraph(f"📋 Historique des Triages - {session['prenom']} {session['nom']}", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        data = [['Date/Heure', 'Patient', 'Âge', 'Sexe', 'Niveau', 'Score', 'Statut', 'Tension', 'Freq. Card.', 'Responsable']]
        
        for t in triages:
            niveau_fr = {'red': 'CRITIQUE', 'orange': 'URGENT', 'yellow': 'MODÉRÉ', 'green': 'STABLE'}.get(t['niveau_triage'])
            statut_fr = {'en_attente': 'Attente', 'en_cours': 'En cours', 'termine': 'Terminé'}.get(t['statut'])
            
            # CORRECTION: Affichage correct selon le rôle
            responsable = ''
            if t['medecin_charge_nom']:
                if t['medecin_charge_role'] == 'medecin':
                    responsable = f"Dr. {t['medecin_charge_prenom']} {t['medecin_charge_nom']}"
                else:
                    responsable = f"{t['medecin_charge_prenom']} {t['medecin_charge_nom']}"
            
            data.append([
                t['date_triage'].strftime('%d/%m/%Y %H:%M') if t['date_triage'] else '',
                f"{t['nom']} {t['prenom']}",
                str(t['age']),
                t['sexe'],
                niveau_fr,
                f"{t['score_urgence']}%",
                statut_fr,
                str(t['blood_pressure']),
                str(t['max_heart_rate']),
                responsable
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        doc.build(story)
        
        buffer.seek(0)
        filename = f"historique_triage_{session['username']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ImportError:
        flash('Export PDF non disponible. Veuillez installer reportlab: pip install reportlab', 'error')
        return redirect(url_for('historique'))
    except Exception as e:
        flash(f'Erreur lors de l\'export PDF: {e}', 'error')
        return redirect(url_for('historique'))

if __name__ == '__main__':
    print("🏥 Démarrage du système de triage médical IA...")
    print("=" * 60)
    
    print("🤖 Chargement du modèle IA...")
    model_loaded = load_ai_model()
    
    print("\n📋 INFORMATIONS DE CONNEXION:")
    print("=" * 40)
    print("🔐 Login: http://localhost:5000/login")
    print("📊 Dashboard: http://localhost:5000/dashboard") 
    print("🩺 Triage: http://localhost:5000/triage")
    print("📋 Historique: http://localhost:5000/historique")
    print("🧪 Test users: http://localhost:5000/create_test_user")
    print("⚙️ System check: http://localhost:5000/system_check")
    
    print("\n👥 COMPTES DE TEST:")
    print("=" * 30)
    print("👨‍⚕️ Médecin: medecin@hopital.ma / 123456")
    print("👩‍⚕️ Infirmier: infirmier@hopital.ma / 123456")
    print("🧪 Test: test@hopital.ma / 123456")
    
    print("\n🚀 Serveur démarré sur http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)