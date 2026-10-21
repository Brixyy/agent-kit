---
name: code-quality
description: Code quality rules and common error prevention. Use ALWAYS when writing or editing components - prevents need for complex audits.
version: "1.0.0"
effort: low
author: Brixyy
---

# Code Quality & Design System Compliance

## Apply when writing/editing code

This skill prevents common mistakes **during code writing**, eliminating the need for complex audits later.

---

## Critical Rules

### 1. Colors - ONLY Design Tokens

```tsx
// DON'T - hardcoded colors
style={{ color: '#10b981' }}
style={{ backgroundColor: '#f97316' }}
className="text-[#ef4444]"
className="bg-[#22c55e]"

// DO - design tokens
className="text-success"      // green
className="text-warning"      // orange
className="text-destructive"  // red
className="text-info"         // blue
className="text-primary"      // forest green
className="text-muted-foreground" // secondary text
```

### 2. Glassmorphism - ALWAYS CSS Class

```tsx
// DON'T - inline glassmorphism
className="bg-card/40 backdrop-blur-xl border border-border/50"
className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10"

// DO - CSS classes
className="glass-card"      // standard card
className="elevated-card"   // for nodes, floating elements
className="feature-card"    // for landing page
```

### 3. Transitions - Standardized Values

```tsx
// DON'T - inconsistent or missing
className="hover:bg-primary/10"  // missing transition!
className="transition-all duration-500"  // too slow
className="transition-all duration-100"  // too fast

// DO
className="transition-colors duration-200 hover:bg-primary/10"
className="transition-all duration-200"   // standard
className="transition-all duration-300"   // for modals, sidebars
```

### 4. Inline Styles - MINIMIZE

```tsx
// DON'T - static values
style={{ marginTop: '16px' }}
style={{ borderRadius: '12px' }}
style={{ padding: '24px' }}

// DO - Tailwind
className="mt-4"
className="rounded-xl"
className="p-6"

// EXCEPTION - only for dynamic values
style={{ width: `${percentage}%` }}
style={{ transform: `translateY(${offset}px)` }}
```

### 5. Imports - Duplicates

```tsx
// DON'T - duplicate imports
import { useState } from 'react';
// ... more code ...
import { useState } from 'react';  // ERROR!

// DO - single import
import { useState, useEffect, useMemo } from 'react';
```

---

## Performance & rendering rules (react-doctor prevence)

Tyhle vzory flaguje `react-doctor` (audit). Piš je **rovnou správně**, ať se audit nemusí dohánět.

### 6. Jeden průchod místo řetězených iterací (`js-combine-iterations`)

```tsx
// DON'T - .filter().map() projde pole dvakrát
const labels = items.filter((i) => i.active).map((i) => i.label);

// DO - jeden for…of / reduce
const labels: string[] = [];
for (const item of items) {
  if (item.active) labels.push(item.label);
}
```

### 7. `toSorted()` místo `[...arr].sort()` (`js-tosorted-immutable`)

```tsx
// DON'T - spread jen kvůli nemutaci = zbytečná alokace
const sorted = [...values].sort((a, b) => a - b);

// DO - immutable bez spreadu
const sorted = values.toSorted((a, b) => a - b);

// Iterátor (Map/Set.values()) musíš materializovat → Array.from, ne [...x].sort()
const rows = Array.from(byKey.values()).sort((a, b) => a.id.localeCompare(b.id));
```

### 8. Set/Map pro opakované lookupy (`js-set-map-lookups`, `js-index-maps`)

```tsx
// DON'T - .includes()/.find()/.indexOf() O(n) uvnitř smyčky
for (const row of rows) {
  if (allowedKeys.includes(row.key)) { /* … */ }       // O(n) každé kolo
  const owner = users.find((u) => u.id === row.userId); // O(n*m)
}

// DO - Set/Map postavený JEDNOU před smyčkou
const allowed = new Set(allowedKeys);
const userById = new Map(users.map((u) => [u.id, u]));
for (const row of rows) {
  if (allowed.has(row.key)) { /* … */ }
  const owner = userById.get(row.userId);
}
```

### 9. Paralelizuj nezávislé `await` (`async-await-in-loop`, `async-parallel`)

```tsx
// DON'T - nezávislé operace sekvenčně
for (const file of files) { results.push(await file.text()); }

// DO - Promise.all
const results = await Promise.all(files.map((f) => f.text()));
```

**ALE NE, když:** iterace závisí na předchozí (běžící součet, budget, brzdné `break`), nebo jde o **Prisma interaktivní transakci** (`prisma.$transaction(async (tx) => …)`) — souběžné dotazy na stejný `tx` Prisma zakazuje, drž je sekvenčně.

### 10. Render: nevolat funkci vracející JSX inline (`no-render-in-render`)

```tsx
// DON'T - funkce vrací ReactNode a voláš ji v JSX → špatná rekonciliace
<td>{renderInlineMarkdown(text, key)}</td>

// DO - extrahuj komponentu
function InlineMarkdown({ text, keyPrefix }: { text: string; keyPrefix: string }) {
  return <>{renderInlineMarkdown(text, keyPrefix)}</>;
}
<td><InlineMarkdown keyPrefix={key} text={text} /></td>
```

