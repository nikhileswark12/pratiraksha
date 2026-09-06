import { test, expect } from '@playwright/test';

test('Operator can view EHR records', async ({ page }) => {
  // Login as operator
  await page.goto('/');
  await page.fill('input[type="email"]', 'operator@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Wait for login to complete
  await expect(page.locator('text=Live Hospital Status')).toBeVisible({ timeout: 10000 });

  // Navigate to EHR
  await page.goto('/ehr');
  await expect(page).toHaveURL(/.*\/ehr/);

  // Wait for patient records to load
  const patientRow = page.locator('tbody tr').first();
  await expect(patientRow).toBeVisible({ timeout: 10000 });
  
  // Verify patient data exists with proper format (e.g. MRN0, MRN10)
  await expect(patientRow).toContainText(/MRN\d+/);
});
