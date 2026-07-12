# ComptaCopilot AI

Copilote IA pour cabinets comptables — import de documents, propositions
d'écritures en partie double, TVA, bilan, analyse financière. Le comptable
valide toujours avant tout enregistrement.

## Structure du monorepo

```
comptacopilot-ai/
├── frontend/     # React + TypeScript + Vite + Tailwind — déployé sur Vercel
├── backend/      # FastAPI + SQLAlchemy + PostgreSQL — déployé sur Railway/Render
└── docker-compose.yml   # Postgres, Redis, MinIO pour le développement local
```

**Point important sur l'architecture de déploiement** : Vercel héberge très
bien un frontend statique/React, mais ne fait pas tourner un backend Python
avec une base de données PostgreSQL persistante et des tâches de fond (OCR,
appels LLM). Le frontend et le backend sont donc déployés sur deux
plateformes différentes, qui communiquent par HTTP :

```
┌─────────────────────┐         HTTPS          ┌──────────────────────────┐
│  Vercel              │ ─────────────────────▶ │  Railway / Render          │
│  frontend/ (React)   │                        │  backend/ (FastAPI)        │
└─────────────────────┘                         │  + PostgreSQL + Redis      │
                                                  └──────────────────────────┘
```

---

## 1. Développement local

### Prérequis
- Node.js 20+
- Python 3.12+
- Docker (pour Postgres/Redis/MinIO)

### Backend

```bash
cd backend
cp .env.example .env          # ajuste les valeurs si besoin
python3 -m venv .venv
source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt

cd ..
docker compose up -d          # lance Postgres, Redis, MinIO

cd backend
uvicorn app.main:app --reload --port 8000
```

L'API est disponible sur `http://localhost:8000`, la documentation interactive
sur `http://localhost:8000/docs`.

Pour lancer les tests (dont ceux, déjà écrits et vérifiés, du module
exercices comptables) :

```bash
cd backend/app
python3 -m unittest tests.unit.test_exercice_domain -v
```

### Frontend

```bash
cd frontend
cp .env.example .env.local    # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

Le site est disponible sur `http://localhost:5173`.

---

## 2. Publier le projet sur GitHub

```bash
cd comptacopilot-ai
git init
git add .
git commit -m "Initialisation du monorepo ComptaCopilot AI"
git branch -M main
git remote add origin https://github.com/TON-COMPTE/comptacopilot-ai.git
git push -u origin main
```

Crée d'abord le dépôt vide sur [github.com/new](https://github.com/new) (sans
README ni .gitignore, le projet en a déjà) avant de faire le `push`.

---

## 3. Déployer le frontend sur Vercel

