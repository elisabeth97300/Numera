# Déploiement sur Vercel — ComptaCopilot AI

Ce guide couvre uniquement le déploiement du **frontend** sur Vercel. Le
backend (FastAPI + PostgreSQL) ne peut pas tourner sur Vercel — il a besoin
d'un hébergement séparé (Railway ou Render, détaillés en fin de document).

---

## 1. Pré-requis

- Le dépôt `comptacopilot-ai` poussé sur GitHub (voir `README.md` à la racine si ce n'est pas déjà fait).
- Un compte sur [vercel.com](https://vercel.com) (connexion possible directement avec GitHub).
- Le backend déjà déployé quelque part, ou en tout cas son URL prévue — Vercel a besoin de savoir où envoyer les appels API.

---

## 2. Import du projet sur Vercel

1. Va sur **[vercel.com/new](https://vercel.com/new)**.
2. Clique sur **Import Git Repository** et sélectionne `comptacopilot-ai`.
3. Vercel affiche un écran de configuration. Renseigne exactement ceci :

| Champ | Valeur |
|---|---|
| **Framework Preset** | Vite (détecté automatiquement) |
| **Root Directory** | `frontend` ⚠️ obligatoire — sinon Vercel cherche un `package.json` à la racine du repo et ne le trouve pas |
| **Build Command** | `npm run build` (valeur par défaut, à laisser telle quelle) |
| **Output Directory** | `dist` (valeur par défaut, à laisser telle quelle) |
| **Install Command** | `npm install` (valeur par défaut) |

4. Clique sur **Environment Variables** et ajoute :

| Nom | Valeur | Exemple |
|---|---|---|
| `VITE_API_URL` | l'URL publique de ton backend | `https://comptacopilot-api.up.railway.app` |

Si le backend n'est pas encore déployé, mets une valeur temporaire
(`http://localhost:8000`) — tu la corrigeras à l'étape 5 une fois le backend
en ligne.

5. Clique sur **Deploy**.

En général moins d'une minute plus tard, Vercel donne une URL du type
`https://comptacopilot-ai.vercel.app`.

---

## 3. Vérifier que ça fonctionne

Ouvre l'URL fournie par Vercel. Tu dois voir la page de connexion
(`/login`). Si tu as une erreur de build, regarde l'onglet **Deployments →
[ton déploiement] → Build Logs** dans Vercel — les erreurs les plus
fréquentes :

- **`Root Directory` mal configuré** → erreur `no package.json found`. Va dans
  **Settings → General → Root Directory** et corrige en `frontend`.
- **Erreur TypeScript au build** → le build local (`npm run build` dans
  `frontend/`) doit passer avant de pousser ; teste-le en local si Vercel échoue.

---

## 4. Redéploiement automatique

Une fois le projet importé, **chaque `git push` sur la branche `main`
redéploie automatiquement** le frontend — rien d'autre à faire. Les pushs sur
d'autres branches créent des **Preview Deployments** (URL de test séparée),
utile pour tester une modification avant de la fusionner dans `main`.

---

## 5. Connecter le vrai backend une fois déployé

Une fois ton backend en ligne (Railway/Render, voir section suivante) :

1. Dans Vercel : **Settings → Environment Variables**.
2. Modifie `VITE_API_URL` avec la vraie URL du backend.
3. Va dans **Deployments**, clique sur les `...` du dernier déploiement,
   puis **Redeploy** (nécessaire : une variable d'environnement modifiée ne
   s'applique qu'au prochain build, elle n'est pas injectée à chaud).

Pense aussi à ajouter l'URL Vercel (`https://comptacopilot-ai.vercel.app`)
dans la variable `CORS_ALLOWED_ORIGINS` du **backend**, sinon le navigateur
bloquera les appels API (erreur CORS visible dans la console du navigateur).

---

## 6. Nom de domaine personnalisé (optionnel)

**Settings → Domains** dans le projet Vercel → ajoute ton domaine (ex.
`app.comptacopilot.fr`) → Vercel indique les enregistrements DNS à créer chez
ton registrar (en général un simple `CNAME`). La certification HTTPS est
automatique une fois le DNS propagé (quelques minutes à quelques heures).

---

## 7. Déployer le backend (rappel — pas sur Vercel)

Le backend a besoin de PostgreSQL, Redis, et de tâches de fond (OCR, appel
LLM) : Vercel ne le permet pas nativement. Deux options simples :

### Railway

1. [railway.app/new](https://railway.app/new) → **Deploy from GitHub repo** → `comptacopilot-ai`.
2. **Root Directory** du service : `backend` (Railway détecte le `Dockerfile` automatiquement).
3. Ajoute un service **PostgreSQL** et un service **Redis** depuis le même projet Railway (un clic chacun) — les variables `DATABASE_URL` / `REDIS_URL` sont injectées automatiquement.
4. Dans **Variables** du service backend, ajoute au minimum :
   - `JWT_SECRET_KEY` (une vraie valeur aléatoire, jamais celle du `.env.example`)
   - `CORS_ALLOWED_ORIGINS` = `["https://comptacopilot-ai.vercel.app"]`
   - `LLM_API_KEY` si l'assistant IA / la génération de propositions doivent fonctionner
5. Railway fournit une URL publique (`https://xxx.up.railway.app`) — c'est celle à mettre dans `VITE_API_URL` côté Vercel (étape 5 ci-dessus).

### Render

1. [render.com/new](https://render.com/new) → **Web Service** → connecte le dépôt GitHub.
2. **Root Directory** : `backend`. Render détecte le `Dockerfile`.
3. **New → PostgreSQL** pour créer la base ; copie l'URL de connexion fournie dans `DATABASE_URL` du service backend.
4. Mêmes variables d'environnement que pour Railway ci-dessus.

---

## Résumé visuel

```
GitHub (comptacopilot-ai)
   │
   ├── Root Directory: frontend  ──▶  Vercel  ──▶  https://comptacopilot-ai.vercel.app
   │                                              (VITE_API_URL pointe vers le backend)
   │
   └── Root Directory: backend   ──▶  Railway/Render  ──▶  https://xxx.up.railway.app
                                       + PostgreSQL + Redis
                                       (CORS_ALLOWED_ORIGINS pointe vers Vercel)
```
