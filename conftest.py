import pytest
import json
import allure


ROUTING_BASE_URL = "http://routing.api.2gis.com/routing/7.0.0/global"
PLACES_BASE_URL = "https://catalog.api.2gis.com/3.0/items"
#API_KEY = "ffaa9fce-3d28-4faf-aef9-2f8f36a207e3"
API_KEY = "624404dc-3c68-404e-ad0a-fc3c4e418636"

TEST_POINTS = {
    "Moscow_1": [
        {"type": "stop", "lon": 37.582591, "lat": 55.775364},
        {"type": "stop", "lon": 37.579206, "lat": 55.774362}
    ],
    "Moscow_2": [
        {"type": "stop", "lon": 37.617494, "lat": 55.751999},
        {"type": "stop", "lon": 37.615655, "lat": 55.768005}
    ]
}

LOMONOSOV_SQUARE = "30.334575,59.928964"
PACIFIC_OCEAN = "-121.485531,-52.667643"

with open('schemas/routingResponseSchema.json', 'r') as schema:
    ROUTE_RESPONSE_SCHEMA = json.load(schema)

@pytest.fixture
def route_payload():
    def build_route_payload(points, **kwargs):
        payload = {
            "points": points,
            "locale": "ru",
            "transport": "driving",
            "route_mode": "fastest",
            "traffic_mode": "jam",
            "output": "detailed"
        }
        payload.update(kwargs)
        return payload
    return build_route_payload

@pytest.fixture
def test_points():
    return TEST_POINTS

@pytest.fixture
def locations():
    return {
        "lomonosov_square": LOMONOSOV_SQUARE,
        "pacific_ocean": PACIFIC_OCEAN
    }

@pytest.fixture
def api_config():
    return {
        "routing_url": ROUTING_BASE_URL,
        "places_url": PLACES_BASE_URL,
        "api_key": API_KEY,
        "timeout": 10
    }

@pytest.fixture
def schemas():
    return {
        "routing": ROUTE_RESPONSE_SCHEMA
    }

def attach_request_response(allure_step, request_data, response):
    """Прикрепляет данные запроса и ответа к отчету"""
    with allure_step:
        allure.attach(
            json.dumps(request_data, indent=2, ensure_ascii=False),
            name="Request Body",
            attachment_type=allure.attachment_type.JSON
        )
        
        try:
            response_json = response.json()
            allure.attach(
                json.dumps(response_json, indent=2, ensure_ascii=False),
                name="Response Body",
                attachment_type=allure.attachment_type.JSON #attachment_type="application/json"
            )
        except:
            allure.attach(
                response.text,
                name="Response Text",
                attachment_type=allure.attachment_type.TEXT
            )

@pytest.fixture
def attach_bodies():
    return attach_request_response