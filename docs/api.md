# API

🇬🇧 English | [🇫🇷 Français](api.fr.md)

## Summary

- [Overview](#overview)
  - [Base URL](#base-url)
  - [Authentication](#authentication)
  - [Pagination](#pagination)
  - [Error shape](#error-shape)
  - [Interactive docs](#interactive-docs)
- [1. Accounts & authentication (`users`)](#1-accounts--authentication-users)
- [2. Cookbooks (`cookbooks`)](#2-cookbooks-cookbooks)
- [3. Recipes, tags & ingredients (`recipes`)](#3-recipes-tags--ingredients-recipes)
- [4. Planning (`planning`)](#4-planning-planning)
- [5. Messaging (`messaging`)](#5-messaging-messaging)

This document lists every API route exposed by the backend, grouped by Django
app. For each route it explains: the expected response status codes, its
parameters (path, query and body), and the workflow a caller is expected to
follow. For the underlying database tables see [`docs/database.md`](database.md);
for the Microsoft OAuth login flow specifically, see [`docs/oauth.md`](oauth.md).

---

## Overview

### Base URL

All routes below are relative to `/api/`. Locally (via
`docker-compose.dev.yml`), that's `http://localhost:${BACKEND_PORT}/api/`.

### Authentication

The API uses JWT bearer tokens (`djangorestframework-simplejwt`). Once a
caller has an `access` token (from register/login/OAuth), it must be sent on
every authenticated request as:

```
Authorization: Bearer <access>
```

- **Access token lifetime:** 60 minutes (`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME`).
- **Refresh token lifetime:** 7 days (`SIMPLE_JWT.REFRESH_TOKEN_LIFETIME`).
- When an access token expires, exchange the `refresh` token for a new one via
  [`POST /api/users/token/refresh/`](#post-apiuserstokenrefresh).
- [`POST /api/users/logout/`](#post-apiuserslogout) blacklists **both** the
  refresh token and the access token used to call it - see
  `users.authentication.BlacklistAwareJWTAuthentication` - so neither can be
  reused afterwards, even though the access token hasn't naturally expired
  yet.
- Routes are `AllowAny` (no token needed), `IsAuthenticated` (any valid,
  non-blacklisted access token), or further restricted (staff-only,
  object-owner-only, cookbook-role-based) - each route below states which.

### Pagination

List endpoints that support pagination (`DefaultPagination`, 10 items/page by
default, 100 max via `?page_size=`) wrap their results in this envelope:

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

Not every list endpoint paginates - `GET /api/tags/` and
`GET /api/ingredients/` return a plain JSON array, since no pagination class
is configured on those two viewsets.

### Error shape

Validation errors (`400 Bad Request`) come from DRF serializers, as either:

```json
{ "detail": "A single, human-readable message." }
```

or a per-field error map:

```json
{ "field_name": ["This field is required."] }
```

`401 Unauthorized` is returned when authentication is missing/invalid/expired
(handled entirely by DRF/Simple JWT, not by application code). `403 Forbidden`
is returned when authentication succeeded but the caller lacks the required
role/permission. `404 Not Found` is used - deliberately, in several places
below - instead of `403` when revealing that an object exists at all would
leak information the caller shouldn't have (e.g. a cookbook they aren't a
member of).

### Interactive docs

The schema documented by hand below is also generated automatically from the
same code (via `drf-spectacular`):

- Raw OpenAPI schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`

---

## 1. Accounts & authentication (`users`)

### `POST /api/users/register/`

Creates a new local account (username/email/password) and immediately logs it
in.

**Auth:** `AllowAny`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Account created; response includes the user and a token pair. |
| `400 Bad Request` | Missing/invalid field, username or email already taken, or password fails Django's validators (too short, too common, too similar to the username, entirely numeric). |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `username` | string | yes | Unique. |
| `email` | string | yes | Unique, must be a valid email address. |
| `password` | string | yes | Write-only, validated by Django's password validators. |
| `first_name` | string | no | |
| `last_name` | string | no | |
| `profile_icon` | string | no | Defaults to `""` when omitted. |

**Workflow**

1. Client `POST`s the registration form.
2. Serializer validates uniqueness of `username`/`email` and password strength.
3. Server hashes the password (`set_password`) and creates the `User` row.
4. Server issues a JWT pair (`RefreshToken.for_user`) exactly like a normal login.
5. Response: `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`.
6. Client stores `access`/`refresh` and attaches `Authorization: Bearer <access>` to subsequent calls.

---

### `POST /api/users/login/`

Authenticates with email + password.

**Auth:** `AllowAny`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Credentials valid; response includes the user and a token pair. |
| `400 Bad Request` | Unknown email, wrong password, disabled account, or an OAuth-only account with no local password - all return the same generic message so a caller can't tell which case applies. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `email` | string | yes | |
| `password` | string | yes | Write-only. |

**Workflow**

1. Client `POST`s `{ email, password }`.
2. Server looks up the `User` by email, then calls Django's `authenticate()` with that user's `username` + the given password.
3. On success, a fresh JWT pair is issued (previous tokens, if any, are **not** revoked by logging in again).
4. Response: `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`.

---

### `POST /api/users/logout/`

Revokes the current session: blacklists the given refresh token **and** the
access token used to authenticate this very call.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Both tokens blacklisted. `{ "detail": "Logged out successfully." }` |
| `400 Bad Request` | `refresh` missing, malformed, expired, already blacklisted, or belongs to a different user than the one authenticating the request. |
| `401 Unauthorized` | No/invalid/expired/already-blacklisted access token supplied. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `refresh` | string | yes | The refresh token issued alongside the access token currently in use. |

**Workflow**

1. Client sends `Authorization: Bearer <access>` and `{ "refresh": "<refresh>" }` in the body.
2. Server parses `refresh` as a `RefreshToken`; a decode/expiry/already-blacklisted failure returns `400` immediately.
3. Server checks the refresh token's `user_id` claim matches `request.user.id` - otherwise `400` (can't log out someone else's session).
4. Server blacklists the refresh token (`RefreshToken.blacklist()` - standard Simple JWT behaviour).
5. Server also blacklists the **access** token used for this request (`request.auth`), by manually creating the `OutstandingToken`/`BlacklistedToken` rows Simple JWT doesn't create for access tokens by default.
6. From this point on: refreshing with that `refresh` token → `401` on `/token/refresh/`; reusing that `access` token on any authenticated route → `401` (enforced by `BlacklistAwareJWTAuthentication`).

---

### `POST /api/users/oauth/microsoft/`

Exchanges a Microsoft authorization `code` for a Graph profile, then logs the
user in (creating the account on first login). See
[`docs/oauth.md`](oauth.md) for the full sequence diagram and frontend
integration steps.

**Auth:** `AllowAny`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Login/registration successful; response includes the user and a token pair. |
| `400 Bad Request` | `code` missing, Microsoft rejected the exchange (expired/used code, wrong `redirect_uri`, revoked consent), or the Graph profile has neither `mail` nor `userPrincipalName`. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | string | yes | Authorization code obtained by redirecting the browser to Microsoft's `/oauth2/v2.0/authorize` endpoint. |

**Workflow**

1. Frontend redirects the browser to Microsoft to authenticate/consent.
2. Microsoft redirects back to the frontend's callback URL with `?code=...`.
3. Frontend `POST`s `{ code }` to this endpoint.
4. Backend exchanges `code` for a Graph access token via MSAL (server-side only - uses `AZURE_CLIENT_SECRET`, never exposed to the frontend).
5. Backend fetches the Graph profile (`givenName`, `surname`, `mail`/`userPrincipalName`) and checks whether the account has a photo.
6. Backend gets-or-creates the `User` (matched by email) and its linked `OAuthUser(provider="microsoft")` row.
7. Response: `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }`, identical shape to `/login/`.

---

### `POST /api/users/token/refresh/`

Exchanges a refresh token for a new access token. Built-in Simple JWT view
(`TokenRefreshView`), shared by every login method (password, Microsoft).

**Auth:** `AllowAny`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | `{ "access": "<new jwt>" }` |
| `401 Unauthorized` | `refresh` invalid, expired, or blacklisted (e.g. after `/logout/`). |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `refresh` | string | yes | A refresh token previously issued by register/login/OAuth. |

**Workflow**

1. Client detects (or anticipates) that its `access` token has expired.
2. Client `POST`s `{ "refresh": "<refresh>" }`.
3. Server verifies the token (signature, expiry, not blacklisted) and issues a new `access` token (`ROTATE_REFRESH_TOKENS` is off, so the same `refresh` token stays valid and reusable for future refreshes).
4. Client replaces its stored `access` token and keeps using the same `refresh` token.

---

### `POST /api/users/change-password/`

Changes the authenticated user's own password.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | `{ "detail": "Password updated successfully." }` |
| `400 Bad Request` | `current_password` wrong, `new_password` fails Django's password validators, or the account only has linked OAuth identities (no local password to replace). |
| `401 Unauthorized` | No/invalid access token. |
| `405 Method Not Allowed` | Any method other than `POST`. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `current_password` | string | yes | Must match the account's current password. |
| `new_password` | string | yes | Validated by Django's password validators. |

**Workflow**

1. Client `POST`s `{ current_password, new_password }` with a valid access token.
2. Serializer rejects the request outright if the account is OAuth-only (`user.oauth_accounts.exists()`).
3. Serializer checks `current_password` against the stored hash.
4. Server calls `set_password(new_password)` and saves the user.
5. **Note:** existing access/refresh tokens are *not* revoked by this call - combine with `POST /api/users/logout/` if other sessions should be force-logged-out too.

---

### `GET /api/users/me/`

Returns the authenticated user's own profile.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The caller's `User` representation. |
| `401 Unauthorized` | No/invalid/expired/blacklisted access token. |

**Parameters:** none.

**Workflow**

1. Client `GET`s with `Authorization: Bearer <access>`.
2. Server returns `UserSerializer(request.user).data` directly - no extra query needed since the user is already resolved by authentication.

---

### `GET /api/users/`

Lists all user accounts. Staff-only - this is an administrative listing, not
a public directory.

**Auth:** `IsAuthenticated` + `IsAdminUser`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Plain JSON array of users (no pagination configured on this viewset). |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Authenticated but not staff. |

**Parameters:** none.

**Workflow**

1. Staff client `GET`s `/api/users/`.
2. `UserViewSet.get_permissions()` requires `IsAdminUser` for `list`/`retrieve`.
3. Server returns every `User` row, serialized with `UserSerializer`.

---

### `GET /api/users/{id}/`

Retrieves a single user's profile by id. Staff-only, same rationale as the
list route.

**Auth:** `IsAuthenticated` + `IsAdminUser`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The requested `User`. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Authenticated but not staff. |
| `404 Not Found` | No user with that id. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Target user's id. |

**Workflow:** same as list, scoped to one row via `get_object()`.

---

### `PATCH` / `PUT /api/users/{id}/`

Updates a user's own profile fields (or any user's, if staff).

**Auth:** `IsAuthenticated` + `IsSelfOrStaff`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Updated `User` representation. |
| `400 Bad Request` | Invalid field value (e.g. duplicate email/username). |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller is neither the target user nor staff. |
| `404 Not Found` | No user with that id. |

**Parameters** (path + body)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `id` | path | integer | yes | Target user's id. |
| `username`, `email`, `first_name`, `last_name`, `profile_icon` | body | varies | no (any subset for `PATCH`; all writable fields for `PUT`) | Fields to change. |

**Workflow**

1. Client sends `PATCH` (partial) or `PUT` (full) with the fields to change.
2. `IsSelfOrStaff.has_object_permission` checks `request.user.is_staff or obj == request.user`.
3. Server validates and saves via `UserSerializer`.

---

### `DELETE /api/users/{id}/`

Deletes a user's own account (or any account, if staff).

**Auth:** `IsAuthenticated` + `IsSelfOrStaff`

**Status codes**

| Status | Meaning |
| --- | --- |
| `204 No Content` | Account deleted. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller is neither the target user nor staff. |
| `404 Not Found` | No user with that id. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Target user's id. |

**Workflow**

1. Client `DELETE`s `/api/users/{id}/`.
2. Permission check as above.
3. Row deleted. **Note:** every foreign key to `User` uses `on_delete=PROTECT` - deleting a user who still owns cookbooks/recipes/plannings/messages will raise a `ProtectedError` (surfaced as a `500` today; there is no cascading/reassignment step before delete).

---

## 2. Cookbooks (`cookbooks`)

Cookbooks are the sharing/permission boundary for recipes, plannings and
messages. A cookbook's own creator is its implicit admin; other users can be
granted a `creator` / `editor` / `commentator` / `reader` role via
[`share`](#post--patch-apicookbooksidshare). See
`cookbooks.permissions` for the exact rank order.

### `GET /api/cookbooks/`

Lists cookbooks the caller created **or** was shared.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Paginated list (see [Pagination](#pagination)). |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (query)

| Name | Type | Description |
| --- | --- | --- |
| `name` | string | Case-insensitive partial match on cookbook name. |
| `shared_with_me` | boolean | `true`: only cookbooks shared with the caller (not owned by them). `false`: only cookbooks the caller owns. |
| `page` | integer | Page number. |
| `page_size` | integer | Items per page (max 100). |

**Workflow**

1. `get_queryset()` restricts rows to `creator=user OR shared_with__user=user`.
2. Filters and pagination apply on top of that base set.
3. Each cookbook is returned with its nested `recipes`, `plannings` and `shared_with` list.

---

### `POST /api/cookbooks/`

Creates a cookbook. The caller becomes its creator (implicit admin).

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Cookbook created. |
| `400 Bad Request` | Missing/invalid `name`. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | |
| `icon` | string | no | Data URI/base64 image; defaults to a built-in icon if omitted. |

**Workflow**

1. `CookbookWriteSerializer` validates `name`/`icon`.
2. `perform_create()` sets `creator=request.user`.
3. Response uses the full nested `CookbookSerializer` shape (empty `recipes`/`plannings`/`shared_with` for a brand-new cookbook).

---

### `GET /api/cookbooks/{id}/`

Retrieves one cookbook with its recipes, plannings and members.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The cookbook. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | Cookbook doesn't exist, or the caller isn't its creator and isn't in `shared_with` (a non-member gets `404`, never `403`, so they can't confirm the cookbook exists). |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Cookbook id. |

---

### `PATCH` / `PUT /api/cookbooks/{id}/`

Renames a cookbook / changes its icon. Admin-only.

**Auth:** `IsAuthenticated` + `IsCookbookAdmin`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Updated cookbook. |
| `400 Bad Request` | Invalid field value. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller has access to the cookbook (so it 404s otherwise) but isn't its creator/staff. |
| `404 Not Found` | Not a member at all. |

**Parameters** (path + body)

| Name | Location | Required | Description |
| --- | --- | --- | --- |
| `id` | path | yes | Cookbook id. |
| `name`, `icon` | body | no (any subset for `PATCH`) | Fields to change. |

---

### `DELETE /api/cookbooks/{id}/`

Deletes a cookbook. Admin-only.

**Auth:** `IsAuthenticated` + `IsCookbookAdmin`

**Status codes**

| Status | Meaning |
| --- | --- |
| `204 No Content` | Deleted. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Member but not admin. |
| `404 Not Found` | Not a member. |
| `500` (`ProtectedError`) | The cookbook still has recipes/plannings/messages/shares pointing at it via `PROTECT` FKs - nothing in this route unlinks them first. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Cookbook id. |

---

### `POST` / `PATCH /api/cookbooks/{id}/share/`

Grants or updates one or more users' access to the cookbook, in a single
call. Both methods behave identically (an upsert); `PATCH` just reads better
when changing an existing member's role.

**Auth:** `IsAuthenticated` + `IsCookbookAdmin`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Cookbook returned with its up-to-date `shared_with` list. |
| `400 Bad Request` | Neither/both of `user`/`email` given per entry, unknown email, invalid `role`, or trying to share with the cookbook's own creator. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Member but not admin. |
| `404 Not Found` | Not a member of the cookbook. |

**Parameters** (path + body)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `id` | path | integer | yes | Cookbook id. |
| `shares` | body | array | yes | List of `{ user or email, role }` entries. |
| `shares[].user` | body | integer | one of `user`/`email` | Target user's id. |
| `shares[].email` | body | string | one of `user`/`email` | Target user's email (resolved to a user server-side). |
| `shares[].role` | body | string | yes | One of `creator`, `editor`, `commentator`, `reader` (most to least permissive; there is no `admin` role here). |

**Workflow**

1. Admin `POST`s/`PATCH`es `{ "shares": [{ "user": 2, "role": "editor" }, ...] }`.
2. Each entry is validated: exactly one of `user`/`email`, `email` resolved to a `User`, target isn't the cookbook's own creator.
3. For each entry, `SharedUserCookbook.objects.update_or_create(cookbook, user, defaults={"role": ...})` - re-sharing with an existing member **updates their role** rather than duplicating the row.
4. Response returns the cookbook with its refreshed `shared_with` list.

---

### `POST /api/cookbooks/{id}/unshare/`

Revokes one or more users' access to the cookbook, in a single call.

**Auth:** `IsAuthenticated` + `IsCookbookAdmin`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Cookbook returned with its up-to-date `shared_with` list (revoking a non-member is a no-op, not an error). |
| `400 Bad Request` | Invalid user id(s) in `users`. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Member but not admin. |
| `404 Not Found` | Not a member of the cookbook. |

**Parameters** (path + body)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `id` | path | integer | yes | Cookbook id. |
| `users` | body | array of integers | yes | IDs of the users to revoke. |

---

### `GET /api/cookbooks/{id}/export/`

Exports a single cookbook (its recipes and plannings) as portable JSON.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | JSON export, with a `Content-Disposition: attachment` header. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | Not a member of the cookbook. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Cookbook id. |

**Workflow**

1. Any member (any role, including `reader`) can export.
2. Every recipe filed in the cookbook is embedded (same shape as a recipe export), each tagged with an export-local `id`.
3. Every planning's meals reference a recipe via `recipe_id`, matching one of those local `id`s - a meal scheduling a recipe *not* filed into this cookbook is silently dropped.
4. `shared_with` (members) is never included in the export.
5. The result can be fed as-is to [`POST /api/cookbooks/import/`](#post-apicookbooksimport).

---

### `GET /api/cookbooks/export/`

Exports every cookbook **the caller created** as a JSON array.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | JSON array, one export object per owned cookbook (shared-only cookbooks are excluded). |
| `401 Unauthorized` | No/invalid access token. |

**Parameters:** none.

---

### `POST /api/cookbooks/import/`

Imports one or more cookbooks from previously exported JSON.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Always returns a JSON array of the created cookbooks, even for a single-object payload. |
| `400 Bad Request` | Any item fails validation (e.g. a `meals[].recipe_id` that doesn't match any `recipes[].id`) - the whole import is rejected, nothing is created. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| *(request body)* | object or array | yes | A single cookbook export object, or a JSON array of them (as produced by the two export routes above). |

**Workflow**

1. Client `POST`s the exact JSON previously downloaded from an export route.
2. For each cookbook object: a new `Cookbook` is created with the caller as creator; each nested recipe is created (ingredients/tags matched by name and reused if they already exist, otherwise created; steps always created fresh); each planning's meals are rebuilt by resolving `recipe_id` against the payload's own `recipes[].id` values.
3. No members are imported - only the importing user has access to the new cookbook(s).
4. The whole operation is atomic: any validation failure rolls back everything.

---

## 3. Recipes, tags & ingredients (`recipes`)

### `GET /api/recipes/`

Lists recipes visible to the caller: personal recipes (no cookbook), recipes
they created, or recipes filed in a cookbook they own or are shared.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Paginated list. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (query)

| Name | Type | Description |
| --- | --- | --- |
| `name` | string | Full-text search (PostgreSQL, French config) on the recipe title. |
| `tags` | string | Comma-separated tag names and/or ids; the recipe must have **all** of them. |
| `ingredients` | string | Comma-separated ingredient names and/or ids; the recipe must contain **all** of them. |
| `cookbook` | string | Case-insensitive partial match on the cookbook's name. |
| `in_cookbook` | boolean | `true`: only recipes filed in a cookbook. `false`: only standalone recipes. |
| `favorite` | boolean | `true`: only the caller's favorited recipes. `false`: only non-favorites. |
| `shared_with_me` | boolean | `true`: only recipes in a cookbook shared with the caller (not owned by them). |
| `prep_time_min` / `prep_time_max` | number | Bounds (minutes) on the sum of the recipe's step durations. |
| `cooking_duration_min` / `cooking_duration_max` | number | Bounds (minutes) on the `cooking_duration` field. |
| `page` / `page_size` | integer | Pagination. |

---

### `POST /api/recipes/`

Creates a recipe together with its ingredients, tags and steps.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Recipe created. |
| `400 Bad Request` | Missing/invalid field, or `cookbook` given but the caller lacks at least `creator` rank on it. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | yes | |
| `image`, `source` | string | no | |
| `cooking_duration` | decimal | no | Minutes. |
| `cookbook` | integer | no | Target cookbook id; caller must have `creator` role or be its admin. |
| `ingredients` | array | no | `{ name, image?, quantity, unity?, person_numbers }` per line; matched/reused by name (case-insensitive), created if new. |
| `tags` | array | no | `{ name, type, description? }` per tag; matched/reused by name, created if new. |
| `steps` | array | no | `{ description, step_number, dury, type }` per step; always created fresh. |

**Workflow**

1. `RecipeWriteSerializer` validates the recipe fields and, if `cookbook` is set, that the caller has at least `creator` rank on it (`cookbooks.permissions.has_rank`).
2. `creator` is set from the request, never from the payload.
3. Ingredients/tags are synced by name (get-or-create in the shared catalogue); steps are (re)created from scratch (`recipes/services.py`).
4. Response uses the nested, read-only `RecipeSerializer` shape.

---

### `GET /api/recipes/{id}/`

Retrieves one recipe with its ingredients, tags and steps.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The recipe. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Recipe is filed in a cookbook the caller has no role on (visible in the base queryset only if creator/cookbook member). |
| `404 Not Found` | Recipe doesn't exist / isn't visible per `get_queryset()`. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Recipe id. |

---

### `PATCH` / `PUT /api/recipes/{id}/`

Updates a recipe's fields and/or replaces its ingredients/tags/steps.

**Auth:** `IsAuthenticated` + `CookbookItemPermission`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Updated recipe. |
| `400 Bad Request` | Invalid field, or insufficient rank on the target `cookbook`. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller isn't the recipe's creator and lacks at least `editor` rank on its cookbook (or `creator`+ rank required for a standalone recipe with no cookbook - only the creator can touch it). |
| `404 Not Found` | Recipe doesn't exist / isn't visible. |

**Parameters** (path + body)

| Name | Location | Required | Description |
| --- | --- | --- | --- |
| `id` | path | yes | Recipe id. |
| `title`, `image`, `source`, `cooking_duration`, `cookbook`, `ingredients`, `tags`, `steps` | body | no (any subset) | Omitting `ingredients`/`tags`/`steps` leaves them untouched; passing `[]` clears them. |

---

### `DELETE /api/recipes/{id}/`

Deletes a recipe, unlinking its ingredients/tags/steps/favorites first (all
`PROTECT` FKs to `Recipe`).

**Auth:** `IsAuthenticated` + `CookbookItemPermission`

**Status codes**

| Status | Meaning |
| --- | --- |
| `204 No Content` | Deleted. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller isn't the creator and lacks `creator` rank on its cookbook. |
| `404 Not Found` | Recipe doesn't exist / isn't visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Recipe id. |

---

### `GET /api/recipes/{id}/export/`

Exports a single recipe as portable JSON (no `id`/`creator`/`cookbook`).

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | JSON export, with a `Content-Disposition: attachment` header. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | Recipe doesn't exist / isn't visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Recipe id. |

**Workflow:** any recipe the caller can read (own, or in a shared cookbook)
can be exported this way; the result can be fed as-is to
[`POST /api/recipes/import/`](#post-apirecipesimport), landing as a
standalone personal recipe.

---

### `GET /api/recipes/export/`

Exports the caller's **personal** recipes (created by them, filed in no
cookbook) as a JSON array.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | JSON array. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters:** none.

---

### `POST /api/recipes/import/`

Imports one or more recipes from previously exported JSON.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Always returns a JSON array of the created recipes, even for a single-object payload. |
| `400 Bad Request` | Any item fails validation - the whole import is rejected. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| *(request body)* | object or array | yes | A single recipe export object, or a JSON array of them. |

**Workflow:** every imported recipe always becomes a standalone personal
recipe owned by the caller (`cookbook` is never set, even if the export
originally came from one); ingredients/tags matched/reused by name
(case-insensitive), created if new; steps always created fresh.

---

### `POST` / `DELETE /api/recipes/{id}/favorite/`

Adds (`POST`) or removes (`DELETE`) a recipe from the caller's favorites.

**Auth:** `IsAuthenticated` + `CookbookItemPermission` (read access is enough - favoriting doesn't require edit rights)

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | `POST`, and the recipe wasn't already a favorite. |
| `200 OK` | `POST`, and the recipe was already a favorite (idempotent, no duplicate created). |
| `204 No Content` | `DELETE` (idempotent, regardless of prior favorite state). |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | Recipe doesn't exist / isn't visible to the caller. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Recipe id. |

---

### `GET /api/tags/` and `GET /api/tags/{id}/`

Read-only browsing of the shared tag catalogue (categories/sub-categories).
Tags are only ever created through the recipe write endpoints.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | List (plain JSON array - **not** paginated) or single tag. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | (detail route) No tag with that id. |

**Parameters** (query, list route only)

| Name | Type | Description |
| --- | --- | --- |
| `search` | string | Substring match on `name` (DRF `SearchFilter`). |
| `type` | string | Exact match on the tag's sub-category (e.g. `"repas"`, `"regime_alimentaire"`). |

---

### `GET /api/ingredients/` and `GET /api/ingredients/{id}/`

Read-only browsing of the shared ingredient catalogue (e.g. for
search/autocomplete). Ingredients are only ever created through the recipe
write endpoints.

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | List (plain JSON array - **not** paginated) or single ingredient. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | (detail route) No ingredient with that id. |

**Parameters** (query, list route only)

| Name | Type | Description |
| --- | --- | --- |
| `search` | string | Substring match on `name` (DRF `SearchFilter`). |

---

## 4. Planning (`planning`)

Plannings schedule recipes into day/meal-moment/course slots
(`dayofweek` × `lunch` × `type`, up to 42 slots/week). Same
visibility/permission model as recipes: a planning outside any cookbook is
only manageable by its creator; one filed in a cookbook is gated by the
caller's role on that cookbook.

### `GET /api/plannings/`

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Paginated list. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (query)

| Name | Type | Description |
| --- | --- | --- |
| `name` | string | Case-insensitive partial match on planning name. |
| `cookbook` | string | Case-insensitive partial match on the cookbook's name. |
| `in_cookbook` | boolean | `true`: only plannings filed in a cookbook. `false`: only standalone plannings. |
| `shared_with_me` | boolean | `true`: only plannings in a cookbook shared with the caller. |
| `page` / `page_size` | integer | Pagination. |

---

### `POST /api/plannings/`

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Planning created. |
| `400 Bad Request` | Missing/invalid field, insufficient rank on `cookbook`, or two meals target the same `(dayofweek, lunch, type)` slot. |
| `401 Unauthorized` | No/invalid access token. |

**Parameters** (body, JSON)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | |
| `icon` | string | no | Defaults to a built-in icon. |
| `cookbook` | integer | no | Caller must have `creator` role or be its admin. |
| `meals` | array | no | `{ recipe, dayofweek, lunch, type }` per scheduled meal. At most one recipe per `(dayofweek, lunch, type)` slot. |

**Parameters** (`meals[]` choices)

| Field | Allowed values |
| --- | --- |
| `lunch` | `midi`, `soir` |
| `type` | `entree`, `plat`, `dessert` |
| `dayofweek` | `lundi`, `mardi`, `mercredi`, `jeudi`, `vendredi`, `samedi`, `dimanche` |

---

### `GET /api/plannings/{id}/`

**Auth:** `IsAuthenticated`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The planning, with its scheduled `meals`. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | Doesn't exist / not visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Planning id. |

---

### `PATCH` / `PUT /api/plannings/{id}/`

**Auth:** `IsAuthenticated` + `CookbookItemPermission`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Updated planning. |
| `400 Bad Request` | Invalid field, slot conflict, or insufficient rank on `cookbook`. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Insufficient rank (at least `editor` required; `creator` for a standalone planning). |
| `404 Not Found` | Doesn't exist / not visible. |

**Parameters** (path + body)

| Name | Location | Required | Description |
| --- | --- | --- | --- |
| `id` | path | yes | Planning id. |
| `name`, `icon`, `cookbook`, `meals` | body | no (any subset) | Omitting `meals` leaves the existing schedule untouched; passing `[]` clears it. |

---

### `DELETE /api/plannings/{id}/`

Unlinks scheduled meals (`RecipePlanning`, `PROTECT` FK) before deleting the
planning itself.

**Auth:** `IsAuthenticated` + `CookbookItemPermission`

**Status codes**

| Status | Meaning |
| --- | --- |
| `204 No Content` | Deleted. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Insufficient rank (`creator` required). |
| `404 Not Found` | Doesn't exist / not visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `id` | integer | Planning id. |

---

## 5. Messaging (`messaging`)

Chat messages exist in two flavours of the same underlying resource: a
cookbook's **global channel**, and a specific **recipe's channel** within
that cookbook. There is deliberately no update route - a message can only be
posted or deleted, never edited.

### `GET /api/cookbooks/{cookbook_pk}/messages/`

Lists messages in the cookbook's global channel (`recipe` always `null`).

**Auth:** `IsAuthenticated` + `CanAccessCookbookMessages` (any role, including `reader`, can read)

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | Paginated list. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | `cookbook_pk` doesn't exist, or the caller isn't a member (and isn't staff) - a stranger can't tell the cookbook exists. |

**Parameters** (path + query)

| Name | Location | Type | Description |
| --- | --- | --- | --- |
| `cookbook_pk` | path | integer | Cookbook id. |
| `page` / `page_size` | query | integer | Pagination. |

---

### `POST /api/cookbooks/{cookbook_pk}/messages/`

Posts a message to the cookbook's global channel.

**Auth:** `IsAuthenticated` + `CanAccessCookbookMessages` (at least `commentator` role required to write)

**Status codes**

| Status | Meaning |
| --- | --- |
| `201 Created` | Message created. |
| `400 Bad Request` | Missing/invalid `content`/`canal`. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Member with `reader` role only (read access, no write). |
| `404 Not Found` | `cookbook_pk` doesn't exist / caller isn't a member. |

**Parameters** (path + body)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `cookbook_pk` | path | integer | yes | Cookbook id. |
| `content` | body | string | yes | Message text. |
| `canal` | body | string | yes | Free-text conversation channel label. |

**Workflow:** `author`, `cookbook` (from the URL) and `recipe=None` are always
set server-side, never accepted from the request body.

---

### `GET /api/cookbooks/{cookbook_pk}/messages/{pk}/`

Retrieves one message from the cookbook's global channel.

**Auth:** `IsAuthenticated` + `CanAccessCookbookMessages`

**Status codes**

| Status | Meaning |
| --- | --- |
| `200 OK` | The message. |
| `401 Unauthorized` | No/invalid access token. |
| `404 Not Found` | `cookbook_pk`/`pk` doesn't exist, or not visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Cookbook id. |
| `pk` | integer | Message id. |

---

### `DELETE /api/cookbooks/{cookbook_pk}/messages/{pk}/`

Deletes a message from the cookbook's global channel.

**Auth:** `IsAuthenticated` + `CanAccessCookbookMessages` + `CanDeleteMessage`

**Status codes**

| Status | Meaning |
| --- | --- |
| `204 No Content` | Deleted. |
| `401 Unauthorized` | No/invalid access token. |
| `403 Forbidden` | Caller is neither the message's author, nor the cookbook's admin, nor staff. |
| `404 Not Found` | `cookbook_pk`/`pk` doesn't exist, or not visible. |

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Cookbook id. |
| `pk` | integer | Message id. |

---

### `GET` / `POST /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/`

Same behaviour as the cookbook-level list/create routes above, scoped to a
specific recipe's channel instead of the cookbook's global one.

**Auth:** same as the cookbook-level equivalents.

**Status codes:** identical to the two routes above, plus:

| Status | Meaning |
| --- | --- |
| `404 Not Found` | Additionally returned if `recipe_pk` doesn't belong to `cookbook_pk` (`recipe.cookbook_id != cookbook_pk`) - a mismatched pair can't be used to leak or misfile a message. |

**Parameters** (path + query/body)

| Name | Location | Type | Description |
| --- | --- | --- | --- |
| `cookbook_pk` | path | integer | Cookbook id. |
| `recipe_pk` | path | integer | Recipe id; must be filed in `cookbook_pk`. |
| `content`, `canal` | body (`POST` only) | string | Same as the cookbook-level route. |
| `page` / `page_size` | query (`GET` only) | integer | Pagination. |

---

### `GET /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/{pk}/`

Retrieves one message from the recipe's channel.

**Auth/status codes:** identical to the cookbook-level retrieve route above,
plus the `recipe_pk`-mismatch `404` case.

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Cookbook id. |
| `recipe_pk` | integer | Recipe id. |
| `pk` | integer | Message id. |

---

### `DELETE /api/cookbooks/{cookbook_pk}/recipes/{recipe_pk}/messages/{pk}/`

Deletes a message from the recipe's channel.

**Auth/status codes:** identical to the cookbook-level delete route above,
plus the `recipe_pk`-mismatch `404` case.

**Parameters** (path)

| Name | Type | Description |
| --- | --- | --- |
| `cookbook_pk` | integer | Cookbook id. |
| `recipe_pk` | integer | Recipe id. |
| `pk` | integer | Message id. |