1. Va sur [vercel.com/new](https://vercel.com/new), connecte-toi avec GitHub.
2. Importe le dépôt `comptacopilot-ai`.
3. **Étape importante** : dans la configuration du projet, renseigne
   **Root Directory = `frontend`** (Vercel doit savoir que le projet Vite se
   trouve dans le sous-dossier `frontend/`, pas à la racine du repo).
4. Vercel détecte automatiquement Vite (`npm run build`, sortie dans `dist/`).
5. Dans **Environment Variables**, ajoute :
   - `VITE_API_URL` = l'URL de ton backend une fois déployé (étape suivante).
6. Clique sur **Deploy**.

Chaque `git push` sur `main` redéploie automatiquement le frontend.

---

## 4. Déployer le backend (Railway ou Render)

Vercel ne convient pas ici (pas de PostgreSQL managé persistant adapté, pas de
tâches de fond longues pour l'OCR/LLM). Deux options simples et proches en
prix :

### Option Railway

1. [railway.app/new](https://railway.app/new) → **Deploy from GitHub repo** →
   sélectionne `comptacopilot-ai`.
2. Railway propose d'ajouter un service **PostgreSQL** et un service
   **Redis** en un clic depuis le même projet — fais-le, ça configure les
   variables `DATABASE_URL` / `REDIS_URL` automatiquement.
3. Pour le service backend : **Root Directory = `backend`**, Railway détecte
   le `Dockerfile` et construit l'image automatiquement.
4. Renseigne les variables d'environnement du fichier `.env.example` dans
   l'onglet **Variables** du service (au minimum `JWT_SECRET_KEY`, et les
   URLs de connexion générées par Railway pour Postgres/Redis).
5. Railway fournit une URL publique (`https://xxx.up.railway.app`) — c'est
   celle à renseigner comme `VITE_API_URL` côté Vercel, et à ajouter dans
   `CORS_ALLOWED_ORIGINS` côté backend.

### Option Render

1. [render.com/new](https://render.com/new) → **Web Service** → connecte le
   dépôt GitHub.
2. Root Directory : `backend`. Render détecte le `Dockerfile`.
3. Ajoute une base **PostgreSQL** depuis le dashboard Render (bouton
   **New → PostgreSQL**), copie l'URL de connexion fournie dans la variable
   `DATABASE_URL` du service backend.
4. Ajoute les autres variables d'environnement comme ci-dessus.

Dans les deux cas, une fois le backend en ligne, retourne dans les
**Environment Variables** du projet Vercel pour y mettre la vraie URL du
backend, puis redéploie le frontend (`Deployments → Redeploy`).

---

## 5. Où en est le code aujourd'hui

- **Fait et testé** : Auth/multi-tenant, Exercices & reprise de dossier,
  Import/OCR, IA comptable, Écritures en partie double, Anomalies/doublons,
  Balance/Bilan/Compte de résultat, TVA, Rapprochement bancaire, Assistant
  conversationnel multi-agents, **Moteur PCG structuré** (recherche/validation/
  suggestion), **Moteur de mémoire et d'apprentissage des habitudes**
  (le système retient qu'un tiers est toujours comptabilisé sur tel compte),
  **Moteur de confiance unifié** (combine OCR + LLM + mémoire), **Orchestrateur
  multi-agents** (routage testé vers l'agent spécialisé pertinent), **Prévisions
  étendues** (TVA, IS estimé, simulation embauche/investissement) — 184 tests
  unitaires passants sur la logique métier pure de chaque module.

- **Interfaces réelles posées mais non activées** (nécessitent de vraies clés/
  contrats externes pour fonctionner, structure du code déjà prête) :
  - OCR : Azure Document Intelligence et Mistral OCR, en plus de Tesseract/
    Google Vision déjà actifs (`app/services/ocr_service.py`) ;
  - Open banking : connecteurs Bridge et Powens implémentant une interface
    commune (`app/services/banking/`), branchés sur le même moteur de
    rapprochement que l'import CSV manuel.

- **Ce qui reste explicitement hors périmètre, par choix assumé** :
  - RAG juridique (PCG officiel complet, BOFiP, CGI, jurisprudence) — non
    fabriqué : inventer des citations fiscales sans corpus source réel serait
    dangereux. Nécessite un vrai corpus ingéré + base vectorielle avant d'être
    codé sérieusement ;
  - Base de données en graphe (Neo4j) — une projection graphe légère existe
    depuis les données relationnelles (`GET /clients/{id}/graphe`), suffisante
    tant que le volume ne justifie pas une vraie base graphe dédiée ;
  - Export/synchronisation vers Sage, Cegid, Quadratus — le FEC en sortie
    serait la première brique à ajouter ;
  - Génération de la liasse fiscale complète (au-delà de la TVA et de
    l'estimation d'IS indicative).
- **Squelette posé, à compléter** : Auth (JWT émis mais pas encore
  d'endpoint d'inscription/connexion réel), modèles Organisation/Client/
  Écriture (structure minimale pour que le reste tienne debout), toutes les
  pages frontend (routées et stylées, mais affichent des données de
  substitution en attendant que les endpoints correspondants existent).
- **Pas encore commencé** : Import/OCR, IA comptable, TVA, anomalies, bilan,
  analyse financière — cf. le plan de développement MVP du document
  d'architecture pour l'ordre recommandé.

---

## 6. Prochaine étape suggérée

Coder l'étape 1 du plan MVP (Auth réelle : inscription, connexion, gestion
des utilisateurs par organisation) pour que le frontend (déjà câblé pour
appeler `/api/v1/auth/login`) puisse réellement s'y connecter.
