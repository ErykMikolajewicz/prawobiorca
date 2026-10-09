# Description of "Prawobiorca" Application Logic

## 1. Introduction
**Prawobiorca** is an application designed for intelligent searching of legal acts. The system uses Vector Search to enable users to find relevant regulations using natural language queries.
For logged-in users, the application offers a "Cases" management function, which allows aggregating regulations from various sources and generating ready-made legal applications in DOCX format.
---

## 2. User Roles

### 2.1. Guest (Unlogged User)
- Has access only to public, predefined documents.
- Can search documents.
- Does not have the ability to save data.

### 2.2. Logged User
- Has all Guest permissions.
- Can add their own documents.
- Can create and manage "Cases."
- Can generate DOCX applications based on gathered materials.

### 2.3. Administrator
- Has all Logged User permissions.
- Can add, edit and delete public documents.
- Manages application templates used to generate DOCX applications.
---

## 3. Views and Functionalities

### 3.1. Main Screen

This is the starting point of the application.

**For Guest:**
- **List of Public Documents**: The user sees a list of predefined legal acts (read-only).
- There is no possibility to add or remove documents from this list.
- Clicking on a document redirects to the **Search View**.

**For Logged User:**
- Sees the same as the Guest plus additional sections:
- **My Documents**:
    - Ability to upload own files (legal acts, regulations).
    - List of files added by themselves.
    - **Automatic indexing**: Once an upload is confirmed, the indexing process (creating embeddings) is queued automatically. No manual action is required.
    - **Preparation status**: Each file shows its state (`NOT_STARTED`, `IN_PROGRESS`, `PREPARED`, `FAILED`). Only `PREPARED` files can be searched.
    - **Retry option**: A file that ends up `FAILED` (after the automatic attempts are exhausted) can be retried by the user.

**Sidebar (Logged User):**
- **My Cases**:
    - List of created cases.
    - Ability to create a new case.
    - Ability to set a case as "active" (pin icon). The active case is used in the **Search View**.
    - Ability to delete a case (with confirmation). Deleting the currently opened case redirects to the Main Screen.
    - Clicking on a case redirects to the **Case View**.
- **Application Templates** menu item, visible only for the Administrator, redirects to the **Application Templates View**.
---

### 3.2. Document Search View

This view opens after selecting a specific document (both public and private).

**Common Functions (Guest and Logged):**
- **Semantic Search**: Search bar supporting natural language (e.g., *"Regulations regarding student rights"*).
- **Search Scope**: Only the **current, open document** is searched.
- **Search Results**: List of most matching articles/text fragments obtained through vector search. A result is always a whole editorial unit (an article, or a `§` in university regulations) together with its breadcrumb, for example *"Rozdział 4 Samorząd studencki i organizacje studenckie > Art. 110"*. Long units are chunked for retrieval only — the chunks are never shown, and the unit's score combines its two best-matching chunks.

**Additional Functions (Only Logged):**
- **Pinning Articles**:
    - Next to each search result, there is an "Add to case" button.
    - Pinning adds the article to the context of the active case, selected in the sidebar. Without an active case, the user is asked to select one.
    - Articles from different documents can be pinned to a single case.
---

### 3.3. Case View

View available exclusively for **Logged Users**, serving to finalize work on a legal issue.

**Functionalities:**
1. **List of Pinned Articles**:
    - Displays all fragments the user pinned to this case in the Search View.
    - Each item contains the content of the article and information about the source document (e.g., *"Art. 5, Civil Code"*), built from the structural metadata stored with every section.
    - Ability to unpin (remove) an article from the case.

2. **Context / Application Description**:
    - Selection of the application type, from the templates published by the Administrator.
    - Fields defined by the selected template (text, number, select list or date), prefilled with their default values. Required fields must be filled.
    - Text field (Input/Textarea) where the user describes their situation or the purpose of the letter (e.g., *"I request financial aid due to the difficult situation I found myself in after the death of a parent..."*).

3. **DOCX Generator**:
    - "Generate Application" button.
    - **Logic of operation**: The system (LLM) retrieves:
        - The AI instructions of the selected template.
        - The template field values marked to be passed to AI.
        - The application description, entered by the user.
        - The content of all pinned articles.
    - Based on this, it generates the content of a formal document (application/letter), inserted into the template's **DOCX** file.
    - Generation runs in the background: the user does not wait for the response, the new application appears in the list with the "Generating" status.

4. **List of Generated Applications**:
    - Displays all applications generated for this case, with their name, creation date and generation status ("Generating", "Generation failed"). The name is given by the LLM after generation; until then, the template name is shown.
    - The list refreshes automatically while any application is being generated.
    - Ability to download a generated application (DOCX) and to delete an application.
    - Deleting the case deletes its applications as well.
---

### 3.4. Application Templates View

View available exclusively for the **Administrator**, serving to manage templates of applications generated in the Case View.

**Functionalities:**
1. **List of Templates**:
    - Displays all templates with their status: "Not uploaded", "Draft" or "Published".
    - Ability to delete a template (with confirmation). Applications already generated from it are kept.
    - Clicking on a template redirects to the **Template Editor**.

2. **Adding a Template**:
    - The Administrator uploads a DOCX file and gives the template a name (by default the file name).
    - The DOCX file is a Jinja2 template. It must contain the `paragraphs` variable, where the generated content is inserted. The `current_date` variable is filled automatically.
    - Every other template variable becomes a template field. The new template gets the "Draft" status and default AI instructions.

3. **Template Editor**:
    - Editing the template name.
    - Editing the AI instructions in a Markdown editor.
    - Configuration of each field: label, type (text, number, select list, date), optional validation regex (text only), list options (select list only), optional default value, "Required" and "Pass to AI" flags.
    - Download of the DOCX file and its preview.
    - Only a draft can be edited. A published template must be unpublished first.

4. **Publishing**:
    - A draft with non-empty AI instructions can be published. Only published templates are available to users in the Case View.
    - Unpublishing returns the template to the "Draft" status.
