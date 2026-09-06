import { test, expect } from '@playwright/test';

test('should show login screen and prevent invalid login', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('text=Pratiraksha Login')).toBeVisible();
  
  await page.fill('input[type="email"]', 'invalid@example.com');
  await page.fill('input[type="password"]', 'WrongPass!');
  await page.click('button[type="submit"]');

  // Verify specific error message shows instead of just red text
  const errorMessage = page.locator('.text-red-600, .error-message').first();
  await expect(errorMessage).toBeVisible({ timeout: 5000 });
  await expect(errorMessage).toContainText(/invalid|wrong|incorrect/i);
});
