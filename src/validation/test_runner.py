import requests
import time
from urllib.parse import urljoin

class TestRunner:
    def __init__(self, php_base_url: str, csharp_base_url: str):
        self.php_base_url = php_base_url
        self.csharp_base_url = csharp_base_url
        
    def _map_php_path_to_csharp(self, php_path: str) -> str:
        # e.g., /api_get_products.php -> /api/products
        # Simple heuristic mapping for now, can be improved
        base_name = php_path.strip('/').replace('.php', '')
        if base_name.startswith('api_'):
            # e.g., api_get_products -> /api/products
            parts = base_name.split('_')
            if len(parts) > 2 and parts[1] in ['get', 'post', 'put', 'delete']:
                return f"/api/{parts[2]}"
            elif len(parts) > 1:
                return f"/api/{parts[1]}"
        return f"/api/{base_name}"

    def run_tests(self, test_cases: list) -> list:
        results = []
        for index, test in enumerate(test_cases):
            print(f"Running Test [{index+1}/{len(test_cases)}]: {test.get('name', 'Unnamed Test')}")
            
            php_path = test.get('path', '/')
            csharp_path = self._map_php_path_to_csharp(php_path)
            
            php_url = urljoin(self.php_base_url, php_path)
            csharp_url = urljoin(self.csharp_base_url, csharp_path)
            
            import urllib.parse
            import json
            method = test.get('method', 'GET').upper()
            
            # Parse query params string or fallback to dict
            qp_str = test.get('query_params_string', '')
            if not qp_str and 'query_params' in test:
                params = test.get('query_params', {})
            else:
                params = dict(urllib.parse.parse_qsl(qp_str)) if qp_str else {}
                
            # Parse headers JSON or fallback to dict
            h_str = test.get('headers_json', '{}')
            if not h_str and 'headers' in test:
                headers = test.get('headers', {})
            else:
                try:
                    headers = json.loads(h_str) if h_str else {}
                except Exception:
                    headers = {}
                    
            # Parse body JSON or fallback to dict
            b_str = test.get('body_json', '{}')
            if not b_str and 'body' in test:
                body = test.get('body', None)
            else:
                try:
                    body = json.loads(b_str) if b_str else None
                except Exception:
                    body = None
            
            # 1. Request PHP
            php_response_text = ""
            php_status = 500
            try:
                php_res = requests.request(method, php_url, params=params, json=body, headers=headers, timeout=5)
                php_response_text = php_res.text
                php_status = php_res.status_code
            except Exception as e:
                php_response_text = f"Error: {str(e)}"
                
            # 2. Request C#
            csharp_response_text = ""
            csharp_status = 500
            try:
                csharp_res = requests.request(method, csharp_url, params=params, json=body, headers=headers, timeout=5)
                csharp_response_text = csharp_res.text
                csharp_status = csharp_res.status_code
            except Exception as e:
                csharp_response_text = f"Error: {str(e)}"
                
            results.append({
                "test_case": test,
                "php_result": {
                    "url": php_url,
                    "status": php_status,
                    "body": php_response_text
                },
                "csharp_result": {
                    "url": csharp_url,
                    "status": csharp_status,
                    "body": csharp_response_text
                }
            })
            
            # small delay between requests
            time.sleep(0.5)
            
        return results
