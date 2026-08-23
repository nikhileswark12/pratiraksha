# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: crisis.spec.js >> Operator can trigger a crisis simulation
- Location: e2e\crisis.spec.js:3:1

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
  3  | test('Operator can trigger a crisis simulation', async ({ page }) => {
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
  13 |   // Navigate to Crisis Sim
  14 |   await page.click('text=Crisis Simulation');
  15 |   await expect(page).toHaveURL(/.*\/crisis/);
  16 | 
  17 |   // Run Simulation
  18 |   await page.click('text=Run Simulation');
  19 |   
  20 |   // Verify alert pops up or result renders
  21 |   const resultCard = page.locator('.crisis-result-card, .alert, .text-red-600').first();
  22 |   await expect(resultCard).toBeVisible({ timeout: 10000 });
  23 | });
  24 | 
```