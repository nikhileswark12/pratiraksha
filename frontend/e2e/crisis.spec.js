import { test, expect } from '@playwright/test';

test('Operator can trigger a crisis simulation', async ({ page }) => {
  // Login as operator
  await page.goto('/');
  await page.fill('input[type="email"]', 'operator@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Wait for login to complete
  await expect(page.locator('text=Live Hospital Status')).toBeVisible({ timeout: 10000 });

  // Navigate to Crisis Sim
  await page.goto('/crisis');
  await expect(page).toHaveURL(/.*\/crisis/);

  // Run Simulation
  await page.click('text=Run Simulation');
  
  // Verify alert pops up or result renders
  const resultCard = page.locator('.crisis-result-card, .alert, .text-red-600').first();
  await expect(resultCard).toBeVisible({ timeout: 10000 });
});
