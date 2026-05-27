import os
import json
import urllib.parse

class TestCodeGenerator:
    def __init__(self, run_output_dir):
        self.run_output_dir = run_output_dir
        self.tests_dir = os.path.join(self.run_output_dir, "tests")
        self.csharp_tests_dir = os.path.join(self.tests_dir, "csharp")
        self.php_tests_dir = os.path.join(self.tests_dir, "php")

    def prepare_directories(self):
        os.makedirs(self.csharp_tests_dir, exist_ok=True)
        os.makedirs(self.php_tests_dir, exist_ok=True)

    def _safe_method_name(self, name):
        # convert string to valid method name
        safe = "".join(c if c.isalnum() else "_" for c in name)
        while "__" in safe:
            safe = safe.replace("__", "_")
        safe = safe.strip("_")
        # Ensure it starts with letters
        if safe and safe[0].isdigit():
            safe = "Test_" + safe
        return safe

    def _map_php_path_to_csharp(self, php_path: str, test_case: dict = None) -> str:
        # If the test case has a dynamically generated csharp_path from Gemini, use it directly!
        if test_case and test_case.get('csharp_path'):
            return test_case.get('csharp_path')

        # Fallback to the original heuristic mapping
        base_name = php_path.strip('/').replace('.php', '')
        if base_name.startswith('api_'):
            parts = base_name.split('_')
            if len(parts) > 2 and parts[1] in ['get', 'post', 'put', 'delete']:
                return f"/api/{parts[2]}"
            elif len(parts) > 1:
                return f"/api/{parts[1]}"
        return f"/api/{base_name}"

    def generate_native_test_files(self, test_cases):
        if not test_cases:
            print("No test cases to generate native files for.")
            return

        self.prepare_directories()
        
        # 1. Generate C# Integration Test File
        self._generate_csharp_tests(test_cases)
        
        # 2. Generate PHP Integration Test File
        self._generate_php_tests(test_cases)

    def _generate_csharp_tests(self, test_cases):
        csharp_test_file_path = os.path.join(self.csharp_tests_dir, "CSharpIntegrationTests.cs")
        
        methods_code = []
        for index, test in enumerate(test_cases):
            name = test.get('name', f'Test_{index+1}')
            safe_name = self._safe_method_name(name)
            method = test.get('method', 'GET').upper()
            php_path = test.get('path', '/')
            csharp_path = self._map_php_path_to_csharp(php_path, test)
            
            # Query params handling
            qp_str = test.get('query_params_string', '')
            if not qp_str and 'query_params' in test:
                params = test.get('query_params', {})
                if params:
                    qp_str = urllib.parse.urlencode(params)
            
            url_suffix = f"{csharp_path}"
            if qp_str:
                url_suffix += f"?{qp_str}"

            # Headers handling
            h_str = test.get('headers_json', '{}')
            headers = {}
            if h_str and h_str != '{}':
                try:
                    headers = json.loads(h_str)
                except Exception:
                    pass
            elif 'headers' in test:
                headers = test.get('headers', {})

            headers_setup_lines = []
            for h_key, h_val in headers.items():
                if h_key.lower() == 'content-type':
                    continue  # Content type is set on request content, not headers
                headers_setup_lines.append(f'            request.Headers.TryAddWithoutValidation("{h_key}", "{h_val}");')
            
            headers_setup = "\n".join(headers_setup_lines) if headers_setup_lines else "            // No custom headers"

            # Body/Payload handling
            b_str = test.get('body_json', '{}')
            body = None
            if b_str and b_str != '{}':
                try:
                    body = json.loads(b_str)
                except Exception:
                    pass
            elif 'body' in test:
                body = test.get('body', None)

            body_setup = "            // No request body"
            if body and method in ['POST', 'PUT', 'PATCH']:
                escaped_body = json.dumps(body).replace('"', '\\"')
                body_setup = f'            var jsonPayload = "{escaped_body}";\n'
                body_setup += f'            request.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");'

            method_template = f"""        [Fact]
        public async Task {safe_name}()
        {{
            // Arrange - {name}
            var requestUri = "{url_suffix}";
            var request = new HttpRequestMessage(HttpMethod.{method.capitalize()}, requestUri);
            
{headers_setup}

{body_setup}

            // Act
            var response = await _client.SendAsync(request);

            // Assert
            Console.WriteLine($"Test '{name}' status code: {{response.StatusCode}}");
            Assert.True((int)response.StatusCode >= 200 && (int)response.StatusCode < 400, 
                $"API call to '{{requestUri}}' failed with status: {{response.StatusCode}}");
            
            var content = await response.Content.ReadAsStringAsync();
            Assert.NotNull(content);
        }}"""
            methods_code.append(method_template)

        methods_joined = "\n\n".join(methods_code)

        csharp_template = f"""using System;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Xunit;

namespace GeneratedProject.Tests
{{
    public class CSharpIntegrationTests : IDisposable
    {{
        private readonly HttpClient _client;
        private const string BaseUrl = "http://localhost:5000";

        public CSharpIntegrationTests()
        {{
            _client = new HttpClient {{ BaseAddress = new Uri(BaseUrl) }};
            _client.DefaultRequestHeaders.Accept.Clear();
            _client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        }}

        public void Dispose()
        {{
            _client.Dispose();
        }}

{methods_joined}
    }}
}}
"""
        with open(csharp_test_file_path, "w", encoding="utf-8") as f:
            f.write(csharp_template)
        print(f"Generated native C# test file: {csharp_test_file_path}")

    def _generate_php_tests(self, test_cases):
        php_test_file_path = os.path.join(self.php_tests_dir, "PhpIntegrationTests.php")

        methods_code = []
        for index, test in enumerate(test_cases):
            name = test.get('name', f'Test_{index+1}')
            safe_name = self._safe_method_name(name)
            method = test.get('method', 'GET').upper()
            php_path = test.get('path', '/')

            # Query params handling
            qp_str = test.get('query_params_string', '')
            if not qp_str and 'query_params' in test:
                params = test.get('query_params', {})
                if params:
                    qp_str = urllib.parse.urlencode(params)
            
            url_suffix = f"{php_path}"
            if qp_str:
                url_suffix += f"?{qp_str}"

            # Headers handling
            h_str = test.get('headers_json', '{}')
            headers = {}
            if h_str and h_str != '{}':
                try:
                    headers = json.loads(h_str)
                except Exception:
                    pass
            elif 'headers' in test:
                headers = test.get('headers', {})

            headers_lines = []
            for h_key, h_val in headers.items():
                headers_lines.append(f'            "{h_key}: {h_val}"')
            
            headers_array = ",\n".join(headers_lines) if headers_lines else ""

            # Body/Payload handling
            b_str = test.get('body_json', '{}')
            body = None
            if b_str and b_str != '{}':
                try:
                    body = json.loads(b_str)
                except Exception:
                    pass
            elif 'body' in test:
                body = test.get('body', None)

            body_setup = "        // No body for GET request"
            if body and method in ['POST', 'PUT', 'PATCH']:
                escaped_body = json.dumps(body).replace('"', '\\"')
                body_setup = f'        curl_setopt($ch, CURLOPT_POSTFIELDS, "{escaped_body}");'

            method_template = f"""    public function test{safe_name}()
    {{
        // Arrange - {name}
        $url = $this->baseUrl . "{url_suffix}";
        $ch = curl_init($url);
        
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "{method}");
        
        $headers = [
{headers_array}
        ];
        if (!empty($headers)) {{
            curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        }}
        
{body_setup}
        
        // Act
        $response = curl_exec($ch);
        $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        // Assert
        echo "PHP Test '{name}' responded with Status Code: " . $statusCode . "\\n";
        $this->assertLessThan(400, $statusCode, "PHP API call to '$url' failed with status: " . $statusCode);
        $this->assertNotEmpty($response, "PHP API response was empty");
    }}"""
            methods_code.append(method_template)

        methods_joined = "\n\n".join(methods_code)

        php_template = f"""<?php
use PHPUnit\\Framework\\TestCase;

class PhpIntegrationTests extends TestCase
{{
    private $baseUrl = "http://localhost:8000";

{methods_joined}
}}
"""
        with open(php_test_file_path, "w", encoding="utf-8") as f:
            f.write(php_template)
        print(f"Generated native PHP test file: {php_test_file_path}")
