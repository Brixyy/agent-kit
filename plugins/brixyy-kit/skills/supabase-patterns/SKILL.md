---
name: supabase-patterns
description: |
  Complete Supabase development skill covering Auth, RLS policies, queries, Edge Functions,
  Storage, migrations, types, and real-time subscriptions.

  Use when working with Supabase auth flows, writing RLS policies, creating Edge Functions,
  managing storage buckets, running migrations, or generating TypeScript types.
version: "1.0.0"
author: Brixyy
---

# Supabase Complete Development Guide

## Projekty a účty

Který Supabase projekt (ref) a organizace patří k projektu, je v `AGENTS.md` daného projektu — sem ID nepatří (repozitář je veřejný).

Produkční databázi měň jen migracemi přes CI/workflow projektu a po souhlasu uživatele (hlídá hook pojistka).

### Key Convention (since 11/2025)

| New Name | Old Name | Usage |
|----------|----------|-------|
| `Publishable key` (`sb_publishable_...`) | `anon key` | Client-side, safe to expose |
| `Secret key` (`sb_secret_...`) | `service_role key` | Server-side only, never expose |

- CLI redacts `sb_secret_*` - sync-env uses legacy JWT service_role (works the same)

---

## Auth

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com', password: 'secure123',
  options: { data: { full_name: 'Jan Novak', role: 'candidate' } },
})

// Sign in (password)
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com', password: 'secure123',
})

// Sign in (OAuth)
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: { redirectTo: `${window.location.origin}/auth/callback` },
})

// Sign out
const { error } = await supabase.auth.signOut()

// Session & user
const { data: { session } } = await supabase.auth.getSession()
const { data: { user } } = await supabase.auth.getUser()

// Listen for auth changes (cleanup on unmount!)
const { data: { subscription } } = supabase.auth.onAuthStateChange(
  (event, session) => { /* SIGNED_IN | SIGNED_OUT | TOKEN_REFRESHED */ }
)
subscription.unsubscribe()
```

**Do:** Use `getUser()` for server-side validation. Set up `onAuthStateChange` early. Use `redirectTo` with OAuth.
**Don't:** Trust `getSession()` alone on server. Store tokens manually. Forget to unsubscribe.

---

## RLS (Row Level Security)

```sql
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- SELECT: own data
CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT USING (auth.uid() = user_id);

-- SELECT: public
CREATE POLICY "Public listings"
  ON public.jobs FOR SELECT USING (status = 'published');

-- INSERT: own data
CREATE POLICY "Users can create profile"
  ON public.profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

-- UPDATE: own data (USING + WITH CHECK)
CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- DELETE: own data
CREATE POLICY "Users can delete own posts"
  ON public.posts FOR DELETE USING (auth.uid() = author_id);

-- Role-based
CREATE POLICY "Admins full access" ON public.profiles FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_roles.user_id = auth.uid() AND user_roles.role = 'admin'
  ));
```

**Testing RLS:**
```sql
SET request.jwt.claims = '{"sub": "user-uuid"}'; SET role = 'authenticated';
SELECT * FROM public.profiles;
RESET role; RESET request.jwt.claims;
```

**Do:** Enable RLS on every user-data table. Use `WITH CHECK` on INSERT/UPDATE. Test both roles.
**Don't:** Forget policies after enabling RLS. Use `USING (true)` on sensitive tables. Skip junction tables.

---

## Queries

```typescript
// Select with joins and filters
const { data } = await supabase.from('posts')
  .select(`id, title, profiles (full_name, avatar_url)`)
  .eq('status', 'published').gte('salary', 50000)
  .order('created_at', { ascending: false }).limit(10)

// Insert (always chain .select() to get returned data)
const { data } = await supabase.from('profiles')
  .insert({ user_id: userId, full_name: 'Jan' }).select()

// Update (always include .eq() filter!)
const { data } = await supabase.from('profiles')
  .update({ full_name: 'Updated' }).eq('user_id', userId).select()

// Delete
const { error } = await supabase.from('posts').delete().eq('id', postId)

// Pagination
const { data, count } = await supabase.from('jobs')
  .select('*', { count: 'exact' })
  .range(page * 20, (page + 1) * 20 - 1)
