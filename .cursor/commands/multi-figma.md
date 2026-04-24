# 🎨 Figma-to-Component Generation Task

I have a **list of Figma design links**, and I want you to **generate React components** based on each design.

---

## 🧩 Workflow

1. **Process each Figma link in sequence:**
   - Read the **first link**, generate its component.
   - Then move to the **next link**, generate the next component.
   - Continue until all Figma links are completed.

---

## 🧱 Development Requirements

- **Styling:**
  - Use **color variables** (`background`, `border`, `text`, etc.) defined in `tailwind.config.js`.
  - Use **font size classes** defined in `tailwind.config.js` (e.g., `text-display-lg`, `text-heading-md`, `text-body-sm`, etc.) for typography styling.
- **UI Components:**
  - If the design includes **common UI patterns**, check the `src/components/ui` directory.
  - **Reuse existing components** from `src/components` wherever possible to maintain consistency.
- **Icons:**
  - Check if icons from the Figma design already exist in the `src/components/icons` folder.
  - If icons exist, import and use them from the icons index file (e.g., `import { GoogleIcon, MailIcon } from "@/components/icons";`).
  - If icons don't exist, download SVGs from Figma and add them to the `src/components/icons` folder, then update the `index.tsx` file to export them.
  - If icons can't be downloaded, create placeholder SVG files with appropriate names and update the component to use them.

---

## 🌐 Internationalization (i18n)

After generating each component:

1. **Extract all text content** from the Figma design.
2. **Create i18n keys** following the existing structure in `src/i18n/locales/`:
   - Use meaningful, nested key names (e.g., `featureName.componentName.textKey`)
   - Follow the existing pattern in the locale files
3. **Update ALL locale files**:
   - `src/i18n/locales/en.json` - Add English translations
   - `src/i18n/locales/zh.json` - Add Chinese translations
   - ...
4. **Use i18n in the component**:

- Import `useTranslation` hook from `src/i18n`
- Replace hardcoded text with `t('your.i18n.key')`
- Ensure all user-facing text is translatable

**Example:**

\`\`\`typescript
// In component
import { useTranslation } from '@/shared/i18n';

const { t } = useTranslation();

<p className="text-heading-md text-neutral-primary">{t('featureName.componentName.title')}</p>
\`\`\`

---

## 🧭 Output

For each Figma link:

- Generate a **separate, reusable React component**.
- Each component must be:
  - **Cleanly structured**
  - **Aligned with the design system** (fonts, colors, spacing)
  - **Fully internationalized** with i18n keys
  - **Responsive** and consistent with the design system
- Update **all locale files** (`en.json`, `zh.json, ...`) with appropriate translations.
- Follow the existing **project folder conventions** (e.g., `components/[category]/[ComponentName].tsx`).

---

## 🎨 Figma Links

Here are the design references:
