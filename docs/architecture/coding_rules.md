
# Coding Rules
This section contains information aimed at standardizing code writing among developers and enforcing a uniform format.
The rules are very general; if you need specific information (e.g., router naming), refer to the section covering
individual components.

---

## PEP8 and IDE
Generally speaking, you should follow PEP 8 guidelines. For this purpose, using PyCharm, even the community version,
is recommended. Other IDEs do not provide such strong support.

Example:
```
VisualStudioCode ignores the fact that there should be at least 2 blank lines between class declarations.
```

---

## Import Convention
You should divide imports into three types: from the standard library, from public libraries, and from your own project.
If necessary, these three sections can be split into even smaller ones.

Example:

```python
import json

import sqlalchemy.orm as orm

import src.database
# ... further imports from app related to database/sql, then one blank line and more imports from app

from src.services import do_something
```

---

## Variables and Constants
After imports, declare all global variables and constants, e.g., logger initialization, config parameters, etc.
Names of variables that are literals or are initialized once (e.g., by reading values from a file)
should be written in UPPER_SNAKE_CASE.

Example:
```python
API_URL = settings.API_URL
BEARER_TOKEN_LENGTH = 32
```

Module-level variables whose values may change after declaration should be written in snake_case.

Example:
```python
number_of_function_calls = 0
```

When writing code, use descriptive variable names whenever possible, even if they are long.

Example:
```
external_service_manager instead of serv_manager
```

---

## Commenting Guidelines
Adding comments in the code is optional. Ideally, the code should be readable enough to understand without
additional comments. Comments should be left for particularly complex or unusual situations.
Docstrings are also optional. They can be added as part of mkdocs documentation, which can be integrated via a plugin,
and for explaining the operation of functions/classes with many parameters or behavior not easily captured by the name.

Use type hints in function signatures. For variables/class fields, do so when the type is not obvious or required
for other reasons, such as Pydantic validation.

---

## Advanced Python Constructs
Prioritize readability over brevity. Therefore, use advanced Python features such as list comprehensions
or the walrus operator with caution.

### List comprehension
Example of proper list comprehension:
```python
tasks_to_execute = [task for task in tasks if task["status"] == "ready"]
```

Example of improper list comprehension:
```python
tasks = [
    job["task"]
    for job in [job for job in jobs if jobs["status"] == True]
    if isinstance(job, GoodJob)
    or job["priority"] == "high"
    and is_executors_available(executor, job_type="not_good_job")
]
```
In such cases, it's better to split it into for loops.

### Walrus operator
Proper walrus operator usage:
```python
if (task_steps := len(task)) < 5:
    for step in range(task_steps):
        execute_task_step(task, step_number)
else:
    queue_long_task(task)
```

Another good example is in list comprehensions, where it can help avoid calculating a value twice.

Example:
```python
complex_measured_tasks = [(task, execution_time) for task in tasks if (execution_time := measure_complexity(task)) > 3]
```
Instead of:
```python
complex_measured_tasks = [(task, measure_complexity(task)) for task in tasks if measure_complexity(task) > 3]
```

Improper usage of the walrus operator:
```python
if (user_data := await get_current_user(execution_context, settings=settings)) is not None and not user_data.is_admin:
    do_something()
elif user_data.is_admin:
    do_something_other()
else:
    raise Exception("No user data")
```

When more complex conditions are required, do not combine variable declaration with returning it.
For the above code, it's better to write:
```python
user_data = await get_current_user(execution_context, settings=settings)
if user_data is not None:
    if user_data.is_admin:
        do_something_other()
    else:
        do_something()
else:
    raise Exception("No user data")
```

---

## Commit hook
Before every commit:
- Lint and format the code with Ruff
- Check the frontend code with `pnpm check`
- When `core-service/src/` is changed, regenerate the API types with `just api-types`

Tests are not run by the hook, they are run by CI.

---

## Summary
Follow PEP 8 and use PyCharm to help with that. Prefer descriptive and readable code over brevity.
Code should be as self-explanatory as possible, but use comments when necessary and add type hints.
Use advanced Python features like list comprehensions with care.