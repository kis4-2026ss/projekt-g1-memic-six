import os
import json
import re

def fix_using_clauses(code: str) -> str:
    # Match using namespace directive: using System; using Microsoft.EntityFrameworkCore; etc.
    # Exclude using (var ...) or using var ... = ...;
    using_pattern = re.compile(r'^\s*using\s+(static\s+)?[A-Za-z0-9_\.]+(\s*=\s*[A-Za-z0-9_\.]+)?\s*;$')
    
    lines = code.splitlines()
    usings = []
    other_lines = []
    
    for line in lines:
        if using_pattern.match(line):
            usings.append(line)
        else:
            other_lines.append(line)
            
    if usings:
        # Deduplicate while preserving order of first appearance
        unique_usings = []
        seen = set()
        for u in usings:
            normalized = " ".join(u.strip().split())
            if normalized not in seen:
                seen.add(normalized)
                unique_usings.append(u.strip())
        
        # Combine unique usings at the top, then the rest
        return "\n".join(unique_usings) + "\n\n" + "\n".join(other_lines)
    return code

class CSharpProjectGenerator:
    def __init__(self, output_dir="./output/GeneratedProject"):
        self.output_dir = output_dir

    def prepare_directories(self):
        dirs = ["Controllers", "Services", "Repositories", "Models", "Data"]
        for d in dirs:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)

    def write_boilerplate(self):
        # 1. Write csproj
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.4" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="8.0.4">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Pomelo.EntityFrameworkCore.MySql" Version="8.0.2" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

  <ItemGroup>
    <Compile Remove="tests\\**" />
    <Content Remove="tests\\**" />
    <EmbeddedResource Remove="tests\\**" />
    <None Remove="tests\\**" />
  </ItemGroup>

</Project>"""
        with open(os.path.join(self.output_dir, "GeneratedProject.csproj"), "w", encoding="utf-8") as f:
            f.write(csproj_content)

        # 2. Write Program.cs
        program_cs_content = """using Microsoft.EntityFrameworkCore;
using GeneratedProject.Data;

var builder = WebApplication.CreateBuilder(args);

// Add services to the DI container.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseLower;
    });
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure EF Core with MySQL
builder.Services.AddDbContext<AppDbContext>(options =>
{
    var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
    options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString));
});

// Auto-register all generated Services and Repositories
var assembly = System.Reflection.Assembly.GetExecutingAssembly();
foreach (var type in assembly.GetTypes().Where(t => t.IsClass && !t.IsAbstract))
{
    var ns = type.Namespace ?? "";
    if (ns.Contains("Services") || ns.Contains("Repositories") || type.Name.EndsWith("Service") || type.Name.EndsWith("Repository") || type.Name.EndsWith("UnitOfWork") || type.Name.EndsWith("Calculator"))
    {
        var mainInterface = type.GetInterfaces().FirstOrDefault(i => i.Name == "I" + type.Name);
        if (mainInterface != null)
        {
            if (type.IsGenericTypeDefinition)
            {
                builder.Services.AddScoped(mainInterface.GetGenericTypeDefinition(), type);
            }
            else
            {
                builder.Services.AddScoped(mainInterface, type);
            }
        }
        else
        {
            builder.Services.AddScoped(type);
        }
    }
}

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

// Apply migrations / create database automatically on startup
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    try
    {
        var dbContext = services.GetRequiredService<AppDbContext>();
        dbContext.Database.EnsureCreated();
    }
    catch (Exception ex)
    {
        var logger = services.GetRequiredService<ILogger<Program>>();
        logger.LogError(ex, "An error occurred creating the DB.");
    }
}

