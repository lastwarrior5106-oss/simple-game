import random

async def test_create_team(client):
    user = (await client.post("/users/")).json()
    team_name = f"TestTakim{random.randint(1, 999999)}"
    response = await client.post(f"/teams/?name={team_name}&creator_id={user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Team created successfully"
    assert data["creator_remaining_coins"] == 4000

async def test_team_full(client):
    user = (await client.post("/users/")).json()
    team_name = f"DoluTakim{random.randint(1, 999999)}"
    team = (await client.post(f"/teams/?name={team_name}&creator_id={user['id']}")).json()
    team_id = team["team_details"]["id"]

    for _ in range(19):
        new_user = (await client.post("/users/")).json()
        await client.put(f"/teams/{team_id}/join/{new_user['id']}")

    extra_user = (await client.post("/users/")).json()
    response = await client.put(f"/teams/{team_id}/join/{extra_user['id']}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Team is full"