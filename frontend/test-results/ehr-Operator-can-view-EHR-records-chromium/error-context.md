# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ehr.spec.js >> Operator can view EHR records
- Location: e2e\ehr.spec.js:3:1

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /.*\/dashboard/
Received string:  "http://localhost:5173/"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    13 × locator resolved to <html lang="en">…</html>
       - unexpected value "http://localhost:5173/"

```

```yaml
- heading "Pratiraksha Login" [level=1]
- text: Connection error - Backend unreachable Email
- textbox: operator@example.com
- text: Password
- textbox: Password123!
- button "Sign In"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('Operator can view EHR records', async ({ page }) => {
  4  |   // Login as operator
  5  |   await page.goto('/');
  6  |   await page.fill('input[type="email"]', 'operator@example.com');
  7  |   await page.fill('input[type="password"]', 'Password123!');
  8  |   await page.click('button[type="submit"]');
  9  | 
  10 |   // Should navigate to dashboard
> 11 |   await expect(page).toHaveURL(/.*\/dashboard/);
     |                      ^ Error: expect(page).toHaveURL(expected) failed
  12 | 
  13 |   // Navigate to EHR
  14 |   await page.click('text=EHR Integration');
  15 |   await expect(page).toHaveURL(/.*\/ehr/);
  16 | 
  17 |   // Wait for patient records to load
  18 |   const patientRow = page.locator('tbody tr').first();
  19 |   await expect(patientRow).toBeVisible({ timeout: 10000 });
  20 |   
  21 |   // Verify patient data exists
  22 |   await expect(patientRow).toContainText('MRN');
  23 | });
  24 | 
```