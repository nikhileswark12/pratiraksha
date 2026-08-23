import { test, expect } from '@playwright/test';

test('Operator can trigger a crisis simulation', async ({ page }) => {
  // Login as operator
  await page.goto('/');
  await page.fill('input[type="email"]', 'operator@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Should navigate to dashboard
  await expect(page).toHaveURL(/.*\/dashboard/);

  // Navigate to Crisis Sim
  await page.click('text=Crisis Simulation');
  await expect(page).toHaveURL(/.*\/crisis/);

  // Run Simulation
  await page.click('text=Run Simulation');
  
  // Verify alert pops up or result renders
  const resultCard = page.locator('.crisis-result-card, .alert, .text-red-600').first();
  await expect(resultCard).toBeVisible({ timeout: 10000 });
});
