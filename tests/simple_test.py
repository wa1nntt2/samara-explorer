#!/usr/bin/env python3
"""Простой тест API без сложных зависимостей"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_root():
    """Тест главной страницы"""
    print("Тест 1: Главная страница...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успех: {data}")
            return True
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_health():
    """Тест проверки здоровья"""
    print("\nТест 2: Проверка здоровья...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успех: {data}")
            return True
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_get_places():
    """Тест получения списка мест"""
    print("\nТест 3: Получение списка мест...")
    try:
        response = requests.get(f"{BASE_URL}/places/")
        if response.status_code == 200:
            places = response.json()
            print(f"✅ Успех: найдено {len(places)} мест")
            if len(places) > 0:
                print(f"   Пример: {places[0]['title'][:50]}...")
            return True
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_bbox_search():
    """Тест поиска по области"""
    print("\nТест 4: Поиск по области (bbox)...")
    try:
        # Область Самары
        params = {
            "min_lat": 53.0,
            "max_lat": 53.5,
            "min_lon": 49.5,
            "max_lon": 50.5
        }
        response = requests.get(f"{BASE_URL}/places/bbox/", params=params)
        if response.status_code == 200:
            places = response.json()
            print(f"✅ Успех: найдено {len(places)} мест в области Самары")
            return True
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_bbox_validation():
    """Тест валидации координат"""
    print("\nТест 5: Валидация координат (должна быть ошибка)...")
    try:
        # Неправильные координаты
        params = {
            "min_lat": -100,  # Неправильно!
            "max_lat": 53.5,
            "min_lon": 49.5,
            "max_lon": 50.5
        }
        response = requests.get(f"{BASE_URL}/places/bbox/", params=params)
        if response.status_code == 400:
            print(f"✅ Успех: сервер вернул ошибку валидации как и ожидалось")
            return True
        else:
            print(f"⚠️  Неожиданный ответ: статус {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("Тестирование Samara Explorer API")
    print("=" * 60)
    
    # Проверяем доступность сервера
    print("\nПроверка доступности сервера...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code == 200:
            print("✅ Сервер доступен")
        else:
            print(f"❌ Сервер недоступен: статус {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Не удалось подключиться к серверу: {e}")
        print("Убедитесь, что сервер запущен: uvicorn app.main:app --reload")
        return
    
    # Запускаем тесты
    tests = [
        test_root,
        test_health,
        test_get_places,
        test_bbox_search,
        test_bbox_validation,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Итог
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"ИТОГ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Отлично! Все тесты пройдены!")
    else:
        print("⚠️  Некоторые тесты не пройдены")

if __name__ == "__main__":
    main()
