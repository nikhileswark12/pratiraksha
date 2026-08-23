# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: hospital_crud.spec.js >> Hospital manager can view their hospital details and update capacity
- Location: e2e\hospital_crud.spec.js:3:1

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
- textbox: manager@example.com
- text: Password
- textbox: Password123!
- button "Sign In"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('Hospital manager can view their hospital details and update capacity', async ({ page }) => {
  4  |   // Login as manager
  5  |   await page.goto('/');
  6  |   await page.fill('input[type="email"]', 'manager@example.com');
  7  |   await page.fill('input[type="password"]', 'Password123!');
  8  |   await page.click('button[type="submit"]');
  9  | 
  10 |   // Should navigate to dashboard
> 11 |   await expect(page).toHaveURL(/.*\/dashboard/);
     |                      ^ Error: expect(page).toHaveURL(expected) failed
  12 | 
  13 |   // Wait for the hospital card to load
  14 |   const hospitalCard = page.locator('.hospital-card').first();
  15 |   await expect(hospitalCard).toBeVisible({ timeout: 10000 });
  16 |   
  17 |   // Click into detail view
  18 |   await hospitalCard.click();
  19 |   
  20 |   // Expect URL to change to hospital detail
  21 |   await expect(page).toHaveURL(/.*\/hospitals\/[0-9a-fA-F-]+/);
  22 |   
  23 |   // Ensure we can see the edit capacity button
  24 |   const editButton = page.locator('text=Update Capacity');
  25 |   await expect(editButton).toBeVisible();
  26 | });
  27 | 
```