async def test_create_user(client):
    response = await client.post("/users/")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == 1
    assert data["coins"] == 5000

async def test_level_up(client):
    user = (await client.post("/users/")).json()
    response = await client.put(f"/users/{user['id']}/level-up")
    assert response.status_code == 200
    assert response.json()["new_level"] == 2
    assert response.json()["new_coins"] == 5025
