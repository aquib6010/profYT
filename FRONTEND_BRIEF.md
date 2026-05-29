# Profitly — Frontend Brief (for Antigravity)

Build the frontend for **Profitly**, a revenue-analytics dashboard for YouTube creators.
The backend (FastAPI) already exists and is the source of truth — **do not invent
endpoints or change the auth model**. Build the UI to the contract below.

> One-liner: *"Profitly answers the question YouTube Studio doesn't — which of my
> videos actually made money, and what should I make more of?"*

---

## Stack constraints

- **React 18 + TypeScript + Vite.** Tailwind for styling. **TanStack Query** for data
  fetching. **Recharts** for charts. React Router for routing.
- The app **must run on `http://localhost:5173`** in dev. The backend's CORS allowlist
  is pinned to that exact origin. If you change the port, the session cookie is dropped
  and every request looks logged-out.
- Backend base URL comes from `import.meta.env.VITE_API_BASE` (default
  `http://localhost:8000`).

---

## Auth model — READ THIS FIRST (it's where generated frontends break)

Auth is **cookie-based sessions**, not tokens. There is no JWT, no `Authorization`
header, no localStorage. The backend sets an httpOnly `profitly_session` cookie.

Hard rules:

1. **Every `fetch`/request MUST set `credentials: "include"`.** Without it the cookie
   isn't sent and the user appears logged out. This is the #1 failure mode.
2. **The login action is a plain top-level navigation, NOT a fetch/XHR.** Render it as
   `<a href="{API_BASE}/auth/google/login">`. The browser must follow Google's redirect
   chain and let the backend set the cookie on the way back. Calling it with `fetch`
   will not work.
3. **`GET /auth/google/me` returning 401 means "anonymous" — that's a normal logged-out
   state, not an error.** Don't retry it; don't show an error toast. Just route to login.
4. After a successful login, the backend redirects the browser to `/dashboard`. After a
   failed login, it redirects to `/login?error=<CODE>` — show that error to the user.

---

## API contract (implemented — build against these now)

Base URL: `VITE_API_BASE` (e.g. `http://localhost:8000`).

### `GET /auth/google/login`
Top-level navigation only. 302-redirects to Google, then back to `/dashboard` (success)
or `/login?error=<CODE>` (failure). Render as an `<a href>`, never fetch.

### `GET /auth/google/me`
Who is signed in.
- **200**:
  ```json
  { "id": 2, "email": "x@gmail.com", "display_name": "X", "channel_id": "UC..." }
  ```
- **401**: not signed in (treat as anonymous, not an error).

### `POST /auth/google/logout`
Clears the session. Always **200** `{ "ok": true }`. After it resolves, send the user to
`/login` and invalidate any cached auth/analytics queries.

### `GET /api/analytics/summary`
Dashboard top cards. **401** if not signed in. **200**:
```json
{
  "channel": { "display_name": "Aquib Aquil", "channel_id": "UC..." },
  "has_data": true,
  "as_of": "2026-05-28",
  "window_days": 30,
  "revenue_last_30d": 158.68,
  "revenue_prev_30d": 270.98,
  "revenue_change_pct": -41.4,
  "views_last_30d": 194722,
  "videos_tracked": 50,
  "top_category": { "category": "tutorial", "revenue_usd": 80.96 }
}
```
- `has_data: false` → render an empty state ("No analytics yet for this channel…"),
  not a wall of zeros.
- `revenue_change_pct` can be `null` (no prior-window baseline) → render no badge.
- `top_category` can be `null`.
- Money is USD. `revenue_change_pct` positive = green/up, negative = red/down.
- `as_of` is the latest data date; the window is "last 30 days through `as_of`".

### `?error=` codes (on `/login?error=...`)
Map to friendly text:
| code | message |
|---|---|
| `access_denied` | You declined the permission request. Approve access to sign in. |
| `no_youtube_channel` | That Google account has no YouTube channel. Sign in with the account that owns your channel. |
| `token_exchange_failed` | Couldn't complete sign-in with Google. Please try again. |
| `userinfo_incomplete` | Google didn't return your account details. Please try again. |
| `youtube_api_*` (prefix) | YouTube API request failed. Make sure the APIs are enabled. |
| `userinfo_*` (prefix) | Couldn't read your Google profile. Please try again. |
| (anything else) | Sign-in failed (`<code>`). |

---

## Planned API (NOT built yet — scaffold the UI, stub the data)

These endpoints don't exist yet. Build the screens with loading skeletons / "coming
soon" states; wire them when the backend lands. Proposed shapes (subject to change):

- `GET /api/analytics/timeseries?metric=revenue|views|cpm` → daily series for charts:
  `[{ "date": "2026-05-01", "value": 12.34 }, ...]`
- `GET /api/videos` → table of videos with per-video lifetime revenue, category, views.
- `GET /api/forecast` → 30-day revenue forecast with conformal prediction interval:
  `{ "history": [...], "forecast": [{ "date", "yhat", "lower", "upper" }] }`
- `GET /api/anomalies` → flagged revenue/CPM shocks with a SHAP-style explanation.
- `GET /api/recommendations` → content-mix uplift suggestions with $ impact + CI.

---

## Screens

1. **Login** (`/login`)
   - Centered card. Headline + short value prop. One "Continue with Google" button
     (`<a href>` to login endpoint). Read-only-access reassurance line.
   - If `?error=` present, show a red alert with the mapped message above the button.
   - If already authenticated (`/me` 200), redirect to `/dashboard`.

2. **Dashboard** (`/dashboard`, protected)
   - Redirect to `/login` if `/me` is 401. While `/me` is loading, render nothing/skeleton
     (don't flash the login page).
   - Header: "Profitly" logo, nav, the signed-in email, and a "Sign out" button.
   - Cards from `/api/analytics/summary`: Revenue (last 30d) + change badge, Views
     (last 30d) + "N videos tracked", Top category + its revenue.
   - States: loading skeleton, error, and `has_data:false` empty state.
   - Below cards (planned): revenue trend chart, forecast chart, anomalies, recommendations
     — scaffold with placeholders.

3. **Video detail** (`/videos/:id`, planned) — per-video revenue, views, category,
   timeline. Stub for now.

---

## Visual direction

- Clean, trustworthy "fintech dashboard" feel. Light theme, slate/gray neutrals, a single
  brand accent (current code uses a blue `brand-600`). Generous whitespace, rounded-lg
  cards with subtle borders + shadow. Compact number formatting (`$1.2k`, `195K`).
  Up = emerald, down = red. Mobile-responsive grid.

## Definition of done

- Login → consent → lands on a populated dashboard, with the email + working Sign out in
  the header.
- Refresh keeps you logged in (cookie persists). Sign out returns you to login.
- All requests use `credentials: "include"`; app runs on `:5173`.
- Loading / error / empty states for every data view.
