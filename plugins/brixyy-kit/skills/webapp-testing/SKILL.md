---
name: webapp-testing
description: "Comprehensive web application testing strategy covering the testing pyramid — unit tests (Vitest), component tests (Testing Library), integration tests, and E2E tests. Includes mocking strategy, code coverage, and CI integration."
version: "1.0.0"
author: Brixyy
---

# Web Application Testing

Kompletní testovací strategie pro webové aplikace. Od unit testů po E2E, s důrazem na praktické vzory pro React + Vite stack.

---

## Testing Pyramid

```
        /  E2E  \           ← Málo, pomalé, drahé (Playwright)
       /----------\
      / Integration \       ← Střední počet (API testy, DB testy)
     /----------------\
    /   Component       \   ← Více (Testing Library + Vitest)
   /----------------------\
  /      Unit Tests        \  ← Nejvíce, rychlé, levné (Vitest)
 /--------------------------\
```

| Vrstva | Nástroj | Počet testů | Rychlost | Co testuje |
|--------|---------|-------------|----------|------------|
| Unit | Vitest | 60-70% | < 1s | Funkce, utils, hooks, store |
| Component | Vitest + Testing Library | 20-25% | 1-3s | Renderování, interakce |
| Integration | Vitest + MSW | 5-10% | 2-5s | API flow, multi-component |
| E2E | Playwright | 5-10% | 10-30s | Kritické user flows |

### Do / Don't pro pyramidu

```
DO:  Většinu logiky testuj unit testy — rychlé a levné
DO:  Component testy pro interakce a renderování
DO:  E2E pouze pro kritické happy paths (login, checkout, onboarding)
DO:  Integration testy pro API vrstvu a datové toky

DON'T:  E2E pro validaci formuláře — to je unit/component test
DON'T:  Unit test pro CSS layout — to je visual regression
DON'T:  Testuj implementační detaily (interní state, private metody)
DON'T:  100% pokrytí za každou cenu — testuj chování, ne řádky
```

---

## Vitest pro Unit Testy

### Konfigurace

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.test.{ts,tsx}',
        'src/**/index.ts',        // Re-exporty
        'src/types/**',
        'src/main.tsx',
      ],
      thresholds: {
        statements: 80,
        branches: 75,
        functions: 80,
        lines: 80,
      },
    },
  },
});
```

### Setup soubor

```typescript
// tests/setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

### Příklad: testování utility funkce

```typescript
// src/utils/format.ts
export function formatPrice(cents: number, currency = 'CZK'): string {
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency,
  }).format(cents / 100);
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
```

```typescript
// src/utils/format.test.ts
import { describe, it, expect } from 'vitest';
import { formatPrice, slugify } from './format';

describe('formatPrice', () => {
  it('formátuje cenu v CZK', () => {
    expect(formatPrice(29900)).toBe('299,00 CZK');
  });

  it('formátuje nulovou cenu', () => {
    expect(formatPrice(0)).toBe('0,00 CZK');
  });

  it('podporuje jinou měnu', () => {
    expect(formatPrice(1000, 'EUR')).toContain('EUR');
  });
});

describe('slugify', () => {
  it('převede český text na slug', () => {
    expect(slugify('Příliš žluťoučký kůň')).toBe('prilis-zlutoucky-kun');
  });

  it('odstraní speciální znaky', () => {
    expect(slugify('Hello World!')).toBe('hello-world');
  });

  it('neponechá trailing pomlčky', () => {
    expect(slugify('--test--')).toBe('test');
  });
});
```

Custom hooky testuj pomocí `renderHook` z `@testing-library/react` a `vi.useFakeTimers()` pro timeouty.

### Do / Don't pro Vitest

```
DO:  Testuj pure funkce — jasný input/output
DO:  Používej vi.useFakeTimers() pro timeouty a intervaly
DO:  Testuj edge cases (null, undefined, prázdný string, velká čísla)
DO:  Skupinuj testy describe bloky podle funkcionality
DO:  Pojmenuj testy popisně: "vrací error když email je prázdný"

DON'T:  Netestuj React komponenty unit testy — použij Testing Library
DON'T:  Nepoužívej snapshot testy pro logiku
DON'T:  Nemockuj vše — preferuj reálné implementace kde je to praktické
DON'T:  Nepíše víc než 1 assert per test (kromě souvisejících hodnot)
```