app.Run();
"""
        with open(os.path.join(self.output_dir, "Program.cs"), "w", encoding="utf-8") as f:
            f.write(program_cs_content)

        # 3. Write appsettings.json
        appsettings_content = """{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Port=3306;Database=crm_enterprise_csharp_test;Uid=root;Pwd=;"
  }
}"""
        with open(os.path.join(self.output_dir, "appsettings.json"), "w", encoding="utf-8") as f:
            f.write(appsettings_content)
            
        # 4. Write empty AppDbContext if one isn't generated (failsafe)
        app_db_context_content = """using Microsoft.EntityFrameworkCore;

namespace GeneratedProject.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

        // Generated DbSets will be placed here
    }
}"""
        data_dir = os.path.join(self.output_dir, "Data")
        os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(os.path.join(data_dir, "AppDbContext.cs")):
            with open(os.path.join(data_dir, "AppDbContext.cs"), "w", encoding="utf-8") as f:
                f.write(app_db_context_content)

    def write_generated_code(self, migration_result: dict):
        self.prepare_directories()
        self.write_boilerplate()

        # Save the analysis result in the root of the generated project for reference
        with open(os.path.join(self.output_dir, 'analysis.json'), 'w', encoding="utf-8") as f:
            json.dump(migration_result.get("analysis", {}), f, indent=2)

        gen = migration_result.get("generation", {})
        if not gen or not isinstance(gen, dict) or "error" in gen:
            print(f"No valid generation dictionary found or error occurred: {gen.get('error', 'Unknown generation error') if isinstance(gen, dict) else 'Invalid type'}")
            return

        for key, code in gen.items():
            if not code or not isinstance(code, str):
                continue
            
            # Map key to appropriate filename and folder
            filename = f"{key.replace('_code', '')}.cs"
            # Preserve original camelCase/PascalCase but ensure first letter is uppercase
            filename = "".join([word[0].upper() + word[1:] for word in filename.split('_') if word])
            
            # Map keys to folders
            folder = ""
            if "controller" in key.lower():
                folder = "Controllers"
            elif "service" in key.lower():
                folder = "Services"
            elif "repository" in key.lower():
                folder = "Repositories"
            elif "model" in key.lower() or "dto" in key.lower() or "entity" in key.lower():
                folder = "Models"
            elif "context" in key.lower() or "data" in key.lower():
                folder = "Data"
                # Override default AppDbContext
                filename = "AppDbContext.cs"

            out_path = os.path.join(self.output_dir, folder, filename) if folder else os.path.join(self.output_dir, filename)
            
            # Post-process code to clean up any illegal trailing semicolons after property accessors (e.g. { get; set; };)
            cleaned_code = re.sub(r'(get\s*;\s*set\s*;?\s*})\s*;', r'\1', code)
            
            # Post-process: Make GenericRepository._context public so services can access it for transactions
            cleaned_code = re.sub(r'protected\s+readonly\s+AppDbContext\s+_context', r'public readonly AppDbContext _context', cleaned_code)
            cleaned_code = re.sub(r'protected\s+AppDbContext\s+_context', r'public AppDbContext _context', cleaned_code)
            
            # Post-process: Replace invalid Forbid(object) with StatusCode(403, object)
            cleaned_code = re.sub(r'return\s+Forbid\s*\(', r'return StatusCode(StatusCodes.Status403Forbidden, ', cleaned_code)
            
            # Post-process: Replace invalid List<string> initialized with StringComparer to HashSet<string>
            cleaned_code = re.sub(r'List<string>(\s+[A-Z0-9_a-z]+)\s*=\s*new(?:\s+List<string>)?\s*\(\s*StringComparer\.OrdinalIgnoreCase\s*\)', r'HashSet<string>\1 = new HashSet<string>(StringComparer.OrdinalIgnoreCase)', cleaned_code)
            
            # Post-process code to sort all using clauses to the very top to prevent CS1529 namespace errors
            cleaned_code = fix_using_clauses(cleaned_code)
            
            with open(out_path, 'w', encoding="utf-8") as f:
                f.write(cleaned_code)
            print(f"Saved generated C# file: {os.path.join(folder, filename)}")
