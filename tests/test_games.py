from sabogaapi.models import Boardgame


def test_games(client, session):
    game_1 = Boardgame(
        name="Game 1",
        bgg_rating=5.5,
        bgg_id=1,
        bgg_weight=3.5,
        owner="Nobody",
        player_min=1,
        player_max=8,
        player_recommended_min=1,
        player_recommended_max=6
    )
    game_2 = Boardgame(
        name="Test",
        bgg_rating=8.5,
        bgg_id=2,
        bgg_weight=2,
        owner="Somebody",
        player_min=2,
        player_max=6,
        player_recommended_min=2,
        player_recommended_max=4
    )
    session.add(game_1)
    session.add(game_2)
    session.commit()

    response = client.get('/boardgames/')
    data = response.json()

    assert response.status_code == 200

    assert len(data) == 2