```

**Do:** Chain `.select()` after insert/update. Use specific columns. Handle errors.
**Don't:** Forget `.eq()` on update/delete. Use `.single()` when 0/many rows possible.

---

## Edge Functions

```bash
npx supabase functions new my-function    # Create
npx supabase functions deploy my-function --project-ref <ref>  # Deploy
npx supabase functions serve              # Test locally
npx supabase secrets set MY_SECRET=value --project-ref <ref>   # Secrets
```

```typescript
// supabase/functions/my-function/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    )
    const { data, error } = await supabase.from('profiles').select('*').limit(10)
    if (error) throw error
    return new Response(JSON.stringify(data), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
```

```typescript
// Client invocation
const { data, error } = await supabase.functions.invoke('my-function', { body: { name: 'Jan' } })
```

**Do:** Handle CORS preflight. Use `SERVICE_ROLE_KEY` in functions. Test locally first.
**Don't:** Import from `npm:` (use `esm.sh`). Expose `SERVICE_ROLE_KEY` client-side.

---

## Storage

```typescript
// Upload
await supabase.storage.from('avatars')
  .upload(`${userId}/avatar.png`, file, { cacheControl: '3600', upsert: true })

// Download
const { data } = await supabase.storage.from('avatars').download(`${userId}/avatar.png`)

// Public URL
const { data } = supabase.storage.from('avatars').getPublicUrl(`${userId}/avatar.png`)
```

```sql
-- Bucket creation (in migration)
INSERT INTO storage.buckets (id, name, public) VALUES ('avatars', 'avatars', true);

-- Storage RLS: upload to own folder
CREATE POLICY "Upload own avatar" ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Public read" ON storage.objects FOR SELECT
  USING (bucket_id = 'avatars');
```

**Do:** Use user_id folder structure. Set `upsert: true` for replacements. Add RLS on `storage.objects`.
**Don't:** Skip RLS on storage. Upload >50MB without resumable upload.

---

## Migrations

```bash
npx supabase migration new create_profiles   # Create
npx supabase db push --project-ref <ref>      # Push to remote
npx supabase db reset                         # Reset local
npx supabase migration list --project-ref <ref>  # Status
```

```sql
-- supabase/migrations/<timestamp>_create_profiles.sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  CONSTRAINT unique_user_id UNIQUE (user_id)
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
-- Include RLS policies in same migration
```

**Do:** Include RLS in table creation migration. Use `ON DELETE CASCADE` for auth.users FK. Test with `db reset`.
**Don't:** Edit pushed migrations. Forget RLS. Use `DROP TABLE` without `IF EXISTS`.

---

## TypeScript Types

```bash
npx supabase gen types typescript --project-id <ref> > src/types/database.ts
```

```typescript
import type { Database } from '@/types/database'
const supabase = createClient<Database>(url, key)
// Fully typed queries
```

**Do:** Regenerate after every migration. Use `Database` generic. Commit to git.
**Don't:** Manually edit generated types.

---

## Real-time

```typescript
// Subscribe to changes
const channel = supabase.channel('changes')
  .on('postgres_changes', {
    event: '*', schema: 'public', table: 'profiles',
    filter: `user_id=eq.${userId}`,
  }, (payload) => console.log(payload))
  .subscribe()

// Presence
const channel = supabase.channel('room-1')
channel.on('presence', { event: 'sync' }, () => {
  console.log('Online:', channel.presenceState())
}).subscribe(async (status) => {
  if (status === 'SUBSCRIBED') await channel.track({ user_id: userId })
})

// Cleanup (always!)
channel.unsubscribe()
```

**Prerequisite:** `ALTER PUBLICATION supabase_realtime ADD TABLE profiles;`

**Do:** Unsubscribe on unmount. Use filters. Enable publication on table.
**Don't:** Subscribe without filters. Use for high-frequency updates without throttling.

---

## Environment Variables

```bash
# .env.local generated by sync-env.sh - NEVER edit manually
VITE_SUPABASE_URL=https://<ref>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

```typescript
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,
)
```

**Do:** Use `sync-env.sh` to generate `.env.local`.
**Don't:** Edit `.env.local` manually - next sync overwrites it.