### 11. Drž komponenty malé (`no-giant-component`)

Komponenta nad ~250 ř. = rozděl. Vytáhni **prezentační podkomponenty** (`<Header />`, `<List />`, `<Composer />`) a logiku do **custom hooků** (`useVoiceRecorder`). Stav/efekty/handlery nech v rodiči a předávej dolů jako props.

### 12. Stabilní `key`, ne index pole (`no-array-index-as-key`)

```tsx
// DON'T
items.map((item, i) => <Row key={i} … />)
// DO
items.map((item) => <Row key={item.id} … />)
```
Index je přijatelný jen u **staticky parsovaného seznamu, který se nikdy nepřeskupuje** (filtr/řazení/reorder).

### 13. `useState` init, ne mount-only efekt (`no-initialize-state`)

```tsx
// DON'T - počáteční hodnotu nastavuješ efektem
const [v, setV] = useState(0);
useEffect(() => { setV(readStored()); }, []);
// DO - lazy initializer
const [v, setV] = useState(() => readStored());
```
Efekt nech jen tehdy, když init **opravdu potřebuje měření DOM po mountu** (`getBoundingClientRect`) — pak je to legitimní, ne chyba.

### 14. JSX jako prop jen memoizovaně (`jsx-no-jsx-as-prop`)

Předáváš-li čerstvě vytvořený JSX do **`React.memo`** dítěte, memoizuj/extrahuj (`useMemo`), jinak memo nic neušetří. U **nememoizovaného** dítěte je slot-prop (`afterSections={…}`) v pořádku — memoizace by nepomohla.

### 15. Drop nepoužitý `export` (`unused-export`)

Nepoužívaný symbol → zruš `export` (interní použití) nebo smaž deklaraci. **Výjimka:** když je to záměrný feature/spike stub (plánované napojení), radši ho zapoj nebo nahlas — neměň tiše doménovou logiku.

### Když audit nemá pravdu (judgment)

- `prefer-tag-over-role` (`role="listbox"` → `<datalist>`): u **vlastního portálového listboxu/dropdownu** s klávesovou navigací a `aria-activedescendant` je `role="listbox"` **správně** — `<datalist>` (jen autocomplete inputu) ho nenahradí. False positive, nech být.
- Čísla řádků v reportu bývají posunutá proti aktuálnímu kódu — řiď se vzorem, ne řádkem.

---

## Pre-Commit Checklist

When writing code **automatically verify**:

1. **Colors**
   - [ ] No `#xxxxx` hex values
   - [ ] No `rgb()` or `rgba()` values
   - [ ] All colors from design tokens

2. **Glassmorphism**
   - [ ] Cards use `glass-card` class
   - [ ] No `backdrop-blur` inline
   - [ ] No `bg-card/40` pattern inline

3. **Transitions**
   - [ ] Hover states have `transition-*`
   - [ ] Duration is 150/200/300ms
   - [ ] Focus states are defined

4. **Spacing**
   - [ ] Using Tailwind classes (p-4, m-2, gap-6)
   - [ ] No inline margin/padding
   - [ ] `px-N py-N` se stejnou hodnotou → `p-N` (shorthand)

5. **Imports**
   - [ ] No duplicate imports
   - [ ] `@/` path alias (not relative `../../`)

6. **Performance & rendering** (viz pravidla 6–15)
   - [ ] Žádné `.filter().map()` řetězení — jeden průchod
   - [ ] `toSorted()` místo `[...arr].sort()`
   - [ ] Set/Map (postavený před smyčkou) pro opakované `includes`/`find`/`indexOf`
   - [ ] Nezávislé `await` přes `Promise.all` (mimo Prisma `$transaction`)
   - [ ] Žádná funkce vracející JSX volaná inline → komponenta
   - [ ] `key={item.id}`, ne index pole
   - [ ] Žádný nepoužitý `export`

7. **Accessibility**
   - [ ] Každý interaktivní prvek má label (text / `aria-label` / `aria-labelledby`)

---

## Quick Reference

### Colors

| Usage | Class |
|-------|-------|
| Primary | `text-primary`, `bg-primary` |
| Success | `text-success`, `bg-success/10` |
| Warning | `text-warning`, `bg-warning/10` |
| Error | `text-destructive`, `bg-destructive/10` |
| Info | `text-info`, `bg-info/10` |
| Primary text | `text-foreground` |
| Secondary text | `text-muted-foreground` |

### Cards

| Type | Class |
|------|-------|
| Standard card | `glass-card` |
| Elevated (nodes) | `elevated-card` |
| Feature section | `feature-card` |

### Transitions

| Speed | Class | Usage |
|-------|-------|-------|
| Fast | `duration-150` | Hover, focus |
| Normal | `duration-200` | Most cases |
| Slow | `duration-300` | Modals |

### Spacing

| Size | Class |
|------|-------|
| 8px | `p-2`, `m-2`, `gap-2` |
| 12px | `p-3`, `m-3`, `gap-3` |
| 16px | `p-4`, `m-4`, `gap-4` |
| 24px | `p-6`, `m-6`, `gap-6` |
