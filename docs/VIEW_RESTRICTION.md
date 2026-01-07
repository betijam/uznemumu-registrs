# View Restriction (Metered Access) - Technical Documentation

## Overview

This system limits anonymous users to **5 free company profile views**. After that, they must register/login for unlimited access.

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser   │────▶│  Next.js (FE)    │────▶│  FastAPI (BE)   │
│             │     │  Middleware +    │     │  access_control │
│  Cookie:    │     │  Server Comp.    │     │                 │
│  c360_free_ │     │                  │     │  X-View-Count   │
│  views=3    │     │  X-View-Count: 3 │     │  header check   │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Components

### 1. Frontend Middleware (`frontend/src/middleware.ts`)

**Purpose**: Track and increment view count on profile pages.

**Logic**:
```typescript
// Only count views on company/person profile pages
const isProfilePage = /^(\/[a-z]{2})?\/(company|person)\/(\d+|P-[a-fA-F0-9]+)$/.test(pathname);

// Read current count from cookie
const cookie = request.cookies.get('c360_free_views');
let viewCount = cookie ? parseInt(cookie.value, 10) : 0;

// Increment on profile pages
if (isProfilePage) {
    viewCount = viewCount + 1;
}

// Set header for backend
requestHeaders.set('X-View-Count', viewCount.toString());

// Update cookie (30 day expiry)
response.cookies.set('c360_free_views', viewCount.toString(), {
    maxAge: 60 * 60 * 24 * 30,
    path: '/',
    sameSite: 'lax'
});
```

**Key Points**:
- Uses regex to match ONLY `/company/[id]` or `/person/[hash]` paths
- Does NOT count: home page, search, industry pages, etc.
- Cookie persists for 30 days

---

### 2. Server Component (`frontend/src/app/[locale]/company/[id]/page.tsx`)

**Purpose**: Read cookie and pass view count to backend.

**Why read cookie directly?**
The middleware sets headers, but due to `next-intl` middleware chaining, headers don't propagate reliably to Server Components. Reading the cookie directly is more reliable.

```typescript
const cookieStore = await cookies();
const viewCountCookie = cookieStore.get('c360_free_views');
const viewCount = viewCountCookie ? parseInt(viewCountCookie.value, 10) : 0;

// Pass to backend
const apiHeaders = {
    'X-View-Count': viewCount.toString(),
    // Also pass auth token if present
};
```

---

### 3. Backend Access Control (`backend/app/utils/access_control.py`)

**Purpose**: Decide if user gets full data or restricted "teaser" view.

```python
async def check_access(request: Request) -> bool:
    # 1. Logged in users -> Full access
    auth_header = request.headers.get('Authorization')
    if auth_header and valid_jwt(auth_header):
        return True
    
    # 2. Search engine bots -> Teaser only (SEO safety)
    if is_bot(request):
        return False
    
    # 3. Anonymous users -> Check view count
    view_count = int(request.headers.get('X-View-Count', '0'))
    
    ALLOWED_FREE_VIEWS = 5  # First 5 views are free
    return view_count < ALLOWED_FREE_VIEWS
```

---

### 4. Data Filtering (`backend/app/routers/companies.py`)

**Purpose**: Remove sensitive data for restricted users.

```python
has_full_access = await check_access(request)

# ... fetch data from cache ...

# Filter for restricted users
if not has_full_access:
    full_profile["ubos"] = []      # Hide beneficial owners
    full_profile["members"] = []    # Hide shareholders  
    full_profile["officers"] = []   # Hide board members
    # financial_history is kept visible for Overview tab

return full_profile
```

---

## Configuration

| Setting | Location | Value |
|---------|----------|-------|
| Free view limit | `access_control.py` | `ALLOWED_FREE_VIEWS = 5` |
| Cookie name | `middleware.ts` | `c360_free_views` |
| Cookie expiry | `middleware.ts` | 30 days |

---

## User Flow

```
Anonymous User Journey:
========================
1. Visit home page         → No count increment
2. Search for company      → No count increment  
3. Click company #1        → Count = 1, FULL ACCESS ✓
4. Click company #2        → Count = 2, FULL ACCESS ✓
5. Click company #3        → Count = 3, FULL ACCESS ✓
6. Click company #4        → Count = 4, FULL ACCESS ✓
7. Click company #5        → Count = 5, FULL ACCESS ✓
8. Click company #6        → Count = 6, RESTRICTED ✗
   └── Shows teaser: "Register to see full data"

After Login:
============
→ Always FULL ACCESS (JWT token validation)
```

---

## Files Modified

| File | Changes |
|------|---------|
| `frontend/src/middleware.ts` | View counting logic, cookie management |
| `frontend/src/app/[locale]/company/[id]/page.tsx` | Cookie reading, header forwarding |
| `backend/app/utils/access_control.py` | Access decision logic |
| `backend/app/routers/companies.py` | Data filtering for restricted users |

---

## Current Status

⚠️ **TEMPORARILY DISABLED** for debugging.

In `access_control.py`, there's a `return True` at the start that bypasses all checks. Remove it to re-enable metered access:

```python
# TEMPORARY: Force full access to debug data issue
logger.info("[ACCESS] TEMPORARY: Granting full access for debugging")
return True  # <-- DELETE THIS LINE TO RE-ENABLE
```

---

## Future Improvements

1. **Per-company counting**: Don't count the same company twice
2. **Daily reset**: Reset counter every 24 hours instead of 30-day cookie
3. **IP-based fallback**: For users who block cookies
4. **Analytics**: Track conversion rate (free views → registrations)
