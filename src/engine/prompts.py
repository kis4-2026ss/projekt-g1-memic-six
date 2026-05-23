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
You are an expert C# ASP.NET Core 8 developer and software architect.
Your task is to migrate the extracted business intent from legacy PHP code into a highly robust, modern, and production-ready ASP.NET Core Web API architecture.
The target architecture strictly adheres to the Controller-Service-Repository Pattern, Dependency Injection, and Entity Framework Core 8.

{database_schema_context}

Here is the extracted business logic:
{business_logic_json}

Please generate the equivalent C# code. Return ONLY a valid JSON object containing the following keys (if applicable):
- "models_code": All required Domain Entities and Data Transfer Objects (DTOs). Use data annotations (e.g., [Required], [Key]). Place in the `GeneratedProject.Models` namespace.
- "context_code": The `AppDbContext` class inheriting from `DbContext`, containing `DbSet<T>` for all entities. Place in the `GeneratedProject.Data` namespace. Include `using GeneratedProject.Models;`.
- "repository_code": The Repository interfaces (e.g., `IUserRepository`) and their concrete implementations. Inject `AppDbContext` via constructor. Place in `GeneratedProject.Repositories`. Include `using GeneratedProject.Data;` and `using GeneratedProject.Models;`.
- "service_code": The Service interfaces and implementations containing the core business logic. Inject repositories here. Do not access the `AppDbContext` directly from services. Place in `GeneratedProject.Services`. Include `using GeneratedProject.Repositories;` and `using GeneratedProject.Models;`.
- "controller_code": ASP.NET Core API Controllers inheriting from `ControllerBase`. Use `[ApiController]` and route attributes. Return `ActionResult<T>`. Inject services. Place in `GeneratedProject.Controllers`. Include `using GeneratedProject.Services;` and `using GeneratedProject.Models;`.

STRICT GUIDELINES FOR QUALITY AND COMPILATION:
1. **Namespaces & Usings**: Include ALL necessary `using` directives at the top of every file (e.g., `using System;`, `using System.Collections.Generic;`, `using System.Linq;`, `using System.Threading.Tasks;`, `using Microsoft.AspNetCore.Mvc;`, `using Microsoft.EntityFrameworkCore;`).
2. **EF Core Transactions**: If you use transactions (e.g., `BeginTransactionAsync()`), you MUST include `using Microsoft.EntityFrameworkCore.Storage;` to avoid CS0246 errors on `IDbContextTransaction`.
3. **Nullable Reference Types**: C# 8 Nullable reference types are ENABLED. If a method like `FirstOrDefaultAsync` or `FindAsync` can return null, the return type MUST be nullable (e.g., `Task<User?>`). Handle nulls appropriately to avoid CS8603 (Possible null reference return) warnings.
4. **Asynchronous Programming**: Use `async`/`await` for all I/O, database, and network operations. Append `Async` to method names (e.g., `GetUserByIdAsync`).
5. **Separation of Concerns**: Controllers only handle HTTP requests and responses. Services handle business rules. Repositories handle Entity Framework Core data access. 
6. **Database Schema Mapping**: Map Entity models and DbContext DbSets precisely to the tables, columns, constraints, and relationships specified in the target database SQL schema (if provided).
7. **No Context in Repositories File**: Do not declare the `AppDbContext` inside the `repository_code` string. It must only reside in `context_code`.
8. **Syntactic Validity**: Ensure all generated C# code is syntactically valid and compiles cleanly.
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
    "query_params": {{"key": "value"}},
    "headers": {{"Content-Type": "application/json"}},
    "body": {{"key": "value"}} 
  }}
]

Important:
- Set 'path' to the relative endpoint route based on the PHP file provided (e.g., if the file is 'api_get_products.php', the path should be '/api_get_products.php'). The C# runner will map this to the equivalent API route internally if needed.
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

class CSharpMigrationResult(BaseModel):
    models_code: str = Field(description="All required Domain Entities and Data Transfer Objects (DTOs). Use data annotations. Place in the GeneratedProject.Models namespace.")
    context_code: str = Field(description="The AppDbContext class inheriting from DbContext. Place in the GeneratedProject.Data namespace.")
    repository_code: str = Field(description="The Repository interfaces and concrete implementations. Place in GeneratedProject.Repositories.")
    service_code: str = Field(description="The Service interfaces and implementations. Place in GeneratedProject.Services.")
    controller_code: str = Field(description="ASP.NET Core API Controllers. Place in GeneratedProject.Controllers.")

class ValidationTestCase(BaseModel):
    name: str = Field(description="Description of the test case.")
    method: str = Field(description="HTTP Method (GET or POST).")
    path: str = Field(description="Relative endpoint route (e.g. /api_get_products.php).")
    query_params_string: str = Field(default="", description="Query string format (e.g. id=1&format=json). Use empty string if none.")
    headers_json: str = Field(default="{}", description="JSON string of headers, e.g. {\"Content-Type\": \"application/json\"}.")
    body_json: str = Field(default="{}", description="JSON string of HTTP request body payload. Use '{}' if none.")

class ValidationTestSuite(BaseModel):
    test_cases: List[ValidationTestCase] = Field(description="The generated HTTP test cases.")

class ValidationComparisonResult(BaseModel):
    match: bool = Field(description="true if outputs are functionally equivalent, false otherwise.")
    reason: str = Field(description="Explanation of why they match or do not match.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")

