#!/usr/bin/env python3
"""
Комплексный тест всех API эндпоинтов SEO Analyzer
Проверяет все функции: авторизацию, CRUD операции, аналитику
"""

import requests
import json
import uuid
from typing import Dict, Any, Optional
import time
from datetime import datetime

class SEOAnalyzerTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.test_user_email = f"test_{int(time.time())}@example.com"
        self.test_password = "testpassword123"
        
        # Для хранения созданных объектов
        self.created_group_id: Optional[str] = None
        self.created_word_id: Optional[str] = None
        self.created_llm_id: Optional[str] = None
        
        # Результаты тестов
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Логирование результатов теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                    params: Dict[str, Any] = None) -> requests.Response:
        """Выполнение HTTP запроса с авторизацией"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            raise
    
    def test_server_health(self):
        """Тест доступности сервера"""
        try:
            response = self.make_request("GET", "/docs")
            success = response.status_code == 200
            self.log_test("Server Health Check", success, 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Server Health Check", False, str(e))
    
    def test_user_registration(self):
        """Тест регистрации пользователя"""
        try:
            data = {
                "email": self.test_user_email,
                "password": self.test_password
            }
            response = self.make_request("POST", "/api/auth/register", data)
            success = response.status_code in [200, 201]
            
            if success:
                user_data = response.json()
                details = f"User created: {user_data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("User Registration", success, details)
        except Exception as e:
            self.log_test("User Registration", False, str(e))
    
    def test_user_login(self):
        """Тест авторизации пользователя"""
        try:
            data = {
                "email": self.test_user_email,
                "password": self.test_password
            }
            response = self.make_request("POST", "/api/auth/login", data)
            success = response.status_code == 200
            
            if success:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                details = f"Token received: {self.access_token[:20]}..."
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("User Login", success, details)
        except Exception as e:
            self.log_test("User Login", False, str(e))
    
    def test_get_current_user(self):
        """Тест получения информации о текущем пользователе"""
        try:
            response = self.make_request("GET", "/api/auth/me")
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                details = f"User: {user_data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Current User", success, details)
        except Exception as e:
            self.log_test("Get Current User", False, str(e))
    
    def test_create_word_group(self):
        """Тест создания группы слов"""
        try:
            data = {
                "name": f"Test Group {int(time.time())}"
            }
            response = self.make_request("POST", "/api/word-groups", data)
            success = response.status_code in [200, 201]
            
            if success:
                group_data = response.json()
                self.created_group_id = group_data.get("uuid")
                details = f"Group created: {group_data.get('name')} (ID: {self.created_group_id})"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Create Word Group", success, details)
        except Exception as e:
            self.log_test("Create Word Group", False, str(e))
    
    def test_get_word_groups(self):
        """Тест получения списка групп слов"""
        try:
            response = self.make_request("GET", "/api/word-groups")
            success = response.status_code == 200
            
            if success:
                groups = response.json()
                details = f"Found {len(groups)} groups"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Word Groups", success, details)
        except Exception as e:
            self.log_test("Get Word Groups", False, str(e))
    
    def test_update_word_group(self):
        """Тест обновления группы слов"""
        if not self.created_group_id:
            self.log_test("Update Word Group", False, "No group ID available")
            return
            
        try:
            data = {
                "name": f"Updated Test Group {int(time.time())}"
            }
            response = self.make_request("PUT", f"/api/word-groups/{self.created_group_id}", data)
            success = response.status_code == 200
            
            if success:
                group_data = response.json()
                details = f"Group updated: {group_data.get('name')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Update Word Group", success, details)
        except Exception as e:
            self.log_test("Update Word Group", False, str(e))
    
    def test_create_word(self):
        """Тест создания слова"""
        try:
            data = {
                "name": f"test keyword {int(time.time())}",
                "group_id": self.created_group_id
            }
            response = self.make_request("POST", "/api/words", data)
            success = response.status_code in [200, 201]
            
            if success:
                word_data = response.json()
                self.created_word_id = word_data.get("uuid")
                details = f"Word created: {word_data.get('name')} (ID: {self.created_word_id})"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Create Word", success, details)
        except Exception as e:
            self.log_test("Create Word", False, str(e))
    
    def test_get_words(self):
        """Тест получения списка слов"""
        try:
            response = self.make_request("GET", "/api/words")
            success = response.status_code == 200
            
            if success:
                words = response.json()
                details = f"Found {len(words)} words"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Words", success, details)
        except Exception as e:
            self.log_test("Get Words", False, str(e))
    
    def test_get_words_by_group(self):
        """Тест получения слов по группе"""
        if not self.created_group_id:
            self.log_test("Get Words by Group", False, "No group ID available")
            return
            
        try:
            params = {"group_id": self.created_group_id}
            response = self.make_request("GET", "/api/words", params=params)
            success = response.status_code == 200
            
            if success:
                words = response.json()
                details = f"Found {len(words)} words in group"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Words by Group", success, details)
        except Exception as e:
            self.log_test("Get Words by Group", False, str(e))
    
    def test_update_word(self):
        """Тест обновления слова"""
        if not self.created_word_id:
            self.log_test("Update Word", False, "No word ID available")
            return
            
        try:
            data = {
                "name": f"updated keyword {int(time.time())}"
            }
            response = self.make_request("PUT", f"/api/words/{self.created_word_id}", data)
            success = response.status_code == 200
            
            if success:
                word_data = response.json()
                details = f"Word updated: {word_data.get('name')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Update Word", success, details)
        except Exception as e:
            self.log_test("Update Word", False, str(e))
    
    def test_create_llm_provider(self):
        """Тест создания LLM провайдера"""
        try:
            data = {
                "name": f"Test LLM {int(time.time())}",
                "api_url": "https://api.example.com/v1/chat",
                "api_key": "test_api_key_123"
            }
            response = self.make_request("POST", "/api/llm", data)
            success = response.status_code in [200, 201]
            
            if success:
                llm_data = response.json()
                self.created_llm_id = llm_data.get("uuid")
                details = f"LLM created: {llm_data.get('name')} (ID: {self.created_llm_id})"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Create LLM Provider", success, details)
        except Exception as e:
            self.log_test("Create LLM Provider", False, str(e))
    
    def test_get_llm_providers(self):
        """Тест получения списка LLM провайдеров"""
        try:
            response = self.make_request("GET", "/api/llm")
            success = response.status_code == 200
            
            if success:
                providers = response.json()
                details = f"Found {len(providers)} LLM providers"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get LLM Providers", success, details)
        except Exception as e:
            self.log_test("Get LLM Providers", False, str(e))
    
    def test_get_word_analytics(self):
        """Тест получения аналитики по слову"""
        if not self.created_word_id:
            self.log_test("Get Word Analytics", False, "No word ID available")
            return
            
        try:
            response = self.make_request("GET", f"/api/analytics/word/{self.created_word_id}")
            success = response.status_code == 200
            
            if success:
                analytics = response.json()
                word_name = analytics.get("word", {}).get("name", "Unknown")
                serp_count = len(analytics.get("serp_results", []))
                companies_count = len(analytics.get("companies", []))
                details = f"Word: {word_name}, SERP: {serp_count}, Companies: {companies_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Word Analytics", success, details)
        except Exception as e:
            self.log_test("Get Word Analytics", False, str(e))
    
    def test_get_group_analytics(self):
        """Тест получения аналитики по группе"""
        if not self.created_group_id:
            self.log_test("Get Group Analytics", False, "No group ID available")
            return
            
        try:
            response = self.make_request("GET", f"/api/analytics/group/{self.created_group_id}")
            success = response.status_code == 200
            
            if success:
                analytics = response.json()
                group_name = analytics.get("group", {}).get("name", "Unknown")
                words_count = len(analytics.get("words", []))
                details = f"Group: {group_name}, Words: {words_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Group Analytics", success, details)
        except Exception as e:
            self.log_test("Get Group Analytics", False, str(e))
    
    def test_get_stats(self):
        """Тест получения общей статистики"""
        try:
            response = self.make_request("GET", "/api/stats")
            success = response.status_code == 200
            
            if success:
                stats = response.json()
                details = f"Stats: {json.dumps(stats, indent=2)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Get Stats", success, details)
        except Exception as e:
            self.log_test("Get Stats", False, str(e))
    
    def test_run_worker_cycle(self):
        """Тест запуска воркера"""
        try:
            response = self.make_request("POST", "/api/worker/run-cycle")
            success = response.status_code == 200
            
            if success:
                result = response.json()
                details = f"Worker started: {result.get('message', 'No message')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Run Worker Cycle", success, details)
        except Exception as e:
            self.log_test("Run Worker Cycle", False, str(e))
    
    def test_delete_word(self):
        """Тест удаления слова"""
        if not self.created_word_id:
            self.log_test("Delete Word", False, "No word ID available")
            return
            
        try:
            response = self.make_request("DELETE", f"/api/words/{self.created_word_id}")
            success = response.status_code == 200
            
            if success:
                result = response.json()
                details = f"Word deleted: {result.get('message', 'No message')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Delete Word", success, details)
        except Exception as e:
            self.log_test("Delete Word", False, str(e))
    
    def test_delete_word_group(self):
        """Тест удаления группы слов"""
        if not self.created_group_id:
            self.log_test("Delete Word Group", False, "No group ID available")
            return
            
        try:
            response = self.make_request("DELETE", f"/api/word-groups/{self.created_group_id}")
            success = response.status_code == 200
            
            if success:
                result = response.json()
                details = f"Group deleted: {result.get('message', 'No message')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Delete Word Group", success, details)
        except Exception as e:
            self.log_test("Delete Word Group", False, str(e))
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Starting SEO Analyzer API Tests")
        print("=" * 50)
        
        # Тесты инфраструктуры
        self.test_server_health()
        
        # Тесты авторизации
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        
        # Тесты групп слов
        self.test_create_word_group()
        self.test_get_word_groups()
        self.test_update_word_group()
        
        # Тесты слов
        self.test_create_word()
        self.test_get_words()
        self.test_get_words_by_group()
        self.test_update_word()
        
        # Тесты LLM провайдеров
        self.test_create_llm_provider()
        self.test_get_llm_providers()
        
        # Тесты аналитики
        self.test_get_word_analytics()
        self.test_get_group_analytics()
        self.test_get_stats()
        
        # Тесты воркера
        self.test_run_worker_cycle()
        
        # Тесты удаления (в конце)
        self.test_delete_word()
        self.test_delete_word_group()
        
        # Вывод результатов
        self.print_summary()
    
    def print_summary(self):
        """Вывод сводки результатов тестирования"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result['status']} {result['test']}")
        
        # Сохранение результатов в файл
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: test_results.json")

def main():
    """Главная функция"""
    print("🔧 SEO Analyzer API Comprehensive Test Suite")
    print("This script will test all API endpoints")
    print("Make sure the server is running on http://localhost:5000")
    
    input("Press Enter to continue...")
    
    tester = SEOAnalyzerTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
