import { test, expect } from '@playwright/test';

test('Operator can view EHR records', async ({ page }) => {
  // Login as operator
  await page.goto('/');
  await page.fill('input[type="email"]', 'operator@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Should navigate to dashboard
  await expect(page).toHaveURL(/.*\/dashboard/);

  // Navigate to EHR
  await page.click('text=EHR Integration');
  await expect(page).toHaveURL(/.*\/ehr/);

  // Wait for patient records to load
  const patientRow = page.locator('tbody tr').first();
  await expect(patientRow).toBeVisible({ timeout: 10000 });
  
  // Verify patient data exists
  await expect(patientRow).toContainText('MRN');
});
