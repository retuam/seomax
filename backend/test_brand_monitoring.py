#!/usr/bin/env python3
"""
Тест Brand Monitoring функционала
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

# Конфигурация
BASE_URL = "http://localhost:5000"
TEST_EMAIL = f"brand_test_{int(time.time())}@example.com"
TEST_PASSWORD = "testpassword123"

class BrandMonitoringTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.headers = {}
        
    def register_and_login(self) -> bool:
        """Регистрация и авторизация тестового пользователя"""
        try:
            # Регистрация
            register_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/api/auth/register", json=register_data)
            if response.status_code not in [200, 201]:
                print(f"❌ Ошибка регистрации: {response.status_code}")
                return False
            
            # Логин
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ Ошибка авторизации: {response.status_code}")
                return False
            
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
            print("✅ Авторизация успешна")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False
    
    def test_create_brand_project(self) -> Dict[str, Any]:
        """Тест создания brand проекта"""
        try:
            project_data = {
                "name": "Test Brand Project",
                "brand_name": "TechCorp",
                "brand_description": "Инновационная IT компания, разрабатывающая программное обеспечение для бизнеса. Специализируемся на CRM системах, автоматизации процессов и облачных решениях.",
                "keywords_count": 20,
                "competitors": [
                    "Microsoft",
                    "Salesforce", 
                    "Oracle",
                    "SAP",
                    "HubSpot"
                ]
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/brand-projects",
                json=project_data,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                project = response.json()
                print(f"✅ Brand проект создан: {project['name']} (ID: {project['uuid']})")
                print(f"   - Бренд: {project['brand_name']}")
                print(f"   - Конкурентов: {len(project['competitors'])}")
                return project
            else:
                print(f"❌ Ошибка создания проекта: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Ошибка создания brand проекта: {e}")
            return {}
    
    def test_get_brand_projects(self) -> bool:
        """Тест получения списка brand проектов"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/brand-projects",
                headers=self.headers
            )
            
            if response.status_code == 200:
                projects = response.json()
                print(f"✅ Получен список проектов: {len(projects)} проектов")
                for project in projects:
                    print(f"   - {project['name']}: {project['brand_name']}")
                return True
            else:
                print(f"❌ Ошибка получения проектов: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения проектов: {e}")
            return False
    
    def test_get_brand_project(self, project_id: str) -> bool:
        """Тест получения конкретного brand проекта"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/brand-projects/{project_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                project = response.json()
                print(f"✅ Получен проект: {project['name']}")
                print(f"   - Бренд: {project['brand_name']}")
                print(f"   - Описание: {project['brand_description'][:50]}...")
                print(f"   - Конкурентов: {len(project['competitors'])}")
                return True
            else:
                print(f"❌ Ошибка получения проекта: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения проекта: {e}")
            return False
    
    def test_brand_analytics(self, project_id: str) -> bool:
        """Тест получения аналитики brand проекта"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/brand-projects/{project_id}/analytics",
                headers=self.headers
            )
            
            if response.status_code == 200:
                analytics = response.json()
                print(f"✅ Получена аналитика проекта")
                print(f"   - Всего запросов: {analytics['total_queries']}")
                print(f"   - Упоминаний бренда: {analytics['brand_mentions']}")
                print(f"   - Упоминаний конкурентов: {analytics['competitor_mentions']}")
                print(f"   - Видимость бренда: {analytics['brand_visibility_percentage']:.1f}%")
                print(f"   - Видимость конкурентов: {analytics['competitor_visibility_percentage']:.1f}%")
                
                if analytics['top_competitors']:
                    print("   - Топ конкуренты:")
                    for comp in analytics['top_competitors'][:3]:
                        print(f"     • {comp['name']}: {comp['mentions']} упоминаний")
                
                return True
            else:
                print(f"❌ Ошибка получения аналитики: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения аналитики: {e}")
            return False
    
    def test_delete_brand_project(self, project_id: str) -> bool:
        """Тест удаления brand проекта"""
        try:
            response = self.session.delete(
                f"{BASE_URL}/api/brand-projects/{project_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Brand проект удален")
                return True
            else:
                print(f"❌ Ошибка удаления проекта: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка удаления проекта: {e}")
            return False
    
    def run_full_test(self):
        """Запуск полного теста Brand Monitoring"""
        print("🧪 ТЕСТИРОВАНИЕ BRAND MONITORING ФУНКЦИОНАЛА")
        print("=" * 60)
        
        # Авторизация
        if not self.register_and_login():
            return
        
        # Создание проекта
        project = self.test_create_brand_project()
        if not project:
            return
        
        project_id = project['uuid']
        
        # Получение списка проектов
        self.test_get_brand_projects()
        
        # Получение конкретного проекта
        self.test_get_brand_project(project_id)
        
        # Ожидание генерации ключевых слов (фоновая задача)
        print("\n⏳ Ожидание генерации ключевых слов (30 секунд)...")
        time.sleep(30)
        
        # Получение аналитики
        self.test_brand_analytics(project_id)
        
        # Удаление проекта
        self.test_delete_brand_project(project_id)
        
        print("\n" + "=" * 60)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")

def main():
    """Основная функция"""
    tester = BrandMonitoringTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
