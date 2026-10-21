---
name: import-hygiene
description: Rules for clean imports - duplicate prevention, correct ordering, and path aliases. Use when adding imports to files.
version: "1.0.0"
effort: low
author: Brixyy
---

# Import Hygiene

## Common Mistake: Duplicate Imports

```tsx
// DON'T - causes build error
import { useSearchParams } from 'react-router-dom';
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';  // DUPLICATE!

// DO
import { useSearchParams } from 'react-router-dom';
import { useState } from 'react';
```

---

## Import Rules

### 1. Check Existing Imports

**ALWAYS before adding an import:**
1. Check the top of the file (first 20-30 lines)
2. Look for whether the import already exists
3. If yes - add to existing, don't add new

```tsx
// DON'T
import { useState } from 'react';
// ... 50 lines of code ...
import { useEffect } from 'react';  // Should be merged!

// DO
import { useState, useEffect } from 'react';
```

### 2. Import Order

```tsx
// 1. React
import { useState, useEffect } from 'react';

// 2. External libraries
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';

// 3. Internal - UI components
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 4. Internal - feature components
import { GlassCard } from '@/components/common/GlassCard';
import { PortfolioSelector } from '@/components/portfolio/PortfolioSelector';

// 5. Hooks
import { usePortfolio } from '@/hooks/usePortfolio';

// 6. Utils/Lib
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/formatters';

// 7. Types
import type { Portfolio } from '@/types/portfolio';

// 8. Icons (always last)
import { Settings, User, LogOut } from 'lucide-react';
```

### 3. Path Aliases

```tsx
// DON'T - relative paths
import { Button } from '../../components/ui/button';
import { useAuth } from '../../../hooks/useAuth';

// DO - @/ alias
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
```

### 4. Merge Imports

```tsx
// DON'T - separate imports from same module
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// OK - shadcn components are in separate files, so this is fine

// DO - merge where possible
import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
```

---

## Workflow for Adding Import

1. **Open file and read imports** (first ~30 lines)
2. **Check if import exists:**
   - If YES -> add to existing
   - If NO -> add at correct position by order
3. **Use @/ alias** (never relative paths)
4. **Verify no duplicates**

---

## Common Sources of Duplicates

1. **Copy-paste from other files** - always verify
2. **AI generation** - AI may add import even if it exists
3. **Merge conflicts** - check imports after resolving conflicts
4. **Incremental additions** - easy to forget during editing

---

## Checklist

For every file edit:

- [ ] Did I read existing imports?
- [ ] Am I not adding a duplicate import?
- [ ] Am I using @/ alias?
- [ ] Are imports correctly ordered?
- [ ] Are imports from same module merged?
