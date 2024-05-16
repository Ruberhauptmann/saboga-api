def test_read_main(client):
    response = client.get("/v1/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