---

## Component Testing s Testing Library

### Základní vzor

```typescript
// src/components/SearchInput.tsx
interface SearchInputProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export function SearchInput({ onSearch, placeholder = 'Hledat...' }: SearchInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} role="search">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        aria-label="Vyhledávání"
      />
      <button type="submit" disabled={!query.trim()}>
        Hledat
      </button>
    </form>
  );
}
```

```typescript
// src/components/SearchInput.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchInput } from './SearchInput';

describe('SearchInput', () => {
  it('renderuje input s placeholderem', () => {
    render(<SearchInput onSearch={vi.fn()} />);
    expect(screen.getByPlaceholderText('Hledat...')).toBeInTheDocument();
  });

  it('tlačítko je disabled když input je prázdný', () => {
    render(<SearchInput onSearch={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Hledat' })).toBeDisabled();
  });

  it('zavolá onSearch s trimovaným textem', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(<SearchInput onSearch={onSearch} />);

    await user.type(screen.getByRole('textbox'), '  React  ');
    await user.click(screen.getByRole('button', { name: 'Hledat' }));

    expect(onSearch).toHaveBeenCalledWith('React');
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it('nevolá onSearch s prázdným textem', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(<SearchInput onSearch={onSearch} />);

    await user.type(screen.getByRole('textbox'), '   ');
    // Tlačítko je disabled, klik nic neudělá
    expect(onSearch).not.toHaveBeenCalled();
  });
});
```

### Selektory Testing Library (priorita)

```typescript
// 1. getByRole — nejlepší, testuje přístupnost
screen.getByRole('button', { name: 'Odeslat' });
screen.getByRole('heading', { level: 2 });
screen.getByRole('textbox', { name: 'Email' });
screen.getByRole('checkbox', { name: 'Souhlasím' });

// 2. getByLabelText — formuláře
screen.getByLabelText('Heslo');

// 3. getByPlaceholderText — vstupy bez labelu
screen.getByPlaceholderText('Hledat...');

// 4. getByText — statický obsah
screen.getByText('Registrace dokončena');
screen.getByText(/Celkem: \d+ Kč/);

// 5. getByTestId — poslední možnost
screen.getByTestId('complex-widget');
```

### Do / Don't pro Testing Library

```
DO:  Testuj z pohledu uživatele — co vidí a co dělá
DO:  Používej userEvent místo fireEvent (realističtější)
DO:  Preferuj getByRole — zároveň ověřuješ přístupnost
DO:  findBy* pro asynchronní elementy, queryBy* pro neexistenci

DON'T:  Netestuj implementační detaily (state, props, lifecycle)
DON'T:  Nepoužívej container.querySelector — preferuj screen queries
DON'T:  Snapshot testy pro komponenty — křehké a neinformativní
DON'T:  Netestuj CSS styly v component testech — to je visual regression
```

---

## Kdy Mockovat a Kdy Ne

### Mockuj

| Co | Proč | Jak |
|----|------|-----|
| API volání | Rychlost, determinismus | MSW nebo vi.mock |
| Časovače | Determinismus | vi.useFakeTimers() |
| Random/Date | Reprodukovatelnost | vi.spyOn(Math, 'random') |
| External services | Nestabilní, drahé | vi.mock('@/lib/analytics') |
| Browser APIs | Nedostupné v jsdom | vi.stubGlobal() |

### Nemockuj

| Co | Proč |
|----|------|
| Utility funkce | Rychlé, deterministické, testuj reálné chování |
| React komponenty (children) | Testuj integraci, ne izolaci |
| Zustand/Jotai store | Testuj s reálným stavem |
| CSS/Tailwind | Nemá side effects |
| Pure kalkulace | Žádný důvod mockovat |

