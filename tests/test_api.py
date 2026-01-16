import pytest
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Сначала импортируем приложение
from app.main import app

# Потом импортируем TestClient из правильного места
try:
    # Для новых версий FastAPI
    from fastapi.testclient import TestClient
except ImportError:
    # Для старых версий
    from starlette.testclient import TestClient

client = TestClient(app)

def test_root():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    print("✅ test_root пройден")

def test_health():
    """Тест проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ test_health пройден")

def test_create_place():
    """Тест создания нового места"""
    # Создаем тестовое изображение в памяти
    test_image = b"fake_image_data"
    
    response = client.post(
        "/places/",
        files={
            "photo": ("test.jpg", test_image, "image/jpeg")
        },
        data={
            "title": "Тестовое место для API",
            "description": "Описание тестового места",
            "lat": 53.2,
            "lon": 50.2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Тестовое место для API"
    assert data["lat"] == 53.2
    assert data["lon"] == 50.2
    assert "id" in data
    assert "photo_url" in data
    print(f"✅ test_create_place пройден, создано место с ID: {data['id']}")
    return data["id"]

def test_get_places():
    """Тест получения списка мест"""
    response = client.get("/places/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        place = data[0]
        assert "title" in place
        assert "lat" in place
        assert "lon" in place
    print(f"✅ test_get_places пройден, найдено {len(data)} мест")

def test_bbox_search():
    """Тест поиска по bounding box"""
    # Сначала создаем тестовое место
    test_image = b"bbox_test_image"
    response = client.post(
        "/places/",
        files={"photo": ("test_bbox.jpg", test_image, "image/jpeg")},
        data={
            "title": "Место для поиска по bbox",
            "description": "Тест поиска",
            "lat": 53.25,
            "lon": 50.25
        }
    )
    assert response.status_code == 200
    
    # Ищем в области где должно быть наше место
    response = client.get("/places/bbox/?min_lat=53.2&max_lat=53.3&min_lon=50.2&max_lon=50.3")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Ищем в области где НЕ должно быть мест
    response = client.get("/places/bbox/?min_lat=0&max_lat=1&min_lon=0&max_lon=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # В этой области не должно быть мест
    print("✅ test_bbox_search пройден")

def test_bbox_validation():
    """Тест валидации координат"""
    # Неправильные координаты (широта > 90)
    response = client.get("/places/bbox/?min_lat=-100&max_lat=53.5&min_lon=49.5&max_lon=50.5")
    assert response.status_code == 400
    
    # Неправильные координаты (долгота > 180)
    response = client.get("/places/bbox/?min_lat=53.0&max_lat=53.5&min_lon=200&max_lon=250")
    assert response.status_code == 400
    print("✅ test_bbox_validation пройден")

def test_image_validation():
    """Тест валидации изображений"""
    # Пытаемся загрузить не изображение
    response = client.post(
        "/places/",
        files={
            "photo": ("test.txt", b"not an image", "text/plain")
        },
        data={
            "title": "Неправильный файл",
            "lat": 53.0,
            "lon": 50.0
        }
    )
    assert response.status_code == 400
    assert "Файл должен быть изображением" in response.text
    print("✅ test_image_validation пройден")

# Простой запуск без pytest
def run_all_tests():
    """Запуск всех тестов вручную"""
    print("=== Запуск тестов API ===")
    
    tests = [
        test_root,
        test_health,
        test_get_places,
        test_bbox_validation,
        test_image_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} не пройден: {e}")
            failed += 1
    
    # Тесты которые создают данные - запускаем последними
    try:
        test_create_place()
        passed += 1
    except Exception as e:
        print(f"❌ test_create_place не пройден: {e}")
        failed += 1
    
    try:
        test_bbox_search()
        passed += 1
    except Exception as e:
        print(f"❌ test_bbox_search не пройден: {e}")
        failed += 1
    
    print(f"\n=== Итог: {passed} пройдено, {failed} не пройдено ===")
    
    if failed == 0:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены")

if __name__ == "__main__":
    run_all_tests()
