---
name: typescript-patterns
description: TypeScript 5.9 best practices for React + Supabase projects. Covers strict mode, utility types, type guards, generics, discriminated unions, Zod inference, and more.
version: "1.0.0"
effort: medium
author: Brixyy
---

# TypeScript Patterns

TypeScript 5.9 best practices for React + Supabase codebase. Strict mode is always on.

---

## 1. Never `any` — Always `unknown` + Type Guard

```typescript
// DON'T
function processData(data: any) {
  return data.name.toUpperCase();
}

// DO
function processData(data: unknown): string {
  if (isUser(data)) {
    return data.name.toUpperCase();
  }
  throw new Error('Invalid data');
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'name' in value &&
    typeof (value as User).name === 'string'
  );
}
```

**Exception:** Third-party library types that genuinely require `any` — add `// eslint-disable-next-line @typescript-eslint/no-explicit-any` with a comment explaining why.

---

## 2. Interface vs Type

**Use `interface`** for object shapes that may be extended:

```typescript
// DO - extendable object shapes
interface UserProfile {
  id: string;
  email: string;
  name: string;
}

interface AdminProfile extends UserProfile {
  role: 'admin';
  permissions: string[];
}
```

**Use `type`** for unions, intersections, mapped types, and utility compositions:

```typescript
// DO - unions and computed types
type Status = 'idle' | 'loading' | 'success' | 'error';
type UserWithPosts = User & { posts: Post[] };
type FormFields = Pick<UserProfile, 'email' | 'name'>;
```

**Rule of thumb:** If it describes a "thing" (noun), use `interface`. If it describes a "shape transformation" or "union of possibilities", use `type`.

---

## 3. Utility Types

```typescript
// Pick — select specific fields
type LoginForm = Pick<UserProfile, 'email'> & { password: string };

// Omit — exclude fields
type CreateUserDTO = Omit<UserProfile, 'id'>;

// Partial — all fields optional (useful for updates)
type UpdateUserDTO = Partial<Omit<UserProfile, 'id'>>;

// Required — all fields required
type CompleteProfile = Required<UserProfile>;

// Record — typed key-value maps
type StatusColors = Record<Status, string>;
const colors: StatusColors = {
  idle: 'gray',
  loading: 'blue',
  success: 'green',
  error: 'red',
};

// Readonly — immutable data
type FrozenConfig = Readonly<AppConfig>;
```

---

## 4. Discriminated Unions for State

```typescript
// DON'T — boolean flags create impossible states
interface FetchState {
  isLoading: boolean;
  isError: boolean;
  data: User[] | null;
  error: string | null;
}

// DO — discriminated union
type FetchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: User[] }
  | { status: 'error'; error: string };

// Usage with exhaustive narrowing
function renderState(state: FetchState) {
  switch (state.status) {
    case 'idle':
      return <Placeholder />;
    case 'loading':
      return <Spinner />;
    case 'success':
      return <UserList users={state.data} />;
    case 'error':
      return <ErrorMessage message={state.error} />;
    default:
      // Compile-time exhaustiveness check
      const _exhaustive: never = state;
      return _exhaustive;
  }
}
```

---

## 5. `satisfies` Operator

Use `satisfies` to validate a value matches a type while preserving the narrower inferred type:

```typescript
// DON'T — loses specific keys
const routes: Record<string, string> = {
  home: '/',
  dashboard: '/dashboard',
  settings: '/settings',
};
// routes.typo is allowed — no autocomplete

// DO — validates AND preserves literal types
const routes = {
  home: '/',
  dashboard: '/dashboard',
  settings: '/settings',
} satisfies Record<string, string>;
// routes.typo is a compile error — full autocomplete

// Great for config objects
const theme = {
  colors: {
    primary: '#10b981',
    secondary: '#6366f1',
  },
  spacing: {
    sm: 4,
    md: 8,
    lg: 16,
  },
} satisfies Record<string, Record<string, string | number>>;
```

---

## 6. Generics for React Components

