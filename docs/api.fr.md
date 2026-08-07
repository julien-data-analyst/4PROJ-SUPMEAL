# API

[🇬🇧 English](api.md) | 🇫🇷 Français

## Sommaire

- [Vue d'ensemble](#vue-densemble)
  - [URL de base](#url-de-base)
  - [Authentification](#authentification)
  - [Pagination](#pagination)
  - [Format des erreurs](#format-des-erreurs)
  - [Documentation interactive](#documentation-interactive)
- [1. Comptes & authentification (`users`)](#1-comptes--authentification-users)
- [2. Cookbooks (`cookbooks`)](#2-cookbooks-cookbooks)
- [3. Recettes, tags & ingrédients (`recipes`)](#3-recettes-tags--ingrédients-recipes)
- [4. Planning (`planning`)](#4-planning-planning)
- [5. Messagerie (`messaging`)](#5-messagerie-messaging)

Ce document liste chaque route API exposée par le backend, regroupée par app
Django. Pour chaque route sont détaillés : les codes de statut de réponse
attendus, ses paramètres (chemin, query et corps de requête), et le workflow
attendu côté appelant. Pour les tables de la base de données sous-jacente,
voir [`docs/database.md`](database.fr.md) ; pour le flux de connexion OAuth
Microsoft en particulier, voir [`docs/oauth.md`](oauth.fr.md).

---

## Vue d'ensemble

### URL de base

Toutes les routes ci-dessous sont relatives à `/api/`. En local (via
`docker-compose.dev.yml`), cela donne
`http://localhost:${BACKEND_PORT}/api/`.

### Authentification

L'API utilise des jetons JWT de type bearer (`djangorestframework-simplejwt`).
Une fois qu'un appelant dispose d'un token `access` (obtenu via
inscription/connexion/OAuth), celui-ci doit être envoyé sur chaque requête
authentifiée :

```
Authorization: Bearer <access>
```

- **Durée de vie de l'access token :** 60 minutes (`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME`).
- **Durée de vie du refresh token :** 7 jours (`SIMPLE_JWT.REFRESH_TOKEN_LIFETIME`).
- Quand l'access token expire, il faut échanger le `refresh` token contre un
  nouveau via
  [`POST /api/users/token/refresh/`](#post-apiuserstokenrefresh).
- [`POST /api/users/logout/`](#post-apiuserslogout) blackliste **à la fois**
  le refresh token et l'access token ayant servi à l'appeler - voir
  `users.authentication.BlacklistAwareJWTAuthentication` - de sorte qu'aucun
  des deux ne peut être réutilisé ensuite, même si l'access token n'a pas
  encore expiré naturellement.
- Les routes sont soit `AllowAny` (aucun token requis), soit
  `IsAuthenticated` (n'importe quel access token valide, non blacklisté),
  soit soumises à une restriction supplémentaire (réservé au staff,
  réservé au propriétaire de l'objet, basé sur le rôle dans le cookbook) -
  chaque route ci-dessous précise laquelle s'applique.

### Pagination

Les endpoints de liste qui gèrent la pagination (`DefaultPagination`, 10
éléments par page par défaut, 100 maximum via `?page_size=`) enveloppent
leurs résultats dans ce format :

```json
{
  "count": 42,
  "total_pages": 5,
  "current_page": 1,
  "next": "http://localhost:8000/api/recipes/?page=2",
  "previous": null,
  "results": [ /* ... */ ]
}
```

Tous les endpoints de liste ne sont pas paginés - `GET /api/tags/` et
`GET /api/ingredients/` renvoient un simple tableau JSON, car aucune classe
de pagination n'est configurée sur ces deux viewsets.

### Format des erreurs

Les erreurs de validation (`400 Bad Request`) proviennent des serializers
DRF, sous l'une de ces deux formes :

```json
{ "detail": "Un message unique, lisible par un humain." }
```

ou une map d'erreurs par champ :

```json
{ "field_name": ["This field is required."] }
```

`401 Unauthorized` est renvoyé quand l'authentification est absente,
invalide ou expirée (entièrement géré par DRF/Simple JWT, pas par le code
applicatif). `403 Forbidden` est renvoyé quand l'authentification a réussi
mais que l'appelant n'a pas le rôle/la permission requise. `404 Not Found`
est utilisé - volontairement, à plusieurs endroits ci-dessous - à la place
de `403` quand révéler qu'un objet existe divulguerait une information que
l'appelant ne devrait pas avoir (par exemple un cookbook dont il n'est pas
membre).

### Documentation interactive

Le schéma documenté manuellement ci-dessous est également généré
automatiquement à partir du même code (via `drf-spectacular`) :

- Schéma OpenAPI brut : `GET /api/schema/`
- Interface Swagger : `GET /api/docs/`

---

## 1. Comptes & authentification (`users`)

### `POST /api/users/register/`

Crée un nouveau compte local (username/email/mot de passe) et connecte
immédiatement l'utilisateur.

**Auth :** `AllowAny`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Compte créé ; la réponse inclut l'utilisateur et une paire de tokens. |
| `400 Bad Request` | Champ manquant/invalide, username ou email déjà pris, ou mot de passe rejeté par les validateurs Django (trop court, trop courant, trop proche du username, entièrement numérique). |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `username` | string | oui | Unique. |
| `email` | string | oui | Unique, doit être une adresse email valide. |
| `password` | string | oui | Écriture seule, validé par les validateurs de mot de passe Django. |
| `first_name` | string | non | |
| `last_name` | string | non | |
| `profile_icon` | string | non | Vaut `""` par défaut si omis. |

**Workflow**

1. Le client envoie le formulaire d'inscription en `POST`.
2. Le serializer valide l'unicité de `username`/`email` et la robustesse du mot de passe.
3. Le serveur hache le mot de passe (`set_password`) et crée la ligne `User`.
4. Le serveur émet une paire de JWT (`RefreshToken.for_user`), exactement comme une connexion classique.
5. Réponse : `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`.
6. Le client stocke `access`/`refresh` et joint `Authorization: Bearer <access>` aux appels suivants.

---

### `POST /api/users/login/`

Authentifie avec email + mot de passe.

**Auth :** `AllowAny`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Identifiants valides ; la réponse inclut l'utilisateur et une paire de tokens. |
| `400 Bad Request` | Email inconnu, mot de passe erroné, compte désactivé, ou compte OAuth-only sans mot de passe local - les trois cas renvoient le même message générique pour qu'un appelant ne puisse pas distinguer lequel s'applique. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `email` | string | oui | |
| `password` | string | oui | Écriture seule. |

**Workflow**

1. Le client envoie `{ email, password }` en `POST`.
2. Le serveur recherche le `User` par email, puis appelle `authenticate()` de Django avec le `username` de cet utilisateur et le mot de passe fourni.
3. En cas de succès, une nouvelle paire de JWT est émise (les tokens précédents, s'il y en a, ne sont **pas** révoqués par une nouvelle connexion).
4. Réponse : `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`.

---

### `POST /api/users/logout/`

Révoque la session courante : blackliste le refresh token fourni **ainsi
que** l'access token ayant servi à authentifier cet appel.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Les deux tokens sont blacklistés. `{ "detail": "Logged out successfully." }` |
| `400 Bad Request` | `refresh` manquant, malformé, expiré, déjà blacklisté, ou appartenant à un autre utilisateur que celui qui authentifie la requête. |
| `401 Unauthorized` | Access token absent/invalide/expiré/déjà blacklisté. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `refresh` | string | oui | Le refresh token émis avec l'access token actuellement utilisé. |

**Workflow**

1. Le client envoie `Authorization: Bearer <access>` et `{ "refresh": "<refresh>" }` dans le corps.
2. Le serveur parse `refresh` en tant que `RefreshToken` ; un échec de décodage/expiration/blacklist déjà en place renvoie immédiatement `400`.
3. Le serveur vérifie que la claim `user_id` du refresh token correspond à `request.user.id` - sinon `400` (impossible de déconnecter la session de quelqu'un d'autre).
4. Le serveur blackliste le refresh token (`RefreshToken.blacklist()` - comportement standard de Simple JWT).
5. Le serveur blackliste également l'**access token** utilisé pour cette requête (`request.auth`), en créant manuellement les lignes `OutstandingToken`/`BlacklistedToken` que Simple JWT ne crée pas par défaut pour les access tokens.
6. À partir de ce moment : rafraîchir avec ce `refresh` token → `401` sur `/token/refresh/` ; réutiliser cet `access` token sur une route authentifiée quelconque → `401` (imposé par `BlacklistAwareJWTAuthentication`).

---

### `POST /api/users/oauth/microsoft/`

Échange un `code` d'autorisation Microsoft contre un profil Graph, puis
connecte l'utilisateur (création du compte à la première connexion). Voir
[`docs/oauth.md`](oauth.fr.md) pour le diagramme de séquence complet et les
étapes d'intégration côté frontend.

**Auth :** `AllowAny`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Connexion/inscription réussie ; la réponse inclut l'utilisateur et une paire de tokens. |
| `400 Bad Request` | `code` manquant, Microsoft a rejeté l'échange (code expiré/déjà utilisé, mauvais `redirect_uri`, consentement révoqué), ou le profil Graph n'a ni `mail` ni `userPrincipalName`. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `code` | string | oui | Code d'autorisation obtenu en redirigeant le navigateur vers l'endpoint `/oauth2/v2.0/authorize` de Microsoft. |

**Workflow**

1. Le frontend redirige le navigateur vers Microsoft pour l'authentification/le consentement.
2. Microsoft redirige vers l'URL de callback du frontend avec `?code=...`.
3. Le frontend envoie `{ code }` en `POST` à cet endpoint.
4. Le backend échange `code` contre un access token Graph via MSAL (côté serveur uniquement - utilise `AZURE_CLIENT_SECRET`, jamais exposé au frontend).
5. Le backend récupère le profil Graph (`givenName`, `surname`, `mail`/`userPrincipalName`) et vérifie si le compte a une photo.
6. Le backend récupère ou crée le `User` (apparié par email) et sa ligne `OAuthUser(provider="microsoft")` liée.
7. Réponse : `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`, format identique à `/login/`.

---

### `POST /api/users/token/refresh/`

Échange un refresh token contre un nouvel access token. Vue Simple JWT
intégrée (`TokenRefreshView`), partagée par toutes les méthodes de connexion
(mot de passe, Microsoft).

**Auth :** `AllowAny`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | `{ "access": "<new jwt>" }` |
| `401 Unauthorized` | `refresh` invalide, expiré, ou blacklisté (par ex. après `/logout/`). |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `refresh` | string | oui | Un refresh token précédemment émis par inscription/connexion/OAuth. |

**Workflow**

1. Le client détecte (ou anticipe) l'expiration de son token `access`.
2. Le client envoie `{ "refresh": "<refresh>" }` en `POST`.
3. Le serveur vérifie le token (signature, expiration, non-blacklisté) et émet un nouvel `access` token (`ROTATE_REFRESH_TOKENS` est désactivé, donc le même `refresh` token reste valide et réutilisable pour de futurs rafraîchissements).
4. Le client remplace son `access` token stocké et continue d'utiliser le même `refresh` token.

---

### `POST /api/users/change-password/`

Change le mot de passe de l'utilisateur authentifié lui-même.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | `{ "detail": "Password updated successfully." }` |
| `400 Bad Request` | `current_password` erroné, `new_password` rejeté par les validateurs Django, ou compte n'ayant que des identités OAuth liées (pas de mot de passe local à remplacer). |
| `401 Unauthorized` | Access token absent/invalide. |
| `405 Method Not Allowed` | Toute méthode autre que `POST`. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `current_password` | string | oui | Doit correspondre au mot de passe actuel du compte. |
| `new_password` | string | oui | Validé par les validateurs de mot de passe Django. |

**Workflow**

1. Le client envoie `{ current_password, new_password }` avec un access token valide.
2. Le serializer rejette d'emblée la requête si le compte est OAuth-only (`user.oauth_accounts.exists()`).
3. Le serializer vérifie `current_password` contre le hash stocké.
4. Le serveur appelle `set_password(new_password)` et sauvegarde l'utilisateur.
5. **Remarque :** les access/refresh tokens existants ne sont *pas* révoqués par cet appel - combiner avec `POST /api/users/logout/` si les autres sessions doivent aussi être déconnectées de force.

---

### `GET /api/users/me/`

Renvoie le profil de l'utilisateur authentifié lui-même.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | La représentation `User` de l'appelant. |
| `401 Unauthorized` | Access token absent/invalide/expiré/blacklisté. |

**Paramètres :** aucun.

**Workflow**

1. Le client envoie `GET` avec `Authorization: Bearer <access>`.
2. Le serveur renvoie directement `UserSerializer(request.user).data` - aucune requête supplémentaire n'est nécessaire puisque l'utilisateur est déjà résolu par l'authentification.

---

### `GET /api/users/`

Liste tous les comptes utilisateurs. Réservé au staff - c'est un listing
administratif, pas un annuaire public.

**Auth :** `IsAuthenticated` + `IsAdminUser`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Tableau JSON simple d'utilisateurs (aucune pagination configurée sur ce viewset). |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Authentifié mais pas staff. |

**Paramètres :** aucun.

**Workflow**

1. Un client staff envoie `GET` sur `/api/users/`.
2. `UserViewSet.get_permissions()` exige `IsAdminUser` pour `list`/`retrieve`.
3. Le serveur renvoie chaque ligne `User`, sérialisée avec `UserSerializer`.

---

### `GET /api/users/{id}/`

Récupère le profil d'un utilisateur par son id. Réservé au staff, même
logique que la route de liste.

**Auth :** `IsAuthenticated` + `IsAdminUser`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | L'utilisateur demandé. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Authentifié mais pas staff. |
| `404 Not Found` | Aucun utilisateur avec cet id. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de l'utilisateur ciblé. |

**Workflow :** identique à la liste, restreint à une seule ligne via `get_object()`.

---

### `PATCH` / `PUT /api/users/{id}/`

Met à jour les champs du profil d'un utilisateur (le sien, ou celui de
n'importe qui si staff).

**Auth :** `IsAuthenticated` + `IsSelfOrStaff`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Représentation `User` mise à jour. |
| `400 Bad Request` | Valeur de champ invalide (par ex. email/username en doublon). |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant n'est ni l'utilisateur ciblé, ni staff. |
| `404 Not Found` | Aucun utilisateur avec cet id. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Type | Requis | Description |
| --- | --- | --- | --- | --- |
| `id` | chemin | integer | oui | Id de l'utilisateur ciblé. |
| `username`, `email`, `first_name`, `last_name`, `profile_icon` | corps | variable | non (tout sous-ensemble pour `PATCH` ; tous les champs modifiables pour `PUT`) | Champs à modifier. |

**Workflow**

1. Le client envoie `PATCH` (partiel) ou `PUT` (complet) avec les champs à modifier.
2. `IsSelfOrStaff.has_object_permission` vérifie `request.user.is_staff or obj == request.user`.
3. Le serveur valide et sauvegarde via `UserSerializer`.

---

### `DELETE /api/users/{id}/`

Supprime son propre compte (ou n'importe quel compte, si staff).

**Auth :** `IsAuthenticated` + `IsSelfOrStaff`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `204 No Content` | Compte supprimé. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant n'est ni l'utilisateur ciblé, ni staff. |
| `404 Not Found` | Aucun utilisateur avec cet id. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de l'utilisateur ciblé. |

**Workflow**

1. Le client envoie `DELETE` sur `/api/users/{id}/`.
2. Vérification de permission comme ci-dessus.
3. La ligne est supprimée. **Remarque :** toutes les clés étrangères vers `User` utilisent `on_delete=PROTECT` - supprimer un utilisateur qui possède encore des cookbooks/recettes/plannings/messages lèvera une `ProtectedError` (remontée aujourd'hui comme un `500` ; il n'y a aucune étape de réaffectation/cascade avant la suppression).

---

## 2. Cookbooks (`cookbooks`)

Les cookbooks constituent la frontière de partage/permission pour les
recettes, plannings et messages. Le créateur d'un cookbook en est
l'administrateur implicite ; d'autres utilisateurs peuvent se voir accorder
un rôle `creator` / `editor` / `commentator` / `reader` via
[`share`](#post--patch-apicookbooksidshare). Voir `cookbooks.permissions`
pour l'ordre exact des rangs.

### `GET /api/cookbooks/`

Liste les cookbooks que l'appelant a créés **ou** avec lesquels il a été
partagé.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste paginée (voir [Pagination](#pagination)). |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (query)

| Nom | Type | Description |
| --- | --- | --- |
| `name` | string | Correspondance partielle insensible à la casse sur le nom du cookbook. |
| `shared_with_me` | boolean | `true` : uniquement les cookbooks partagés avec l'appelant (dont il n'est pas propriétaire). `false` : uniquement ses propres cookbooks. |
| `page` | integer | Numéro de page. |
| `page_size` | integer | Éléments par page (100 maximum). |

**Workflow**

1. `get_queryset()` restreint les lignes à `creator=user OR shared_with__user=user`.
2. Les filtres et la pagination s'appliquent ensuite sur cet ensemble de base.
3. Chaque cookbook est renvoyé avec ses `recipes`, `plannings` et sa liste `shared_with` imbriqués.

---

### `POST /api/cookbooks/`

Crée un cookbook. L'appelant en devient le créateur (administrateur
implicite).

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Cookbook créé. |
| `400 Bad Request` | `name` manquant/invalide. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `name` | string | oui | |
| `icon` | string | non | Data URI/image en base64 ; une icône par défaut est utilisée si omis. |

**Workflow**

1. `CookbookWriteSerializer` valide `name`/`icon`.
2. `perform_create()` définit `creator=request.user`.
3. La réponse utilise le format imbriqué complet `CookbookSerializer` (`recipes`/`plannings`/`shared_with` vides pour un cookbook tout neuf).

---

### `GET /api/cookbooks/{id}/`

Récupère un cookbook avec ses recettes, plannings et membres.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Le cookbook. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | Le cookbook n'existe pas, ou l'appelant n'en est pas le créateur et n'est pas dans `shared_with` (un non-membre reçoit un `404`, jamais un `403`, afin de ne pas pouvoir confirmer que le cookbook existe). |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id du cookbook. |

---

### `PATCH` / `PUT /api/cookbooks/{id}/`

Renomme un cookbook / change son icône. Réservé à l'admin.

**Auth :** `IsAuthenticated` + `IsCookbookAdmin`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Cookbook mis à jour. |
| `400 Bad Request` | Valeur de champ invalide. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant a accès au cookbook (sinon `404`) mais n'en est pas le créateur/staff. |
| `404 Not Found` | Pas du tout membre. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Requis | Description |
| --- | --- | --- | --- |
| `id` | chemin | oui | Id du cookbook. |
| `name`, `icon` | corps | non (tout sous-ensemble pour `PATCH`) | Champs à modifier. |

---

### `DELETE /api/cookbooks/{id}/`

Supprime un cookbook. Réservé à l'admin.

**Auth :** `IsAuthenticated` + `IsCookbookAdmin`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `204 No Content` | Supprimé. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Membre mais pas admin. |
| `404 Not Found` | Pas membre. |
| `500` (`ProtectedError`) | Le cookbook a encore des recettes/plannings/messages/partages pointant vers lui via des FK `PROTECT` - rien dans cette route ne les délie au préalable. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id du cookbook. |

---

### `POST` / `PATCH /api/cookbooks/{id}/share/`

Accorde ou met à jour l'accès d'un ou plusieurs utilisateurs au cookbook, en
un seul appel. Les deux méthodes se comportent de façon identique (un
upsert) ; `PATCH` se lit simplement mieux quand on modifie le rôle d'un
membre existant.

**Auth :** `IsAuthenticated` + `IsCookbookAdmin`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Le cookbook est renvoyé avec sa liste `shared_with` à jour. |
| `400 Bad Request` | Ni/à la fois `user`/`email` fournis par entrée, email inconnu, `role` invalide, ou tentative de partage avec le créateur du cookbook lui-même. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Membre mais pas admin. |
| `404 Not Found` | Pas membre du cookbook. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Type | Requis | Description |
| --- | --- | --- | --- | --- |
| `id` | chemin | integer | oui | Id du cookbook. |
| `shares` | corps | array | oui | Liste d'entrées `{ user ou email, role }`. |
| `shares[].user` | corps | integer | un des deux (`user`/`email`) | Id de l'utilisateur cible. |
| `shares[].email` | corps | string | un des deux (`user`/`email`) | Email de l'utilisateur cible (résolu en utilisateur côté serveur). |
| `shares[].role` | corps | string | oui | Une valeur parmi `creator`, `editor`, `commentator`, `reader` (du plus au moins permissif ; il n'y a pas de rôle `admin` ici). |

**Workflow**

1. L'admin envoie `POST`/`PATCH` avec `{ "shares": [{ "user": 2, "role": "editor" }, ...] }`.
2. Chaque entrée est validée : exactement un des deux champs `user`/`email`, `email` résolu en `User`, la cible n'est pas le créateur du cookbook.
3. Pour chaque entrée, `SharedUserCookbook.objects.update_or_create(cookbook, user, defaults={"role": ...})` - repartager avec un membre existant **met à jour son rôle** plutôt que de dupliquer la ligne.
4. La réponse renvoie le cookbook avec sa liste `shared_with` rafraîchie.

---

### `POST /api/cookbooks/{id}/unshare/`

Révoque l'accès d'un ou plusieurs utilisateurs au cookbook, en un seul
appel.

**Auth :** `IsAuthenticated` + `IsCookbookAdmin`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Le cookbook est renvoyé avec sa liste `shared_with` à jour (révoquer un non-membre est un no-op, pas une erreur). |
| `400 Bad Request` | Id(s) utilisateur invalide(s) dans `users`. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Membre mais pas admin. |
| `404 Not Found` | Pas membre du cookbook. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Type | Requis | Description |
| --- | --- | --- | --- | --- |
| `id` | chemin | integer | oui | Id du cookbook. |
| `users` | corps | array d'integers | oui | Ids des utilisateurs à révoquer. |

---

### `GET /api/cookbooks/{id}/export/`

Exporte un cookbook (ses recettes et plannings) en JSON portable.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Export JSON, avec un en-tête `Content-Disposition: attachment`. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | Pas membre du cookbook. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id du cookbook. |

**Workflow**

1. N'importe quel membre (n'importe quel rôle, y compris `reader`) peut exporter.
2. Chaque recette rangée dans le cookbook est incluse (même format qu'un export de recette), chacune associée à un `id` local à l'export.
3. Chaque planning référence ses recettes programmées via `recipe_id`, correspondant à un de ces `id` locaux - un repas programmant une recette qui n'est *pas* rangée dans ce cookbook est silencieusement omis.
4. `shared_with` (les membres) n'est jamais inclus dans l'export.
5. Le résultat peut être renvoyé tel quel à [`POST /api/cookbooks/import/`](#post-apicookbooksimport).

---

### `GET /api/cookbooks/export/`

Exporte tous les cookbooks **créés par l'appelant** sous forme de tableau
JSON.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Tableau JSON, un objet d'export par cookbook possédé (les cookbooks uniquement partagés sont exclus). |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres :** aucun.

---

### `POST /api/cookbooks/import/`

Importe un ou plusieurs cookbooks à partir de JSON préalablement exporté.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Renvoie toujours un tableau JSON des cookbooks créés, même pour une charge utile contenant un seul objet. |
| `400 Bad Request` | Un élément quelconque échoue à la validation (par ex. un `meals[].recipe_id` ne correspondant à aucun `recipes[].id`) - tout l'import est rejeté, rien n'est créé. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| *(corps de requête)* | objet ou tableau | oui | Un objet d'export de cookbook, ou un tableau JSON de ceux-ci (tel que produit par les deux routes d'export ci-dessus). |

**Workflow**

1. Le client envoie exactement le JSON précédemment téléchargé depuis une route d'export.
2. Pour chaque objet cookbook : un nouveau `Cookbook` est créé avec l'appelant comme créateur ; chaque recette imbriquée est créée (ingrédients/tags appariés par nom et réutilisés s'ils existent déjà, sinon créés ; les étapes sont toujours créées à neuf) ; les repas de chaque planning sont reconstruits en résolvant `recipe_id` par rapport aux valeurs `recipes[].id` propres à la charge utile.
3. Aucun membre n'est importé - seul l'utilisateur important a accès au(x) nouveau(x) cookbook(s).
4. L'opération entière est atomique : tout échec de validation annule tout.

---

## 3. Recettes, tags & ingrédients (`recipes`)

### `GET /api/recipes/`

Liste les recettes visibles par l'appelant : recettes personnelles (sans
cookbook), recettes qu'il a créées, ou recettes rangées dans un cookbook
qu'il possède ou avec lequel il a été partagé.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste paginée. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (query)

| Nom | Type | Description |
| --- | --- | --- |
| `name` | string | Correspondance partielle insensible à la casse (`ILIKE` SQL) sur le titre de la recette. |
| `tags` | string | Noms et/ou ids de tags séparés par des virgules ; la recette doit posséder **tous** les tags listés. |
| `ingredients` | string | Noms et/ou ids d'ingrédients séparés par des virgules ; la recette doit contenir **tous** les ingrédients listés. |
| `cookbook` | string | Correspondance partielle insensible à la casse sur le nom du cookbook. |
| `in_cookbook` | boolean | `true` : uniquement les recettes rangées dans un cookbook. `false` : uniquement les recettes autonomes. |
| `planning` | string | Correspondance partielle insensible à la casse sur le nom d'un planning dans lequel la recette est programmée. |
| `in_planning` | boolean | `true` : uniquement les recettes programmées dans au moins un planning. `false` : uniquement celles qui ne le sont dans aucun. |
| `favorite` | boolean | `true` : uniquement les recettes favorites de l'appelant. `false` : uniquement celles qui ne le sont pas. |
| `shared_with_me` | boolean | `true` : uniquement les recettes rangées dans un cookbook partagé avec l'appelant (dont il n'est pas propriétaire). |
| `prep_time_min` / `prep_time_max` | number | Bornes (en minutes) sur la somme des durées des étapes de la recette. |
| `cooking_duration_min` / `cooking_duration_max` | number | Bornes (en minutes) sur le champ `cooking_duration`. |
| `page` / `page_size` | integer | Pagination. |

---

### `POST /api/recipes/`

Crée une recette avec ses ingrédients, tags et étapes.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Recette créée. |
| `400 Bad Request` | Champ manquant/invalide, ou `cookbook` fourni mais l'appelant n'a pas au moins le rang `creator` dessus. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `title` | string | oui | |
| `image`, `source` | string | non | |
| `cooking_duration` | decimal | non | En minutes. |
| `cookbook` | integer | non | Id du cookbook cible ; l'appelant doit avoir le rôle `creator` ou en être l'admin. |
| `ingredients` | array | non | `{ name, image?, quantity, unity?, person_numbers }` par ligne ; apparié/réutilisé par nom (insensible à la casse), créé si nouveau. |
| `tags` | array | non | `{ name, type, description? }` par tag ; apparié/réutilisé par nom, créé si nouveau. |
| `steps` | array | non | `{ description, step_number, dury, type }` par étape ; toujours créées à neuf. |

**Workflow**

1. `RecipeWriteSerializer` valide les champs de la recette et, si `cookbook` est renseigné, que l'appelant a au moins le rang `creator` dessus (`cookbooks.permissions.has_rank`).
2. `creator` est défini à partir de la requête, jamais depuis la charge utile.
3. Ingrédients/tags sont synchronisés par nom (get-or-create dans le catalogue partagé) ; les étapes sont (re)créées à neuf (`recipes/services.py`).
4. La réponse utilise le format imbriqué en lecture seule `RecipeSerializer`.

---

### `GET /api/recipes/{id}/`

Récupère une recette avec ses ingrédients, tags et étapes.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | La recette. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Recette rangée dans un cookbook où l'appelant n'a aucun rôle (visible dans le queryset de base seulement si créateur/membre du cookbook). |
| `404 Not Found` | La recette n'existe pas / n'est pas visible selon `get_queryset()`. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de la recette. |

---

### `PATCH` / `PUT /api/recipes/{id}/`

Met à jour les champs d'une recette et/ou remplace ses ingrédients/tags/étapes.

**Auth :** `IsAuthenticated` + `CookbookItemPermission`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Recette mise à jour. |
| `400 Bad Request` | Champ invalide, ou rang insuffisant sur le `cookbook` cible. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant n'est pas le créateur de la recette et n'a pas au moins le rang `editor` sur son cookbook (ou rang `creator`+ requis pour une recette autonome sans cookbook - seul le créateur peut la toucher). |
| `404 Not Found` | La recette n'existe pas / n'est pas visible. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Requis | Description |
| --- | --- | --- | --- |
| `id` | chemin | oui | Id de la recette. |
| `title`, `image`, `source`, `cooking_duration`, `cookbook`, `ingredients`, `tags`, `steps` | corps | non (tout sous-ensemble) | Omettre `ingredients`/`tags`/`steps` les laisse inchangés ; passer `[]` les vide. |

---

### `DELETE /api/recipes/{id}/`

Supprime une recette, en déliant d'abord ses ingrédients/tags/étapes/favoris
(toutes des FK `PROTECT` vers `Recipe`).

**Auth :** `IsAuthenticated` + `CookbookItemPermission`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `204 No Content` | Supprimée. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant n'est pas le créateur et n'a pas le rang `creator` sur son cookbook. |
| `404 Not Found` | La recette n'existe pas / n'est pas visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de la recette. |

---

### `GET /api/recipes/{id}/export/`

Exporte une recette en JSON portable (sans `id`/`creator`/`cookbook`).

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Export JSON, avec un en-tête `Content-Disposition: attachment`. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | La recette n'existe pas / n'est pas visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de la recette. |

**Workflow :** toute recette que l'appelant peut lire (la sienne, ou dans un
cookbook partagé) peut être exportée ainsi ; le résultat peut être renvoyé
tel quel à
[`POST /api/recipes/import/`](#post-apirecipesimport), et atterrira comme
recette personnelle autonome.

---

### `GET /api/recipes/export/`

Exporte les recettes **personnelles** de l'appelant (créées par lui, sans
cookbook) sous forme de tableau JSON.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Tableau JSON. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres :** aucun.

---

### `POST /api/recipes/import/`

Importe une ou plusieurs recettes à partir de JSON préalablement exporté.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Renvoie toujours un tableau JSON des recettes créées, même pour une charge utile contenant un seul objet. |
| `400 Bad Request` | Un élément quelconque échoue à la validation - tout l'import est rejeté. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| *(corps de requête)* | objet ou tableau | oui | Un objet d'export de recette, ou un tableau JSON de ceux-ci. |

**Workflow :** chaque recette importée devient toujours une recette
personnelle autonome possédée par l'appelant (`cookbook` n'est jamais
défini, même si l'export en provenait à l'origine) ; ingrédients/tags
appariés/réutilisés par nom (insensible à la casse), créés si nouveaux ;
étapes toujours créées à neuf.

---

### `POST` / `DELETE /api/recipes/{id}/favorite/`

Ajoute (`POST`) ou retire (`DELETE`) une recette des favoris de l'appelant.

**Auth :** `IsAuthenticated` + `CookbookItemPermission` (l'accès en lecture suffit - ajouter en favori ne requiert pas de droits d'édition)

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | `POST`, et la recette n'était pas déjà en favori. |
| `200 OK` | `POST`, et la recette était déjà en favori (idempotent, aucun doublon créé). |
| `204 No Content` | `DELETE` (idempotent, quel que soit l'état favori précédent). |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | La recette n'existe pas / n'est pas visible par l'appelant. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id de la recette. |

---

### `GET /api/tags/` et `GET /api/tags/{id}/`

Consultation en lecture seule du catalogue partagé de tags
(catégories/sous-catégories). Les tags ne sont jamais créés que via les
endpoints d'écriture des recettes.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste (tableau JSON simple - **non** paginé) ou tag unique. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | (route de détail) Aucun tag avec cet id. |

**Paramètres** (query, route de liste uniquement)

| Nom | Type | Description |
| --- | --- | --- |
| `search` | string | Correspondance de sous-chaîne sur `name` (`SearchFilter` de DRF). |
| `type` | string | Correspondance exacte sur la sous-catégorie du tag (par ex. `"repas"`, `"regime_alimentaire"`). |

---

### `GET /api/ingredients/` et `GET /api/ingredients/{id}/`

Consultation en lecture seule du catalogue partagé d'ingrédients (par ex.
pour la recherche/l'autocomplétion). Les ingrédients ne sont jamais créés
que via les endpoints d'écriture des recettes.

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste (tableau JSON simple - **non** paginé) ou ingrédient unique. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | (route de détail) Aucun ingrédient avec cet id. |

**Paramètres** (query, route de liste uniquement)

| Nom | Type | Description |
| --- | --- | --- |
| `search` | string | Correspondance de sous-chaîne sur `name` (`SearchFilter` de DRF). |

---

## 4. Planning (`planning`)

Les plannings programment des recettes dans des créneaux
jour/moment-du-repas/plat (`dayofweek` × `lunch` × `type`, jusqu'à 42
créneaux par semaine). Même modèle de visibilité/permission que les
recettes : un planning hors de tout cookbook n'est gérable que par son
créateur ; un planning rangé dans un cookbook est soumis au rôle de
l'appelant sur ce cookbook.

### `GET /api/plannings/`

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste paginée. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (query)

| Nom | Type | Description |
| --- | --- | --- |
| `name` | string | Correspondance partielle insensible à la casse sur le nom du planning. |
| `type` | string | Correspondance exacte sur le type du planning : `journalier` ou `hebdomadaire`. |
| `cookbook` | string | Correspondance partielle insensible à la casse sur le nom du cookbook. |
| `in_cookbook` | boolean | `true` : uniquement les plannings rangés dans un cookbook. `false` : uniquement les plannings autonomes. |
| `shared_with_me` | boolean | `true` : uniquement les plannings dans un cookbook partagé avec l'appelant. |
| `page` / `page_size` | integer | Pagination. |

---

### `POST /api/plannings/`

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Planning créé. |
| `400 Bad Request` | Champ manquant/invalide, rang insuffisant sur `cookbook`, ou deux repas ciblant le même créneau `(dayofweek, lunch, type)`. |
| `401 Unauthorized` | Access token absent/invalide. |

**Paramètres** (corps, JSON)

| Nom | Type | Requis | Description |
| --- | --- | --- | --- |
| `name` | string | oui | |
| `icon` | string | non | Une icône par défaut est utilisée si omise. |
| `cookbook` | integer | non | L'appelant doit avoir le rôle `creator` ou en être l'admin. |
| `meals` | array | non | `{ recipe, dayofweek, lunch, type }` par repas programmé. Au plus une recette par créneau `(dayofweek, lunch, type)`. |

**Paramètres** (valeurs possibles de `meals[]`)

| Champ | Valeurs autorisées |
| --- | --- |
| `lunch` | `midi`, `soir` |
| `type` | `entree`, `plat`, `dessert` |
| `dayofweek` | `lundi`, `mardi`, `mercredi`, `jeudi`, `vendredi`, `samedi`, `dimanche` |

---

### `GET /api/plannings/{id}/`

**Auth :** `IsAuthenticated`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Le planning, avec ses `meals` programmés. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | N'existe pas / non visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id du planning. |

---

### `PATCH` / `PUT /api/plannings/{id}/`

**Auth :** `IsAuthenticated` + `CookbookItemPermission`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Planning mis à jour. |
| `400 Bad Request` | Champ invalide, conflit de créneau, ou rang insuffisant sur `cookbook`. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Rang insuffisant (au moins `editor` requis ; `creator` pour un planning autonome). |
| `404 Not Found` | N'existe pas / non visible. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Requis | Description |
| --- | --- | --- | --- |
| `id` | chemin | oui | Id du planning. |
| `name`, `icon`, `cookbook`, `meals` | corps | non (tout sous-ensemble) | Omettre `meals` laisse le planning existant inchangé ; passer `[]` le vide. |

---

### `DELETE /api/plannings/{id}/`

Délie les repas programmés (`RecipePlanning`, FK `PROTECT`) avant de
supprimer le planning lui-même.

**Auth :** `IsAuthenticated` + `CookbookItemPermission`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `204 No Content` | Supprimé. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Rang insuffisant (`creator` requis). |
| `404 Not Found` | N'existe pas / non visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `id` | integer | Id du planning. |

---

## 5. Messagerie (`messaging`)

Les messages existent en deux variantes de la même ressource sous-jacente :
le **canal global** d'un cookbook, et le canal d'une **recette précise** au
sein de ce cookbook. Il n'existe volontairement aucune route de
modification - un message ne peut être que posté ou supprimé, jamais édité.

### `GET /api/cookbooks/{cookbook_pk}/messages/`

Liste les messages du canal global du cookbook (`recipe` toujours `null`).

**Auth :** `IsAuthenticated` + `CanAccessCookbookMessages` (tout rôle, y compris `reader`, peut lire)

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Liste paginée. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | `cookbook_pk` n'existe pas, ou l'appelant n'est pas membre (et n'est pas staff) - un tiers ne peut pas savoir que le cookbook existe. |

**Paramètres** (chemin + query)

| Nom | Emplacement | Type | Description |
| --- | --- | --- | --- |
| `cookbook_pk` | chemin | integer | Id du cookbook. |
| `page` / `page_size` | query | integer | Pagination. |

---

### `POST /api/cookbooks/{cookbook_pk}/messages/`

Poste un message dans le canal global du cookbook.

**Auth :** `IsAuthenticated` + `CanAccessCookbookMessages` (au moins le rôle `commentator` requis pour écrire)

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `201 Created` | Message créé. |
| `400 Bad Request` | `content`/`canal` manquant/invalide. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | Membre avec seulement le rôle `reader` (accès lecture, pas d'écriture). |
| `404 Not Found` | `cookbook_pk` n'existe pas / l'appelant n'est pas membre. |

**Paramètres** (chemin + corps)

| Nom | Emplacement | Type | Requis | Description |
| --- | --- | --- | --- | --- |
| `cookbook_pk` | chemin | integer | oui | Id du cookbook. |
| `content` | corps | string | oui | Texte du message. |
| `canal` | corps | string | oui | Libellé libre du canal de conversation. |

**Workflow :** `author`, `cookbook` (depuis l'URL) et `recipe=None` sont
toujours définis côté serveur, jamais acceptés depuis le corps de la
requête.

---

### `GET /api/cookbooks/{cookbook_pk}/messages/{pk}/`

Récupère un message du canal global du cookbook.

**Auth :** `IsAuthenticated` + `CanAccessCookbookMessages`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `200 OK` | Le message. |
| `401 Unauthorized` | Access token absent/invalide. |
| `404 Not Found` | `cookbook_pk`/`pk` n'existe pas, ou non visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Id du cookbook. |
| `pk` | integer | Id du message. |

---

### `DELETE /api/cookbooks/{cookbook_pk}/messages/{pk}/`

Supprime un message du canal global du cookbook.

**Auth :** `IsAuthenticated` + `CanAccessCookbookMessages` + `CanDeleteMessage`

**Codes de statut**

| Statut | Signification |
| --- | --- |
| `204 No Content` | Supprimé. |
| `401 Unauthorized` | Access token absent/invalide. |
| `403 Forbidden` | L'appelant n'est ni l'auteur du message, ni l'admin du cookbook, ni staff. |
| `404 Not Found` | `cookbook_pk`/`pk` n'existe pas, ou non visible. |

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Id du cookbook. |
| `pk` | integer | Id du message. |

---

### `GET` / `POST /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/`

Même comportement que les routes de liste/création au niveau cookbook
ci-dessus, mais restreint au canal d'une recette précise plutôt qu'au canal
global du cookbook.

**Auth :** identique aux équivalents au niveau cookbook.

**Codes de statut :** identiques aux deux routes ci-dessus, plus :

| Statut | Signification |
| --- | --- |
| `404 Not Found` | Également renvoyé si `recipe_pk` n'appartient pas à `cookbook_pk` (`recipe.cookbook_id != cookbook_pk`) - une paire incohérente ne peut pas servir à divulguer ou mal ranger un message. |

**Paramètres** (chemin + query/corps)

| Nom | Emplacement | Type | Description |
| --- | --- | --- | --- |
| `cookbook_pk` | chemin | integer | Id du cookbook. |
| `recipe_pk` | chemin | integer | Id de la recette ; doit être rangée dans `cookbook_pk`. |
| `content`, `canal` | corps (`POST` uniquement) | string | Identique à la route au niveau cookbook. |
| `page` / `page_size` | query (`GET` uniquement) | integer | Pagination. |

---

### `GET /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/{pk}/`

Récupère un message du canal de la recette.

**Auth/codes de statut :** identiques à la route de récupération au niveau
cookbook ci-dessus, plus le cas `404` de non-correspondance `recipe_pk`.

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Id du cookbook. |
| `recipe_pk` | integer | Id de la recette. |
| `pk` | integer | Id du message. |

---

### `DELETE /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/{pk}/`

Supprime un message du canal de la recette.

**Auth/codes de statut :** identiques à la route de suppression au niveau
cookbook ci-dessus, plus le cas `404` de non-correspondance `recipe_pk`.

**Paramètres** (chemin)

| Nom | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Id du cookbook. |
| `recipe_pk` | integer | Id de la recette. |
| `pk` | integer | Id du message. |
