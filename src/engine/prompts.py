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
6. **No Context in Repositories File**: Do not declare the `AppDbContext` inside the `repository_code` string. It must only reside in `context_code`.
"""
