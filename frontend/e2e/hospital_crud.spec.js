import { test, expect } from '@playwright/test';

test('Hospital manager can view their hospital details and update capacity', async ({ page }) => {
  // Login as manager
  await page.goto('/');
  await page.fill('input[type="email"]', 'manager@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Should navigate to dashboard
  await expect(page).toHaveURL(/.*\/dashboard/);

  // Wait for the hospital card to load
  const hospitalCard = page.locator('.hospital-card').first();
  await expect(hospitalCard).toBeVisible({ timeout: 10000 });
  
  // Click into detail view
  await hospitalCard.click();
  
  // Expect URL to change to hospital detail
  await expect(page).toHaveURL(/.*\/hospitals\/[0-9a-fA-F-]+/);
  
  // Ensure we can see the edit capacity button
  const editButton = page.locator('text=Update Capacity');
  await expect(editButton).toBeVisible();
});