```typescript
// Generic list component
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

function List<T>({ items, renderItem, keyExtractor, emptyMessage }: ListProps<T>) {
  if (items.length === 0) {
    return <p className="text-muted-foreground">{emptyMessage ?? 'No items'}</p>;
  }

  return (
    <ul>
      {items.map((item) => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}

// Usage — T is inferred as User
<List
  items={users}
  renderItem={(user) => <span>{user.name}</span>}
  keyExtractor={(user) => user.id}
/>
```

### Generic hooks

```typescript
function useLocalStorage<T>(key: string, initialValue: T) {
  const [stored, setStored] = useState<T>(() => {
    const item = localStorage.getItem(key);
    return item ? (JSON.parse(item) as T) : initialValue;
  });

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    setStored((prev) => {
      const next = value instanceof Function ? value(prev) : value;
      localStorage.setItem(key, JSON.stringify(next));
      return next;
    });
  }, [key]);

  return [stored, setValue] as const;
}
```

---

## 7. Zod Schema Inference

```typescript
import { z } from 'zod';

// Define schema once — derive TypeScript type from it
const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(2).max(100),
  role: z.enum(['user', 'admin', 'moderator']),
  createdAt: z.string().datetime(),
});

// Infer the type — single source of truth
type User = z.infer<typeof userSchema>;

// Partial schema for updates
const updateUserSchema = userSchema.partial().omit({ id: true, createdAt: true });
type UpdateUserDTO = z.infer<typeof updateUserSchema>;

// Use in API handlers
async function createUser(input: unknown): Promise<User> {
  const validated = userSchema.parse(input); // throws ZodError if invalid
  return await db.users.create(validated);
}

// Use with React Hook Form
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const formSchema = userSchema.pick({ email: true, name: true });
type FormValues = z.infer<typeof formSchema>;

function UserForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });
  // ...
}
```

---

## 8. Type Guards and Narrowing

```typescript
// Custom type guard
function isNonNull<T>(value: T | null | undefined): value is T {
  return value != null;
}

// Usage — filter nulls with type safety
const results: (User | null)[] = await Promise.all(fetches);
const users: User[] = results.filter(isNonNull);

// Discriminated union guard
function isSuccess<T>(
  result: { status: 'success'; data: T } | { status: 'error'; error: string }
): result is { status: 'success'; data: T } {
  return result.status === 'success';
}

// `in` operator narrowing
function handleEvent(event: MouseEvent | KeyboardEvent) {
  if ('key' in event) {
    // TypeScript knows this is KeyboardEvent
    console.log(event.key);
  } else {
    // TypeScript knows this is MouseEvent
    console.log(event.clientX);
  }
}
```

---

## 9. Supabase Type Patterns

```typescript
import type { Database } from '@/types/supabase';

// Table row types from generated schema
type User = Database['public']['Tables']['users']['Row'];
type InsertUser = Database['public']['Tables']['users']['Insert'];
type UpdateUser = Database['public']['Tables']['users']['Update'];

// Typed Supabase client
import { createClient } from '@supabase/supabase-js';
const supabase = createClient<Database>(url, key);

// Query result is fully typed
const { data, error } = await supabase
  .from('users')
  .select('id, email, name')
  .eq('role', 'admin');
// data is Pick<User, 'id' | 'email' | 'name'>[] | null
```

---

## 10. Const Assertions and Enums

```typescript
// DON'T — TypeScript enums have quirks
enum Direction {
  Up = 'UP',
  Down = 'DOWN',
}

// DO — const object + type derivation
const DIRECTION = {
  Up: 'UP',
  Down: 'DOWN',
} as const;

type Direction = (typeof DIRECTION)[keyof typeof DIRECTION]; // 'UP' | 'DOWN'

// DO — simple string union for most cases
type Status = 'active' | 'inactive' | 'pending';
```

---

## Checklist

- [ ] `strict: true` in tsconfig.json
- [ ] No `any` — use `unknown` with type guards
- [ ] State uses discriminated unions, not boolean flags
- [ ] Zod schemas as single source of truth for validation + types
- [ ] Supabase types generated from database schema
- [ ] `satisfies` for config objects
- [ ] `as const` instead of enums
- [ ] Generic components where items vary by type
