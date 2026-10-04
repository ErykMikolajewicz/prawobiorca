import { test, expect } from '@playwright/test'

const REGULATION_NAME = 'Prawo o nauce i szkolnictwie wyższym - fragment'
const PASSWORD = 'StrongPassword12;'

test('user searches regulation and adds result to case', async ({ page }) => {
  const username = `e2e-${Date.now()}`
  const caseName = `Sprawa ${username}`

  await page.goto('/accounts/register')
  await page.locator('#username').fill(username)
  await page.locator('#password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Zarejestruj' }).click()
  await expect(page).toHaveURL('/auth/login')

  await page.locator('#username').fill(username)
  await page.locator('#password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Zaloguj', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Wyloguj się' })).toBeVisible()

  await page.getByPlaceholder('Utwórz nową sprawę...').fill(caseName)
  await page.getByPlaceholder('Utwórz nową sprawę...').press('Enter')
  await expect(page.getByText(caseName)).toBeVisible()

  await page.getByText(REGULATION_NAME).click()
  await expect(page.getByRole('heading', { name: `Przeszukaj regulacje: ${REGULATION_NAME}` })).toBeVisible()

  await page.getByText('-- Wybierz z listy --').click()
  await page.getByRole('option', { name: caseName }).click()

  await page.getByText('Wg trafności').click()
  await page.getByPlaceholder('Wpisz treść...').fill('obowiązki studenta')
  await page.getByRole('button', { name: 'Przeszukaj' }).click()
  await page.getByRole('button', { name: 'Dodaj do sprawy' }).first().click()
  await expect(page.getByText('Dodano do sprawy.')).toBeVisible()

  await page.getByRole('button', { name: 'Powrót do głównego ekranu' }).click()
  await page.getByText(caseName).click()
  await page.locator('.pinned-document').first().click()
  await expect(page.getByText('Student jest obowiązany').first()).toBeVisible()
})