### Příklad: MSW pro API mocking

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Jan Novák', email: 'jan@test.com' },
      { id: 2, name: 'Eva Svobodová', email: 'eva@test.com' },
    ]);
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),

  http.get('/api/users/:id', ({ params }) => {
    if (params.id === '999') {
      return HttpResponse.json({ error: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json({ id: params.id, name: 'Test User' });
  }),
];
```

```typescript
// tests/setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```typescript
// Přepsání handleru v konkrétním testu
it('zobrazí error při selhání API', async () => {
  server.use(
    http.get('/api/users', () => {
      return HttpResponse.json(null, { status: 500 });
    })
  );

  render(<UserList />);
  await screen.findByText('Nepodařilo se načíst uživatele');
});
```

### Do / Don't pro mocking

```
DO:  MSW pro API mocking — funguje na úrovni sítě, ne importů
DO:  vi.useFakeTimers() pro testy s timeouty
DO:  server.use() pro override v konkrétním testu
DO:  onUnhandledRequest: 'error' — chytí zapomenuté handlery

DON'T:  vi.mock celý modul když stačí mockovat API
DON'T:  Mockuj React internals (useState, useEffect)
DON'T:  Mockuj funkce které testuješ — testuj reálné chování
DON'T:  Nech mock v globálním stavu — vždy resetuj v afterEach
```

---

## Code Coverage Strategy

Coverage je nastavena v `vitest.config.ts` (viz sekce Vitest konfigurace vyse). Spusteni:

```bash
npx vitest run --coverage           # Jednorázově
npx vitest --coverage               # Watch mode
npx vitest run --coverage src/utils  # Konkrétní složka
```

### Co pokrývat

| Priorita | Co | Cílové pokrytí |
|----------|-----|----------------|
| Vysoká | Utils, helpers, pure funkce | 95%+ |
| Vysoká | Custom hooks | 90%+ |
| Střední | Komponenty s logikou | 80%+ |
| Střední | API/service vrstvy | 80%+ |
| Nízká | Presentační komponenty | 60%+ |
| Žádná | Typy, konfigurace, re-exporty | Exclude |

### Do / Don't pro coverage

```
DO:  Nastav realistické thresholds (80% je dobrý start)
DO:  Excluduj soubory které nemá smysl testovat (typy, config)
DO:  Sleduj branch coverage — odhalí neotestované edge cases
DO:  Integruj coverage do CI — failne build pod prahem

DON'T:  Nehon se za 100% — diminishing returns nad 90%
DON'T:  Nepíšej testy jen pro coverage (test chování, ne řádky)
DON'T:  Neignoruj pokles coverage v PR review
DON'T:  Nepoužívej /* v8 ignore */ jako standard — pouze výjimečně
```

---

## E2E vs Component test

Pro E2E testy viz dedikovaný skill `playwright`. Pravidlo: E2E pro multi-page flows, component testy pro izolované interakce.

| Scénář | Typ testu |
|--------|-----------|
| Přihlášení end-to-end | E2E |
| Validace formuláře | Component |
| Navigace mezi stránkami | E2E |
| Platební flow | E2E |
| Dropdown/tooltip | Component |

---

## Struktura testů v projektu

```
src/
  components/
    SearchInput.tsx
    SearchInput.test.tsx      ← Component test vedle komponenty
  hooks/
    useDebounce.ts
    useDebounce.test.ts       ← Hook test vedle hooku
  utils/
    format.ts
    format.test.ts            ← Unit test vedle utility
  services/
    api.ts
    api.test.ts               ← Integration test
tests/
  setup.ts                    ← Globální setup (cleanup, MSW)
  mocks/
    handlers.ts               ← MSW handlery
  specs/                      ← E2E testy (Playwright)
    login.spec.ts
    checkout.spec.ts
  pages/                      ← Page Objects (Playwright)
    login.page.ts
```

### Do / Don't pro strukturu

```
DO:  Test soubory vedle zdrojového kódu (co-location)
DO:  E2E testy v samostatné složce tests/specs/
DO:  Sdílené mocky v tests/mocks/
DO:  Konzistentní pojmenování: .test.ts (unit/component), .spec.ts (E2E)

DON'T:  Neseparuj testy do úplně jiné složky než zdrojový kód
DON'T:  Nemíchej .test a .spec konvence — každá má svůj účel
DON'T:  Nevytvářej __tests__ složky — co-location je přehlednější
```
