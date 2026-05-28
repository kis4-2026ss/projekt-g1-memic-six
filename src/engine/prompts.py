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

    CSHARP_COMPONENT_PROMPT = """
You are an expert C# ASP.NET Core 8 developer and software architect.
Your task is to migrate the extracted business intent from legacy PHP code into a highly robust, modern, and production-ready ASP.NET Core Web API architecture.

{database_schema_context}

Here is the extracted business logic:
{business_logic_json}

You are generating ONLY the following component: **{component_name}**
Description of this component: {component_description}

{previous_code_context}

Please generate the equivalent C# code for this specific component ONLY. 
Return your code inside a single ```csharp ... ``` markdown block.
Do NOT use JSON. Do NOT wrap your response in JSON.

STRICT GUIDELINES FOR QUALITY AND COMPILATION:
1. **Namespaces & Usings**: Include ALL necessary `using` directives at the top of every file (e.g., `using System;`, `using System.Data;`, `using System.Collections.Generic;`, `using System.Linq;`, `using System.Threading.Tasks;`, `using Microsoft.AspNetCore.Mvc;`, `using Microsoft.EntityFrameworkCore;`, `using GeneratedProject.Models;`, `using GeneratedProject.Data;`, `using GeneratedProject.Repositories;`, `using GeneratedProject.Services;`).
2. **File-Scoped Namespaces**: Use modern C# 10+ file-scoped namespaces at the top of every file (e.g., `namespace GeneratedProject.Models;` with a semicolon, and NO enclosing curly braces {{ }} around the rest of the file contents). Do NOT use block namespaces with curly braces around classes.
3. **EF Core Transactions**: If you use transactions, you MUST include `using Microsoft.EntityFrameworkCore.Storage;`.
4. **Nullable Reference Types**: C# 8 Nullable reference types are ENABLED. 
5. **Asynchronous Programming**: Use `async`/`await` for all I/O, database, and network operations. Append `Async` to method names.
6. **Avoid Naming Conflicts with System.Threading.Tasks.Task**: If the legacy code or database schema has a table, entity, or model named `tasks` or `task`, you MUST name the C# model class `UserTask` (or `TodoTask`) instead of `Task`. Use `UserTask` across all generated files (DbContext, Repositories, Services, Controllers) to completely avoid naming collisions with C#'s built-in `System.Threading.Tasks.Task`. Never define a C# model class named `Task`.
7. **Syntactic Validity**: Ensure all generated C# code is syntactically valid and compiles cleanly.
   - Every opened class, interface, method, and namespace block MUST be properly closed with a corresponding closing brace (`}}`).
   - Properties in DTOs and models MUST NOT end with a trailing semicolon after the accessor block (e.g. use `public int Id {{ get; set; }}`).
   - Only use standard HTTP status codes available in `Microsoft.AspNetCore.Http.StatusCodes`. Be very careful with typos: The correct code is `Status422UnprocessableEntity`, NOT `Status442UnprocessableEntity`. Do NOT use fake codes like `Status444NoResponse`.
8. **No Sub-Namespaces**: Do NOT invent or use `.Interfaces` sub-namespaces (e.g. do not write `using GeneratedProject.Repositories.Interfaces;`). Place interfaces in the same namespace as their implementations (e.g. `GeneratedProject.Repositories` or `GeneratedProject.Services`).
9. **No Abstract Instantiation**: Do NOT attempt to instantiate abstract classes or interfaces (e.g. `new BaseRepository<T>()`). You must provide and instantiate concrete implementations, or rely on dependency injection.
10. **Consistent Interfaces**: If you use patterns like `IUnitOfWork`, ensure that all properties (e.g., `Projects`, `UserTasks`) accessed in the services are strictly defined in the interface. Alternatively, prefer injecting specific Repositories directly into the Services rather than using a Unit of Work.
11. **Completeness**: You MUST generate code for ALL entities and tables present in the provided database schema (including `departments`, `contracts`, `timesheets`, `products`, `audit_logs`, etc.). Do NOT truncate or skip any tables, models, or DB sets.
12. **MySQL Compatibility**: The system uses MySQL (Pomelo.EntityFrameworkCore.MySql). You are allowed to use MySQL-specific raw SQL (like `SELECT ... FOR UPDATE` for row locks) if necessary, but prefer standard EF Core LINQ methods where possible.
13. **Safety & Nulls**: Always handle potential `null` references safely. When calculating KPIs or analytics, always check for division-by-zero (e.g. `Total > 0 ? (Value / Total) : 0`).
14. **Tuples**: If returning C# Tuples from methods, strictly use the exact property names defined in the tuple declaration to avoid compilation errors.
15. **LINQ Grouping**: When using LINQ `GroupBy`, remember that the result is an `IGrouping<TKey, TElement>`. Do NOT attempt to access properties of `TElement` directly on the grouping object (e.g., `group.Company` is invalid). You must use `group.Key.PropertyName` if the property is part of the key, or aggregate the elements (e.g., `group.First().Company` or `group.Sum(x => x.Value)`).
"""

    VALIDATION_GENERATION_PROMPT = """
You are an expert QA Engineer. Your task is to generate HTTP test cases for an API based on legacy PHP code and its extracted business logic analysis.
These test cases will be executed against both the original PHP API and the new C# ASP.NET Core migration to verify functional equivalence.

PHP Source Code:
```php
{php_code}
```

Extracted Business Logic:
{business_logic_json}

Generate a suite of 3-5 distinct test cases covering various inputs, including valid, invalid, and edge-case inputs.
Return ONLY a valid JSON array of test cases. Each test case MUST have the following structure:
[
  {{
    "name": "Description of the test case",
    "method": "GET or POST",
    "path": "/api_endpoint.php", 
    "csharp_path": "/api/controller_route",
    "query_params": {{"key": "value"}},
    "headers": {{"Content-Type": "application/json"}},
    "body": {{"key": "value"}} 
  }}
]

Important:
- Set 'path' to the relative endpoint route based on the PHP file provided (e.g., if the file is 'api_get_products.php', the path should be '/api_get_products.php').
- Set 'csharp_path' to the corresponding migrated C# REST endpoint path matching the generated C# controllers. Guess the exact route based on standard ASP.NET Core API conventions for these controllers. For this project, typical generated routes often include: '/api/Products/bulk-upsert', '/api/Invoices', '/api/Analytics/contracts', '/api/Analytics/crm-kpis', '/api/Projects/tree', '/api/Timesheets', '/api/Dashboard'. Ensure you use the exact casing and hyphens as a typical modern REST API would.
- If it's a GET request, provide 'query_params'. If POST, provide 'body' (and use application/x-www-form-urlencoded or application/json appropriately).
- Return ONLY the JSON array.
"""

    VALIDATION_COMPARISON_PROMPT = """
You are an expert software validator. Your task is to compare two HTTP responses: one from a legacy PHP application and one from a newly migrated C# API.
The legacy application often returns HTML or unstructured data, while the C# API returns structured JSON.
Determine if the two outputs represent functionally equivalent data and business logic results.

Legacy PHP Output:
```
{php_output}
```

New C# Output:
```
{csharp_output}
```

Evaluate if they contain the same core data. If the PHP output is a table of products, does the C# JSON array contain the same products? 
Return ONLY a valid JSON object with the following structure:
{{
  "match": true/false,
  "reason": "Explanation of why they match or do not match.",
  "confidence": 0.0 to 1.0
}}
"""

