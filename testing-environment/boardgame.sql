create table boardgame
(
    name       varchar(255) not null,
    bgg_rating int          not null,
    game_id    int auto_increment
        primary key
);

INSERT INTO `database`.boardgame (name, bgg_rating, game_id) VALUES ('Game 1', 80, 1);
INSERT INTO `database`.boardgame (name, bgg_rating, game_id) VALUES ('Game 2', 95, 2);
