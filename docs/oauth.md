# OAuth

🇬🇧 English | [🇫🇷 Français](oauth.fr.md)

## Summary

- [Overview](#overview)
- [Routes concerned by OAuth](#routes-concerned-by-oauth)
- [How the Microsoft flow works](#how-the-microsoft-flow-works)
- [Linking Microsoft to an existing account](#linking-microsoft-to-an-existing-account)
- [Environment variables](#environment-variables)
- [Using it from a frontend](#using-it-from-a-frontend)
- [Response shape](#response-shape)
- [Error handling](#error-handling)
- [What gets written to the database](#what-gets-written-to-the-database)
- [Adding another provider](#adding-another-provider)
- [Tests](#tests)

This document explains how OAuth login (currently: Microsoft / Entra ID) is
wired into the API, which routes are involved, and how a frontend is
expected to drive the flow end to end. For the `User` / `OAuthUser` table
definitions, see [`docs/database.md`](database.md).

---

## Overview

A user can either register with a local password (`/api/users/register/`)
or sign in through an external identity provider. Every external identity
is stored as a row in `OAuth_user`, linked to a `user` row - so a single
account can be reached through several providers over time, or created
from scratch the first time someone signs in with one.

A user can also **link** a Microsoft identity to an account they already
have - typically one created with a local password - after the fact, from
the settings page, without signing out first. This is a separate route
from the login one; see
[Linking Microsoft to an existing account](#linking-microsoft-to-an-existing-account)
below.

`OAuth_user.provider` is a free-form string, not an enum: today only
`"microsoft"` is implemented, but nothing in the schema restricts it to
that value.

Because the confidential client secret (`AZURE_CLIENT_SECRET`) must never
reach the browser, **the backend - not the frontend - performs the
authorization-code exchange with Microsoft**. The frontend's only jobs are:
send the user to Microsoft, catch the `code` Microsoft sends back, and hand
that `code` to the backend.

## Routes concerned by OAuth

| Method | Route                        | Auth      | Purpose                                                                          |
| ------ | ---------------------------- | --------- | --------------------------------------------------------------------------------- |
| `POST` | `/api/users/oauth/microsoft/` | `AllowAny` | Exchanges a Microsoft authorization `code` for tokens; creates or links the user (login/registration) |
| `POST` | `/api/users/oauth/microsoft/link/` | `IsAuthenticated` | Exchanges a `code` and attaches the Microsoft identity to the **caller's own, already-authenticated** account |
| `POST` | `/api/users/token/refresh/`  | `AllowAny` | Refreshes an expired access token (shared with password login)                   |
| `GET`  | `/api/users/me/`             | `IsAuthenticated` | Fetches the profile of whoever the current access token belongs to        |

`/api/users/oauth/microsoft/` and `/api/users/oauth/microsoft/link/` are the
only two OAuth-specific routes. Everything after them (refreshing tokens,
calling `/me/`, etc.) is indistinguishable from a normal password login -
every flow converges on the same JWT pair (linking doesn't even issue a new
one - see below).

## How the Microsoft flow works

```mermaid
sequenceDiagram
    participant Browser
    participant Frontend as Frontend (Nuxt)
    participant Backend as Backend (/api/users/oauth/microsoft/)
    participant MS as Microsoft identity platform
    participant Graph as Microsoft Graph

    Browser->>MS: 1. Redirect to /oauth2/v2.0/authorize?client_id=...&redirect_uri=...
    MS->>Browser: 2. User logs in / consents
    MS->>Frontend: 3. Redirect to AZURE_REDIRECT_URI?code=...
    Frontend->>Backend: 4. POST { code }
    Backend->>MS: 5. Exchange code for access_token (MSAL, uses AZURE_CLIENT_SECRET)
    MS-->>Backend: access_token
    Backend->>Graph: 6. GET /v1.0/me (Bearer access_token)
    Graph-->>Backend: displayName, givenName, surname, mail, userPrincipalName
    Backend->>Graph: 7. GET /v1.0/me/photo/$value (existence check only)
    Graph-->>Backend: 200 (has photo) or 404
    Backend->>Backend: 8. Get-or-create User + OAuthUser(provider="microsoft")
    Backend-->>Frontend: 9. { user, access, refresh }
    Frontend->>Frontend: 10. Store tokens, use `access` as Bearer on future API calls
```

Step by step, on the backend side (`backend/users/oauth_microsoft.py`):

1. `exchange_code_for_token(code)` builds an MSAL `ConfidentialClientApplication`
   from `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_AUTHORITY` and calls
   `acquire_token_by_authorization_code(code, scopes=["User.Read"], redirect_uri=AZURE_REDIRECT_URI)`.
   The `redirect_uri` passed here **must match exactly** the one used to
   obtain the code in step 1 of the diagram - Microsoft rejects the
   exchange otherwise.
2. `fetch_microsoft_profile(access_token)` calls Graph's `/me` endpoint to
   get `mail` / `userPrincipalName`, `givenName`, `surname`.
3. `has_microsoft_photo(access_token)` probes `/me/photo/$value` to check
   whether the account has a picture, without downloading it.
4. `get_or_create_user_from_microsoft(profile, access_token)` matches an
   existing `User` by email, or creates one, then `update_or_create`s the
   linked `OAuthUser(provider="microsoft")` row.
5. The view (`MicrosoftOAuthView`) issues the same JWT pair as
   `RegisterView` / `LoginView` and returns `{ user, access, refresh }`.

If the code is invalid/expired, or the Microsoft account has no email, the
view returns `400 Bad Request` before any database write happens.

## Linking Microsoft to an existing account

Besides signing in, an **already-authenticated** user can attach their
Microsoft identity to the very account they're logged into - e.g. someone
who registered with a local password and now wants "Sign in with
Microsoft" to work too. This is the settings page's "Lier mon compte
Microsoft" action, backed by a separate route,
`POST /api/users/oauth/microsoft/link/` (`LinkMicrosoftOAuthView`), and a
separate service function, `link_microsoft_account()` in
`backend/users/oauth_microsoft.py`.

It reuses the exact same code-exchange/profile-fetch mechanics as the login
flow (`exchange_code_for_token`, `fetch_microsoft_profile`,
`has_microsoft_photo`), but everything after that differs:

| | Login (`/oauth/microsoft/`) | Link (`/oauth/microsoft/link/`) |
| --- | --- | --- |
| **Auth required** | `AllowAny` | `IsAuthenticated` |
| **Which user** | Matched/created by the profile's email | Always `request.user` - never matched/created by email |
| **On success** | Issues a fresh JWT pair | Issues **no tokens** - the caller's existing session keeps working as-is |
| **Side effect on the account** | None beyond creating it | `user.email` is overwritten with the Microsoft profile's email, and `user.set_unusable_password()` is called |

That last row matters: **linking is one-way and destructive to the local
password**. Once linked, the account can only sign in through Microsoft -
the local password stops working entirely, it isn't kept as a fallback.
The frontend's confirmation modal (`pages/settings.vue`) says exactly this
before starting the redirect.

```mermaid
sequenceDiagram
    participant Browser
    participant Frontend as Frontend (Nuxt, /settings)
    participant Backend as Backend (/api/users/oauth/microsoft/link/)
    participant MS as Microsoft identity platform
    participant Graph as Microsoft Graph

    Browser->>MS: 1. Redirect to /oauth2/v2.0/authorize?...&state=link
    MS->>Browser: 2. User logs in / consents
    MS->>Frontend: 3. Redirect to AZURE_REDIRECT_URI?code=...&state=link
    Frontend->>Backend: 4. POST { code }, Authorization: Bearer <access> (current session)
    Backend->>MS: 5. Exchange code for access_token (MSAL, uses AZURE_CLIENT_SECRET)
    MS-->>Backend: access_token
    Backend->>Graph: 6. GET /v1.0/me (Bearer access_token)
    Graph-->>Backend: displayName, givenName, surname, mail, userPrincipalName
    Backend->>Graph: 7. GET /v1.0/me/photo/$value (existence check only)
    Graph-->>Backend: 200 (has photo) or 404
    Backend->>Backend: 8. request.user.email = profile email; set_unusable_password(); update_or_create OAuthUser(provider="microsoft")
    Backend-->>Frontend: 9. { user, detail }
    Frontend->>Frontend: 10. Update cached user - no new tokens to store, the session is unchanged
```

Since linking reuses the same Azure app registration and redirect URI as
login (there's no second one to configure), the frontend needs a way to
tell a login attempt from a link attempt apart on the shared callback page.
It does this with the OAuth `state` parameter, which Microsoft round-trips
verbatim:

1. `useOAuth().startOAuth("microsoft", mode)` (`frontend/app/composables/useOAuth.ts`)
   appends `state=login` or `state=link` to the authorize URL depending on
   which action triggered it - the settings page calls it with `"link"`,
   everywhere else defaults to `"login"`.
2. `finishOAuth("microsoft")`, called from the shared callback page
   (`pages/connect/microsoft/callback.vue`), reads `route.query.state` back
   and branches: `"link"` posts to `/oauth/microsoft/link/` and calls
   `updateUser()` (no tokens to store); anything else posts to
   `/oauth/microsoft/` and calls `setSession()` as usual.
3. On success, the callback page redirects to `/settings?linked=microsoft`
   (a login instead redirects to `/home`); a `linked=microsoft` query param
   is what triggers the "Compte Microsoft lié avec succès." toast on
   `pages/settings.vue`.

**Fails with `400 Bad Request`** if `code` is missing, the exchange with
Microsoft fails the same way it can for login, the Graph profile has no
email, **or that email already belongs to a *different* existing
account** (`User.objects.exclude(pk=user.pk).filter(email__iexact=email).exists()`)
- linking can't be used to silently take over someone else's account.

## Environment variables

Defined in the repo-root `.env` (read by `config/settings.py` the same way
as `DATABASE_*`; injected via `env_file` in `docker-compose.dev.yml` inside
containers):

| Variable              | Meaning                                                                          |
| ---------------------- | --------------------------------------------------------------------------------- |
| `AZURE_CLIENT_ID`      | Application (client) ID of the Azure AD app registration                        |
| `AZURE_TENANT_ID`      | Azure AD tenant ID the app is registered in                                      |
| `AZURE_CLIENT_SECRET`  | Confidential client secret - **backend only**, never sent to the frontend        |
| `AZURE_REDIRECT_URI`   | Must match a redirect URI registered on the Azure app (currently the frontend's `/connect/microsoft/callback` page) |
| `AZURE_AUTHORITY`      | Microsoft identity platform authority, e.g. `https://login.microsoftonline.com/common/v2.0` |

All five have safe empty-string defaults in `settings.py` so the app still
boots without them configured; the OAuth route itself will fail (400/500)
until they're set.

## Using it from a frontend

No MSAL.js or client-side library is required, since the backend performs
the code exchange. A frontend integration only has to do three things:

**1. Redirect the browser to Microsoft to start the login:**

```js
const params = new URLSearchParams({
  client_id: AZURE_CLIENT_ID, // public, safe to expose
  response_type: "code",
  redirect_uri: "http://localhost:3000/connect/microsoft/callback",
  response_mode: "query",
  scope: "openid profile email User.Read",
});

window.location.href = `${AZURE_AUTHORITY}/oauth2/v2.0/authorize?${params}`;
```

**2. On the callback page (`/connect/microsoft/callback`), read `code` from
the query string and send it to the backend:**

```js
const code = new URLSearchParams(window.location.search).get("code");

const res = await fetch("/api/users/oauth/microsoft/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ code }),
});

if (!res.ok) {
  const { detail } = await res.json();
  throw new Error(detail);
}

const { user, access, refresh } = await res.json();
```

**3. Store `access` / `refresh` the same way as after a password login**
(e.g. Pinia store + secure storage), and attach `Authorization: Bearer
<access>` to subsequent API calls. When `access` expires, `POST` `refresh`
to `/api/users/token/refresh/` to get a new one - this part is not
provider-specific.

This three-step shape is also what a **linking** integration reuses -
same redirect, same callback page - just gated behind an existing session
and posting to a different route with no tokens to store afterwards. See
[Linking Microsoft to an existing account](#linking-microsoft-to-an-existing-account)
for the exact differences and how the frontend tells the two attempts
apart on the shared callback page.

## Response shape

**Login (`/oauth/microsoft/`), success (`200 OK`)** - identical envelope to
`/api/users/login/` and `/api/users/register/`:

```json
{
  "user": {
    "id": 42,
    "username": "jane.doe",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@contoso.com",
    "profile_icon": "https://graph.microsoft.com/v1.0/me/photo/$value",
    "is_oauth": true,
    "created_at": "2026-07-25T10:00:00Z",
    "updated_at": "2026-07-25T10:00:00Z"
  },
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

**Link (`/oauth/microsoft/link/`), success (`200 OK`)** - no token pair
(the caller's existing session is untouched), just the updated user plus a
confirmation message:

```json
{
  "user": {
    "id": 42,
    "username": "jane.doe",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@contoso.com",
    "profile_icon": "https://graph.microsoft.com/v1.0/me/photo/$value",
    "is_oauth": true,
    "created_at": "2026-07-25T10:00:00Z",
    "updated_at": "2026-07-25T10:00:00Z"
  },
  "detail": "Microsoft account linked successfully. You can only sign in with Microsoft from now on."
}
```

`is_oauth` (`UserSerializer.get_is_oauth`, `user.oauth_accounts.exists()`)
is what the frontend checks to decide whether to show password-related
settings fields versus the "link Microsoft" call to action - see
`pages/settings.vue`.

## Error handling

**Login (`/oauth/microsoft/`)** - `400 Bad Request` in three cases, all
returned as `{ "detail": "<message>" }`:

- `code` missing from the request body (serializer validation).
- Microsoft rejects the code exchange (expired/already-used code, wrong
  `redirect_uri`, revoked consent, ...).
- The Graph profile has neither `mail` nor `userPrincipalName` to key the
  account on.

**Link (`/oauth/microsoft/link/`)** - the same three cases, plus:

- `401 Unauthorized` if there's no valid access token - unlike login, this
  route requires an existing session.
- `400 Bad Request` if the Microsoft account's email already belongs to a
  **different** existing account (`{ "detail": "This Microsoft account's
  email is already used by another account." }`) - prevents linking from
  being used to silently take over someone else's account.

## What gets written to the database

### Login / registration (`/oauth/microsoft/`)

| Field                    | Source                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `User.username`           | Local part of `userPrincipalName` (or `mail`), de-duplicated with a numeric suffix if taken |
| `User.first_name`         | Graph `givenName`                                          |
| `User.last_name`          | Graph `surname`                                            |
| `User.email`              | Graph `mail` (fallback: `userPrincipalName`)                |
| `User.profile_icon`       | `https://graph.microsoft.com/v1.0/me/photo/$value` if the account has a photo, else empty |
| `User.password`           | Unusable (`set_unusable_password()`) - OAuth-only accounts don't get a local password |
| `OAuthUser.provider`      | `"microsoft"`                                               |
| `OAuthUser.provider_url`  | `AZURE_AUTHORITY`                                           |
| `OAuthUser.profile_icon`  | Same Graph photo URL as `User.profile_icon`                 |
| `OAuthUser.domain`        | Domain part of the email (e.g. `contoso.com`)                |

Note the stored photo value is the **Graph API endpoint**, not a public
image URL - fetching it requires a valid Microsoft access token as a
`Bearer` header, so a frontend `<img src>` can't point at it directly. If a
plain, browser-loadable image URL is needed later, the photo will have to
be downloaded once and re-hosted (e.g. object storage) instead of only
storing the Graph link.

An existing user is matched **by email** (`OAuthUser` has no separate
external-id column), so if an account with the same email already exists
(local or via another provider), the Microsoft identity is linked to it
instead of creating a duplicate user.

### Linking an existing account (`/oauth/microsoft/link/`)

No new `User` row is ever created here - `request.user` is updated in
place:

| Field                    | Source                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `User.username`           | **Untouched** - unlike login/registration, linking never derives a username from the Microsoft profile |
| `User.first_name`/`last_name` | **Untouched**                                          |
| `User.email`               | Overwritten with Graph `mail` (fallback: `userPrincipalName`) |
| `User.password`           | Overwritten to unusable (`set_unusable_password()`) - any previous local password stops working |
| `OAuthUser.provider`      | `"microsoft"` (`update_or_create`d - re-linking after unlinking just refreshes the existing row rather than duplicating it) |
| `OAuthUser.provider_url`  | `AZURE_AUTHORITY`                                           |
| `OAuthUser.profile_icon`  | Graph photo URL if the account has a photo, else empty (`User.profile_icon` itself is **not** touched by linking) |
| `OAuthUser.domain`        | Domain part of the (new) email                               |

Because `User.email` is overwritten, a subsequent Microsoft *login* with
this same Microsoft account will match this user by email as expected -
but a future *local* password reset/change flow keyed on the old email
address would no longer find this account.

## Adding another provider

Because `OAuthUser.provider` is a plain string, adding Google/GitHub/etc.
later doesn't require a schema change - just:

1. A new service module (`users/oauth_<provider>.py`) mirroring
   `oauth_microsoft.py`: exchange whatever code/token the provider issues,
   fetch its profile endpoint, call `get_or_create_user_from_<provider>`
   with `provider="<provider>"`.
2. A new view + route under `/api/users/oauth/<provider>/`.
3. New provider-specific settings (client id/secret/redirect URI).

The email-based linking logic can be factored out of
`get_or_create_user_from_microsoft` if a second provider is added, so both
share the same "match by email, else create" behavior.

## Tests

`backend/tests/users/microsoft_oauth_test.py` covers both routes end to end
with Microsoft mocked out (`_confidential_client` and `requests.get`
patched) - no real network calls or Microsoft account are needed. The
linking-specific cases (`test_link_microsoft_requires_authentication`,
`test_local_user_can_link_microsoft_account`,
`test_linking_microsoft_account_already_used_by_another_user_fails`,
`test_link_microsoft_rejects_get_requests`) live in the same file, below
the login/registration ones. Run it with:

```bash
docker compose -f docker-compose.dev.yml exec backend uv run pytest tests/users/microsoft_oauth_test.py -v
```
