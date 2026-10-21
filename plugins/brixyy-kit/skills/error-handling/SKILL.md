---
name: error-handling
description: Error handling patterns for React + Supabase + TypeScript. Covers async/await, Error Boundaries, Supabase errors, form validation, toast notifications, and logging.
version: "1.0.0"
author: Brixyy
---

# Error Handling Patterns

Consistent error handling across React + Supabase + TypeScript projects.

---

## 1. Async/Await — Try/Catch

```typescript
// DON'T — unhandled promise rejection
async function fetchUsers() {
  const response = await fetch('/api/users');
  const data = await response.json();
  return data;
}

// DON'T — catching but swallowing the error
try {
  await saveData(payload);
} catch (e) {
  // silently ignored
}

// DO — proper error handling with typed errors
async function fetchUsers(): Promise<User[]> {
  try {
    const response = await fetch('/api/users');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: unknown = await response.json();
    return userArraySchema.parse(data); // Zod validation
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Invalid API response shape:', error.issues);
      throw new Error('Server returned unexpected data format');
    }
    throw error; // re-throw network errors etc.
  }
}
```

### Result pattern (alternative to try/catch)

```typescript
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function fetchUsers(): Promise<Result<User[]>> {
  try {
    const res = await fetch('/api/users');
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { ok: true, data };
  } catch {
    return { ok: false, error: 'Network error' };
  }
}

// Usage — forces caller to handle both cases
const result = await fetchUsers();
if (!result.ok) {
  toast.error(result.error);
  return;
}
renderUsers(result.data);
```

---

## 2. Supabase Error Handling

```typescript
// DON'T — ignoring the error field
const { data } = await supabase.from('users').select('*');
// data could be null if there's an error!

// DO — always check error
const { data, error } = await supabase
  .from('users')
  .select('id, email, name')
  .eq('role', 'admin');

if (error) {
  console.error('Supabase query failed:', error.message, error.code);
  throw new Error(`Failed to fetch users: ${error.message}`);
}

// data is now guaranteed non-null
return data;
```

### Supabase helper wrapper

```typescript
async function supabaseQuery<T>(
  queryFn: () => Promise<{ data: T | null; error: { message: string; code: string } | null }>,
  context: string,
): Promise<T> {
  const { data, error } = await queryFn();

  if (error) {
    console.error(`[${context}]`, error.message, error.code);
    throw new Error(`${context}: ${error.message}`);
  }

  if (data === null) {
    throw new Error(`${context}: No data returned`);
  }

  return data;
}

// Usage
const users = await supabaseQuery(
  () => supabase.from('users').select('*').eq('active', true),
  'fetchActiveUsers',
);
```

### Auth error handling

```typescript
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
});

if (error) {
  switch (error.status) {
    case 400:
      toast.error('Neplatný e-mail nebo heslo');
      break;
    case 422:
      toast.error('E-mail není ve správném formátu');
      break;
    case 429:
      toast.error('Příliš mnoho pokusů, zkuste to později');
      break;
    default:
      toast.error('Přihlášení selhalo');
      console.error('Auth error:', error.message, error.status);
  }
  return;
}
```

---

## 3. React Error Boundaries

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
    console.error('ErrorBoundary:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="glass-card p-6 text-center">
          <h3 className="text-destructive font-medium">Něco se pokazilo</h3>
          <p className="text-muted-foreground text-sm mt-2">
            {this.state.error?.message}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Zkusit znovu
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### Where to place Error Boundaries

```tsx
// DON'T — one boundary at the top only
<ErrorBoundary>
  <App />
</ErrorBoundary>

// DO — granular boundaries around risky sections
<Layout>
  <ErrorBoundary fallback={<SidebarFallback />}>
    <Sidebar />
  </ErrorBoundary>
  <main>
    <ErrorBoundary fallback={<DashboardFallback />}>
      <Dashboard />
    </ErrorBoundary>
  </main>
</Layout>
```

---

## 4. Form Validation (Zod + React Hook Form)

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Neplatný e-mail'),
  name: z.string().min(2, 'Jméno musí mít alespoň 2 znaky'),
  age: z.coerce.number().min(18, 'Musíte být starší 18 let'),
});

type FormValues = z.infer<typeof schema>;

function UserForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await createUser(values);
      toast.success('Uživatel vytvořen');
    } catch (error) {
      if (error instanceof ApiError && error.field) {
        // Server-side validation error — show on specific field
        setError(error.field as keyof FormValues, {
          message: error.message,
        });
      } else {
        // General error — show as toast
        toast.error('Nepodařilo se vytvořit uživatele');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <Input {...register('email')} placeholder="E-mail" />
        {errors.email && (
          <p className="text-destructive text-sm mt-1">{errors.email.message}</p>
        )}
      </div>
      <div>
        <Input {...register('name')} placeholder="Jméno" />
        {errors.name && (
          <p className="text-destructive text-sm mt-1">{errors.name.message}</p>
        )}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Ukládání...' : 'Uložit'}
      </Button>
    </form>
  );
}
```

---

## 5. Fetch/API Error Handling

```typescript
// Custom error class for API errors
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public field?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      body.message ?? `Request failed (${response.status})`,
      response.status,
      body.field,
    );
  }

  return response.json() as Promise<T>;
}

// Usage in components
async function handleDelete(id: string) {
  try {
    await apiRequest(`/api/users/${id}`, { method: 'DELETE' });
    toast.success('Smazáno');
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 403) {
        toast.error('Nemáte oprávnění');
      } else if (error.status === 404) {
        toast.error('Záznam nenalezen');
      } else {
        toast.error(error.message);
      }
    } else {
      toast.error('Síťová chyba — zkontrolujte připojení');
    }
  }
}
```

---

## 6. Toast/Notification Patterns

```typescript
// DON'T — generic error messages
toast.error('Error');
toast.error('Something went wrong');

// DO — specific, actionable messages
toast.error('Nepodařilo se uložit profil — zkuste to znovu');
toast.error('Soubor je příliš velký (max 5 MB)');

// DON'T — showing raw error messages to users
toast.error(error.message); // might show "relation 'users' does not exist"

// DO — user-friendly message, log technical details
console.error('Profile save failed:', error);
toast.error('Nepodařilo se uložit profil');
```

### Toast conventions

| Scenario | Type | Example |
|----------|------|---------|
| Success action | `toast.success` | `'Profil uložen'` |
| Validation error | `toast.error` | `'Vyplňte všechna povinná pole'` |
| Server error | `toast.error` | `'Nepodařilo se načíst data'` |
| Network error | `toast.error` | `'Zkontrolujte připojení k internetu'` |
| Warning | `toast.warning` | `'Neuložené změny budou ztraceny'` |
| Info | `toast.info` | `'Nová verze je k dispozici'` |

---

## 7. Logging Strategy

```typescript
// DON'T — console.log in production
console.log('user data:', userData);

// DO — structured error logging
console.error('[AuthService] Sign-in failed:', {
  email: email, // OK to log (not secret)
  errorCode: error.code,
  errorMessage: error.message,
  // NEVER log: password, tokens, API keys
});

// Log levels
console.error('[Module] ...');  // Errors that need attention
console.warn('[Module] ...');   // Degraded state, fallbacks used
console.info('[Module] ...');   // Important state changes (dev only)
// console.log/debug — remove before commit
```

---

## 8. Graceful Degradation

```tsx
// DON'T — crash the whole page on non-critical failure
function Dashboard() {
  const { data, error } = useFetchStats();
  if (error) throw error; // crashes ErrorBoundary for the whole page

  return <StatsGrid data={data} />;
}

// DO — degrade gracefully for non-critical features
function Dashboard() {
  const { data: stats, error: statsError } = useFetchStats();
  const { data: notifications, error: notifError } = useFetchNotifications();

  return (
    <div>
      {/* Critical — show error state */}
      {statsError ? (
        <div className="glass-card p-4 text-muted-foreground">
          Statistiky se nepodařilo načíst
          <Button variant="ghost" size="sm" onClick={refetchStats}>
            Zkusit znovu
          </Button>
        </div>
      ) : (
        <StatsGrid data={stats} />
      )}

      {/* Non-critical — silently hide */}
      {!notifError && notifications && (
        <NotificationList items={notifications} />
      )}
    </div>
  );
}
```

### Loading and empty states

```tsx
// Always handle all states
function UserList() {
  const { data, error, isLoading } = useUsers();

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorCard message="Nepodařilo se načíst uživatele" />;
  if (!data?.length) return <EmptyState message="Žádní uživatelé" />;

  return <ul>{data.map(user => <UserCard key={user.id} user={user} />)}</ul>;
}
```

---

## Checklist

- [ ] Every `await` is in a try/catch (or uses Result pattern)
- [ ] Every Supabase query checks `error` before using `data`
- [ ] Error Boundaries wrap risky component subtrees
- [ ] Form validation uses Zod + zodResolver
- [ ] User-facing errors are localized and actionable
- [ ] Technical details logged to console, not shown to users
- [ ] Loading, error, and empty states handled for every data fetch
- [ ] Non-critical features degrade gracefully without crashing
