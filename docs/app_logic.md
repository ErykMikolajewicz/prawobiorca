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
- **My Cases**:
    - List of created cases.
    - Ability to create a new case.
    - Clicking on a case redirects to the **Case View**.
---

### 3.2. Document Search View

This view opens after selecting a specific document (both public and private).

**Common Functions (Guest and Logged):**
- **Semantic Search**: Search bar supporting natural language (e.g., *"Regulations regarding student rights"*).
- **Search Scope**: Only the **current, open document** is searched.
- **Search Results**: List of most matching articles/text fragments obtained through vector search. A result is always a whole editorial unit (an article, or a `§` in university regulations) together with its breadcrumb, for example *"Rozdział 4 Samorząd studencki i organizacje studenckie > Art. 110"*. Long units are chunked for retrieval only — the chunks are never shown, and the unit's score combines its two best-matching chunks.

**Additional Functions (Only Logged):**
- **Case Management Panel**:
    - **"Add/Select Case" Option**: The user can select one of their cases as "current" or create a new one on the fly.
    - **Change Case**: If the user changes the current case, the view of "pinned" articles in the text updates, showing only those pinned to the newly selected case (within this document).
- **Pinning Articles**:
    - Next to each search result, there is a "Pin to case" button.
    - Pinning adds the article to the context of the currently selected case.
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
    - Text field (Input/Textarea) where the user describes their situation or the purpose of the letter (e.g., *"I request financial aid due to the difficult situation I found myself in after the death of a parent..."*).

3. **DOCX Generator**:
    - "Generate Application" button.
    - **Logic of operation**: The system (LLM) retrieves:
        - The application description, entered by the user.
        - The content of all pinned articles.
    - Based on this, it generates a formal document (application/letter) in **DOCX** format.
