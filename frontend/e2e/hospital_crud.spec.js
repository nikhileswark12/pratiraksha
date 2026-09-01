import { test, expect } from '@playwright/test';

test('Hospital manager can view their hospital details and update capacity', async ({ page }) => {
  // Login as manager
  await page.goto('/');
  await page.fill('input[type="email"]', 'manager@example.com');
  await page.fill('input[type="password"]', 'Password123!');
  await page.click('button[type="submit"]');

  // Wait for login to complete
  await expect(page.locator('text=Live Hospital Status')).toBeVisible({ timeout: 10000 });

  // Navigate to Hospitals list
  await page.goto('/hospitals');
  await expect(page).toHaveURL(/.*\/hospitals/);

  // Take a screenshot to see what's on the page
  await page.screenshot({ path: 'screenshot.png' });

  // Wait for the hospital row to load
  const hospitalRow = page.locator('tbody tr.cursor-pointer').first();
  await expect(hospitalRow).toBeVisible({ timeout: 10000 });
  
  // Click into detail view
  await hospitalRow.click();
  
  // Wait for hospital detail to load
  await expect(page).toHaveURL(/.*\/hospitals\/.+/);
  
  // Ensure we can see the edit capacity button
  const editButton = page.locator('text=Update Capacity');
  await expect(editButton).toBeVisible();

  // Click the button and fill out the modal
  await editButton.click();
  const modalInput = page.locator('input[type="number"]');
  await expect(modalInput).toBeVisible();

  // Change the value
  const newValue = '123';
  await modalInput.fill(newValue);
  
  // Submit the form
  await page.locator('button[type="submit"]').click();
  
  // Verify the modal closes and the new value is present
  await expect(page.locator('.fixed')).toHaveCount(0); // Modal closed
  
  // Wait for UI to update to show the new value (e.g. 123/ total beds)
  await expect(page.locator('text=' + newValue + '/')).toBeVisible();
});
