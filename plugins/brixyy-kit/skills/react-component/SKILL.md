---
name: react-component
description: React 19 component patterns — creation template, composition, performance, shadcn/ui integration, state management. Use when creating, refactoring, or reviewing React components.
version: "1.0.0"
author: Brixyy
---

# React Component Patterns

Comprehensive guide for React 19 + TypeScript + Tailwind + shadcn/ui components.

---

## 1. New Component Template

```tsx
import { type FC } from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface UserCardProps {
  user: User;
  variant?: 'default' | 'compact';
  onSelect?: (userId: string) => void;
  className?: string;
}

export const UserCard: FC<UserCardProps> = ({
  user,
  variant = 'default',
  onSelect,
  className,
}) => {
  return (
    <div
      className={cn(
        'glass-card p-4 transition-all duration-200',
        variant === 'compact' && 'p-2',
        className,
      )}
    >
      <h3 className="text-foreground font-medium">{user.name}</h3>
      <p className="text-muted-foreground text-sm">{user.email}</p>
      {onSelect && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSelect(user.id)}
        >
          Vybrat
        </Button>
      )}
    </div>
  );
};
```

### Rules

- Always define a `Props` interface (never inline)
- Always accept `className` prop for composability
- Use `cn()` for conditional class merging
- Extract to subcomponents at >150 lines
- Business logic belongs in custom hooks, not components

---

## 2. Folder Structure

```
src/
  components/
    ui/              # shadcn/ui primitives — DO NOT MODIFY
    features/        # domain-specific components
      dashboard/
        DashboardHeader.tsx
        DashboardStats.tsx
        index.ts     # re-exports
      users/
        UserCard.tsx
        UserList.tsx
    common/          # shared non-primitive components
      GlassCard.tsx
      PageHeader.tsx
  hooks/             # custom hooks
    useUsers.ts
    useDebounce.ts
  lib/               # utilities
    utils.ts
    formatters.ts
```

---

## 3. React 19 Patterns

### ref as a prop (no more forwardRef)

```tsx
// DON'T — React 19 no longer needs forwardRef
const Input = forwardRef<HTMLInputElement, InputProps>((props, ref) => (
  <input ref={ref} {...props} />
));

// DO — ref is just a prop in React 19
const Input: FC<InputProps & { ref?: React.Ref<HTMLInputElement> }> = ({
  ref,
  ...props
}) => <input ref={ref} {...props} />;
```

### use() hook for context

```tsx
// DON'T
const theme = useContext(ThemeContext);

// DO — React 19
const theme = use(ThemeContext);
```

### Actions and useActionState

```tsx
import { useActionState } from 'react';

function SubmitForm() {
  const [state, action, isPending] = useActionState(
    async (_prev: FormState, formData: FormData) => {
      const result = await submitToAPI(formData);
      return result;
    },
    { error: null },
  );

  return (
    <form action={action}>
      <input name="email" type="email" />
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Odesílání...' : 'Odeslat'}
      </Button>
      {state.error && <p className="text-destructive">{state.error}</p>}
    </form>
  );
}
```

---

## 4. Composition Patterns

### Compound Components

```tsx
// DON'T — boolean prop proliferation
<Card
  showHeader
  showFooter
  headerTitle="Dashboard"
  footerActions={[...]}
  variant="elevated"
  collapsible
/>

// DO — compound components
<Card>
  <Card.Header>
    <Card.Title>Dashboard</Card.Title>
  </Card.Header>
  <Card.Body>
    <DashboardContent />
  </Card.Body>
  <Card.Footer>
    <Button>Uložit</Button>
  </Card.Footer>
</Card>
```

### Implementation with Context

```tsx
import { createContext, use, type FC, type ReactNode } from 'react';

interface CardContextValue {
  variant: 'default' | 'elevated';
}

const CardContext = createContext<CardContextValue>({ variant: 'default' });

interface CardProps {
  variant?: 'default' | 'elevated';
  children: ReactNode;
  className?: string;
}

const Card: FC<CardProps> & {
  Header: FC<{ children: ReactNode; className?: string }>;
  Body: FC<{ children: ReactNode; className?: string }>;
  Footer: FC<{ children: ReactNode; className?: string }>;
} = ({ variant = 'default', children, className }) => (
  <CardContext value={{ variant }}>
    <div className={cn('glass-card', variant === 'elevated' && 'elevated-card', className)}>
      {children}
    </div>
  </CardContext>
);

Card.Header = ({ children, className }) => (
  <div className={cn('border-b border-border/50 p-4', className)}>{children}</div>
);
Card.Body = ({ children, className }) => (
  <div className={cn('p-4', className)}>{children}</div>
);
Card.Footer = ({ children, className }) => (
  <div className={cn('border-t border-border/50 p-4 flex justify-end gap-2', className)}>
    {children}
  </div>
);
```

