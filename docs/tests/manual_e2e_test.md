# Manual E2E Test (Frontend + Backend)

Run this scenario against a local environment initialized with `just init-db` from the repository root.
The API, worker, object storage, extraction, embedding and LLM services must be running.
UI labels and sample input below remain in Polish to match the application.

## 1. Log In

- **Username**: `PrawobiorcaTester`
- **Password**: `PrawobiorcaPassword1;`
- **Action**: Click “Zaloguj”.

## 2. Application Template

- **Skip**: If a published application template already exists. The seeded `PrawobiorcaTester` account is an administrator.
- **Where**: Sidebar, “Szablony wniosków”.
- **Action**: Add a template, select a DOCX file containing the `paragraphs` variable, and click “Dodaj”.
- **Action**: Open the new template, configure its fields, and click “Zapisz i opublikuj”.
- **Expected result**: The template has the “Opublikowany” status.

## 3. Create a Case

- **Where**: “Moje sprawy”.
- **Input**: Enter a name, for example “Odwołanie od skreślenia”.
- **Action**: Create the case.

## 4. Open a Legal Document

- **Where**: “Publiczne regulacje”.
- **Select**: A prepared regulation, for example the seeded `PWr - regulamin studiow.pdf`.
- **Action**: Open the document's search view.

## 5. Select the Active Case

- **Where**: Sidebar, “Moje sprawy” list.
- **Check**: “Odwołanie od skreślenia” (created in step 3) has a filled pin icon, indicating that it is active. Click another case's pin icon to make that case active instead.

## 6. Search

- **Where**: “Twoje zapytanie”.
- **Input**: Enter a question, for example “Ile mam dni na odwołanie się od decyzji o skreśleniu z listy studentów?”.
- **Action**: Click “Przeszukaj”.
- **Select**: The result with the highest “Podobieństwo” value, then click “Dodaj do sprawy”.

## 7. Generate an Application

- **Where**: The case details view, in the application form.
- **Input**: Select a published application template, fill in its fields, and describe the situation, for example “Wnoszę o uchylenie decyzji o skreśleniu z listy studentów z powodu długotrwałej hospitalizacji w trakcie sesji.”.
- **Action**: Click “Generuj Wniosek (DOCX)”.
- **Expected result**: A message confirms that generation has started, and an application appears in the generated applications list with the generation-in-progress status. When generation completes, that status disappears and “Pobierz” becomes available.
- **Action**: Click “Pobierz”.
- **Expected result**: The browser downloads the generated DOCX file.