# Pydantic Schemas for Gemini Structured Outputs
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class PHPAnalysisInputOutput(BaseModel):
    name: str = Field(description="Name of the input or output.")
    type: str = Field(description="Type of the input or output.")
    description: str = Field(description="Description of the input or output.")

class PHPAnalysisBusinessRule(BaseModel):
    rule: str = Field(description="The specific business rule or check applied.")
    description: str = Field(description="Description of the business rule.")

class PHPAnalysisDbInteraction(BaseModel):
    type: str = Field(description="Type of interaction (e.g. SELECT, INSERT, UPDATE).")
    table: str = Field(description="Target table name.")
    query: str = Field(description="The raw or parameterized SQL query.")
    description: str = Field(description="Description of what this query accomplishes.")

class PHPAnalysisResult(BaseModel):
    description: str = Field(description="A high-level description of what the combined code does.")
    inputs: List[PHPAnalysisInputOutput] = Field(description="A list of inputs the code takes.")
    outputs: List[PHPAnalysisInputOutput] = Field(description="A list of outputs the code produces.")
    business_rules: List[PHPAnalysisBusinessRule] = Field(description="A list of specific business rules or logic steps.")
    database_interactions: List[PHPAnalysisDbInteraction] = Field(description="A summary of SQL queries.")


class ValidationTestCase(BaseModel):
    name: str = Field(description="Description of the test case.")
    method: str = Field(description="HTTP Method (GET or POST).")
    path: str = Field(description="Relative endpoint route (e.g. /api_get_products.php).")
    csharp_path: str = Field(default="", description="The corresponding migrated C# REST endpoint path (e.g. /api/Products or /api/Inventory/adjust) matching the generated C# controllers.")
    query_params_string: str = Field(default="", description="Query string format (e.g. id=1&format=json). Use empty string if none.")
    headers_json: str = Field(default="{}", description="JSON string of headers, e.g. {\"Content-Type\": \"application/json\"}.")
    body_json: str = Field(default="{}", description="JSON string of HTTP request body payload. Use '{}' if none.")

class ValidationTestSuite(BaseModel):
    test_cases: List[ValidationTestCase] = Field(description="The generated HTTP test cases.")

class ValidationComparisonResult(BaseModel):
    match: bool = Field(description="true if outputs are functionally equivalent, false otherwise.")
    reason: str = Field(description="Explanation of why they match or do not match.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")