### Explicit Variants over Boolean Props

```tsx
// DON'T
<Button primary large disabled loading />

// DO
<Button variant="primary" size="lg" disabled>
  {isPending ? <Spinner /> : 'Odeslat'}
</Button>
```

### Children over Render Props

```tsx
// DON'T
<Modal renderHeader={() => <h2>Title</h2>} renderBody={() => <Form />} />

// DO
<Modal>
  <Modal.Header>
    <h2>Title</h2>
  </Modal.Header>
  <Modal.Body>
    <Form />
  </Modal.Body>
</Modal>
```

---

## 5. State Management

### When to use what

| Scenario | Tool |
|----------|------|
| Local UI state (toggle, input) | `useState` |
| Complex state with transitions | `useReducer` |
| Shared state across subtree | Context + Provider |
| Server state (fetched data) | Custom hook + SWR pattern |
| Form state | React Hook Form + Zod |
| Global app state | Zustand (if needed) |

### Context + Provider Pattern

```tsx
// Decouple state implementation from consumers
interface AuthContextValue {
  user: User | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = use(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  // Implementation details stay here — consumers just use the interface
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const signIn = useCallback(async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    setUser(data.user);
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
  }, []);

  return (
    <AuthContext value={{ user, signIn, signOut, isLoading }}>
      {children}
    </AuthContext>
  );
};
```

---

## 6. Performance

### When to memoize — and when NOT to

```tsx
// DON'T — memo for trivial components
const Label = memo(({ text }: { text: string }) => (
  <span>{text}</span>
));

// DO — memo for expensive renders or stable identity
const ExpensiveChart = memo(({ data }: { data: DataPoint[] }) => {
  // Heavy SVG rendering
  return <svg>...</svg>;
});

// DON'T — useMemo for simple expressions
const fullName = useMemo(() => `${first} ${last}`, [first, last]);

// DO — just compute it
const fullName = `${first} ${last}`;

// DO — useMemo for genuinely expensive computation
const sortedData = useMemo(
  () => data.toSorted((a, b) => a.score - b.score),
  [data],
);

// DO — useCallback for callbacks passed to memoized children
const handleSelect = useCallback((id: string) => {
  setSelectedId(id);
}, []);
```

### Key performance rules

1. **Memoize** when: passing callbacks to `memo`'d children, expensive computations, referential identity matters
2. **Don't memoize** when: simple string/number operations, component is cheap to render, only used once
3. **Use functional setState** for stable callbacks:

```tsx
// DON'T — depends on items, causes re-renders
const addItem = useCallback((item: Item) => {
  setItems([...items, item]);
}, [items]);

// DO — no dependency needed
const addItem = useCallback((item: Item) => {
  setItems((prev) => [...prev, item]);
}, []);
```

---

## 7. Error Boundaries

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  fallback?: ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="glass-card p-6 text-center">
          <p className="text-destructive font-medium">Něco se pokazilo</p>
          <Button
            variant="outline"
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

// Usage
<ErrorBoundary fallback={<p>Chyba při načítání</p>}>
  <Dashboard />
</ErrorBoundary>
```

---

## 8. shadcn/ui Integration

```tsx
// DO — use shadcn primitives, never re-implement
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

// DON'T — modify files in components/ui/ directly
// If you need a variant, extend via className or create a wrapper

// DO — wrapper for project-specific variant
export const GlassButton: FC<ComponentProps<typeof Button>> = ({
  className,
  ...props
}) => (
  <Button
    className={cn('glass-card hover:bg-primary/10', className)}
    {...props}
  />
);
```

---

## Checklist

- [ ] Props interface defined (with `className` prop)
- [ ] `cn()` used for conditional classes
- [ ] Component < 150 lines (extract subcomponents)
- [ ] Business logic in hooks, not JSX
- [ ] No boolean prop proliferation — use variants/composition
- [ ] Performance: only memoize what matters
- [ ] Error boundary wrapping critical sections
- [ ] shadcn/ui primitives used (not custom reimplementations)
