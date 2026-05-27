import os
import json

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
    <PackageReference Include="Microsoft.EntityFrameworkCore.Sqlite" Version="8.0.4" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

</Project>"""
        with open(os.path.join(self.output_dir, "GeneratedProject.csproj"), "w") as f:
            f.write(csproj_content)

        # 2. Write Program.cs
        program_cs_content = """using Microsoft.EntityFrameworkCore;
using GeneratedProject.Data;

var builder = WebApplication.CreateBuilder(args);

// Add services to the DI container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure EF Core with SQLite
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")));

// Auto-register all generated Services and Repositories
var assembly = System.Reflection.Assembly.GetExecutingAssembly();
foreach (var type in assembly.GetTypes().Where(t => t.IsClass && !t.IsAbstract))
{
    if (type.Name.EndsWith("Service") || type.Name.EndsWith("Repository") || type.Name.EndsWith("UnitOfWork"))
    {
        var mainInterface = type.GetInterfaces().FirstOrDefault(i => i.Name == "I" + type.Name);
        if (mainInterface != null)
        {
            builder.Services.AddScoped(mainInterface, type);
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
        with open(os.path.join(self.output_dir, "Program.cs"), "w") as f:
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
    "DefaultConnection": "Data Source=app.db"
  }
}"""
        with open(os.path.join(self.output_dir, "appsettings.json"), "w") as f:
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
            with open(os.path.join(data_dir, "AppDbContext.cs"), "w") as f:
                f.write(app_db_context_content)

    def write_generated_code(self, migration_result: dict):
        self.prepare_directories()
        self.write_boilerplate()

        # Save the analysis result in the root of the generated project for reference
        with open(os.path.join(self.output_dir, 'analysis.json'), 'w') as f:
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
            
            with open(out_path, 'w') as f:
                f.write(code)
            print(f"Saved generated C# file: {os.path.join(folder, filename)}")
