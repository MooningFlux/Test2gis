import pytest
import requests
import json
import allure
from jsonschema import validate


@pytest.mark.routing
@allure.story('Routing API')
@allure.title('Building route with 2 points: driving')
@pytest.mark.parametrize("points_key", ["Moscow_1", "Moscow_2"])
def test_build_driving_route(points_key, route_payload, test_points, api_config, schemas, attach_bodies):
    """Тест построения автомобильного маршрута между двумя точками"""
    points = test_points[points_key]
    payload = route_payload(points)
    
    response = requests.post(
        api_config["routing_url"],
        params={"key": api_config["api_key"]},
        json=payload,
        timeout=api_config["timeout"]
    )
    
    attach_bodies(
        allure.step("Attach request/response data"),
        {"points": points, "payload": payload},
        response
    )
    
    with allure.step("Check on http status code"):
        assert response.status_code == 200, f"Error: {response.status_code}"
    
    response_data = response.json()
    
    with allure.step("Validate JSON schema"):
        validate(instance=response_data, schema=schemas["routing"])
    
    with allure.step("Check on business logic"):
        assert response_data["status"] == "OK"
        assert response_data["type"] == "result"
        assert len(response_data["result"]) > 0
        
        route = response_data["result"][0]
        
        assert route["total_distance"] > 0
        assert route["total_duration"] > 0
        assert "algorithm" in route
        assert len(route["maneuvers"]) >= 2  #start, end

    with allure.step("Check on total route calculation"):
        total_distance = route["total_distance"]
        total_segment_distance = 0
        
        for segment in route["maneuvers"]:
            if "outcoming_path" in segment and segment["outcoming_path"]:
                segment_distance = segment["outcoming_path"]["distance"]
                total_segment_distance += segment_distance

        allure.attach(
            json.dumps({
                "total_distance": total_distance,
                "total_segment_distance": total_segment_distance,
                "segments_count": len(route["maneuvers"])
            }, indent = 2, ensure_ascii=False),
            name = "Total distance info",
            attachment_type=allure.attachment_type.JSON
        )

        assert total_distance == total_segment_distance, f"total_distance:{total_distance} не совпадает \
            с рассчитанным по-сегментно:{total_segment_distance}"


@pytest.mark.routing
@allure.story('Routing API')
@allure.title('Test traffic modes')
@pytest.mark.parametrize("traffic_mode, expected_algorithm", [
    ("jam", "с учётом пробок"),
    ("statistics", "без учёта пробок")
])
def test_traffic_modes(traffic_mode, expected_algorithm, route_payload, test_points, api_config, schemas):
    """Тестирование режимов учета пробок"""
    points = test_points["Moscow_1"]
    payload = route_payload(points, traffic_mode=traffic_mode)
    
    response = requests.post(
        api_config["routing_url"],
        params={"key": api_config["api_key"]},
        json=payload,
        timeout=api_config["timeout"]
    )
    
    with allure.step("Check on http status code"):
        assert response.status_code == 200, f"Error: {response.status_code}"

    response_data = response.json()

    with allure.step("Validate JSON schema"):
        validate(instance=response_data, schema=schemas["routing"])
    
    with allure.step(f"Check on algorithm's traffic mode {traffic_mode}"):
        route = response_data["result"][0]
        assert expected_algorithm == route["algorithm"]


@pytest.mark.routing
@allure.story('Routing API')
@allure.title('Check error handling with invalid input')
def test_error_handling(route_payload, api_config, attach_bodies):
    """Тест обработки ошибок при некорректных данных в теле"""

    invalid_payload = route_payload(points=[])
    
    response = requests.post(
        api_config["routing_url"],
        params={"key": api_config["api_key"]},
        json=invalid_payload,
        timeout=api_config["timeout"]
    )
    
    attach_bodies(
        allure.step("Attach request/response data"),
        {"payload": invalid_payload},
        response
    )   

    assert response.status_code == 400


@pytest.mark.catalog
@allure.story('Places API')
@allure.title('Search places by text query and validate attributes')
def test_search_places_by_query(api_config, locations, attach_bodies):
    """Тест поиска мест по текстовому запросу и проверка атрибутов объектов"""
    params = {
        "q": "кафе",
        "location": locations["lomonosov_square"],
        "key": api_config["api_key"],
        "fields": "items.point"
    }
    
    with allure.step("Search for cafes near Lomonosov Square"):
        response = requests.get(
            api_config["places_url"],
            params=params,
            timeout=api_config["timeout"]
        )
    
    attach_bodies(
        allure.step("Attach places request/response data"),
        {"params": params},
        response
    )
    
    with allure.step("Check on http status code"):
        assert response.status_code == 200, f"Error: {response.status_code}"
    
    response_data = response.json()
      
    with allure.step("Check response structure and object attributes"):
        assert "items" in response_data["result"]
        
        items = response_data["result"]["items"]
        total = response_data["result"]["total"]
        
        assert total > 0, "No places found for the query"
        assert len(items) > 0, "Items array is empty"
        
        first_place = items[0]
        
        required_attributes = {"id", "name", "type"}
        for attr in required_attributes:
            assert attr in first_place, f"Missing required attributes: {attr}"
            assert first_place[attr], f"Attribute {attr} is null"
            assert first_place[attr] != "", f"Attribute {attr} is empty"
        
        allure.attach(
            json.dumps({
                "first_place_attributes": first_place,
                "total_places_found": total,
                "items_returned": len(items)
            }, indent=2, ensure_ascii=False),
            name="Places search results",
            attachment_type=allure.attachment_type.JSON
        )
        
    with allure.step("Check if first item has correct 'point' attribute"):
        point = first_place["point"]
        assert "lon" in point, "Point missing lon coordinate"
        assert "lat" in point, "Point missing lat coordinate"
        assert 29.0 < point["lon"] < 31.0, f"Invalid longitude: {point['lon']}"
        assert 58.0 < point["lat"] < 60.0, f"Invalid latitude: {point['lat']}"

@pytest.mark.catalog
@allure.story('Places API')
@allure.title('Search deserted/unsupported places by text query')
def test_search_deserted_places_by_query(api_config, locations, attach_bodies):
    """Тест поиска по текстовому запросу неподдерживаемого места"""
    params = {
        "q": "вода соленая",
        "location": locations["pacific_ocean"],
        "key": api_config["api_key"],
    }
    
    with allure.step("Search for salty water in the Pacific Ocean"):
        response = requests.get(
            api_config["places_url"],
            params=params,
            timeout=api_config["timeout"]
        )

    attach_bodies(
        allure.step("Attach places request/response data"),
        {"params": params},
        response
    )

    with allure.step("Check on http status code"):
        assert response.status_code == 200, f"Error: {response.status_code}"
    
    response_data = response.json()
    with allure.step("Check on real status code"):
        assert "meta" in response_data
        assert response_data["meta"]["code"] == 404, f'Expected 404 status code, got {response_data["meta"]["code"]}'