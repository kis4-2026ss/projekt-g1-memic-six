class MigrationPrompts:
    """
    Prompts for the Core Migration Engine to convert PHP to C#.
    """

    PHP_ANALYSIS_PROMPT = """
You are an expert software engineer tasked with analyzing legacy PHP code.
Your goal is to extract the "Business Intent" and core logic of the provided PHP code, completely separate from the PHP-specific syntax or patterns.

Analyze the following PHP code (which may consist of multiple files) and provide a structured JSON response containing:
1. "description": A high-level description of what the combined code does and how the files relate.
2. "inputs": A list of inputs the code takes (e.g., query parameters, form data, database results).
3. "outputs": A list of outputs the code produces (e.g., HTML rendering, JSON response, database updates).
4. "business_rules": A list of specific business rules or logic steps applied across the files.
5. "database_interactions": A summary of any SQL queries or database interactions.

PHP Code:
```php
{php_code}
```
"""

    CSHARP_GENERATION_PROMPT = """
You are an expert C# ASP.NET Core developer.
Your task is to generate modern, clean, and well-structured C# code based on the extracted business intent of legacy PHP code.
The target architecture uses the Controller-Service-Repository Pattern.

{database_schema_context}

Here is the extracted business logic:
{business_logic_json}

Please generate the equivalent C# code. Return the code in a JSON structure containing the following keys (if applicable):
- "controller_code": The ASP.NET Core Controller class.
- "service_code": The Service class containing the business logic.
- "repository_code": The Repository interface and class for data access (using Entity Framework Core patterns, injecting the generated DbContext named AppDbContext).
- "context_code": The ASP.NET Core AppDbContext class inheriting from DbContext, mapping all required DbSets.
- "models_code": Any required DTOs or Entity models.

Ensure the code follows these guidelines:
- Use Dependency Injection (inject AppDbContext into your repositories).
- Use async/await patterns for I/O operations.
- Avoid raw SQL; assume Entity Framework Core will be used.
- Map Entity models and DbContext DbSets precisely to the tables, columns, constraints, and relationships specified in the target database SQL schema (if provided).
- Ensure the code is syntactically valid C#.
- Do not define any DbContext classes inside the repository_code file; assume it is defined in context_code and imported from the Data namespace.
"""

