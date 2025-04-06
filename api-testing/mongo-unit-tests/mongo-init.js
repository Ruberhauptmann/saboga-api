db = db.getSiblingDB("boardgames");

db.createUser({
  user: "api-user",
  pwd: "test",
  roles: [
    {
      role: "readWrite",
      db: "boardgames"
    }
  ]
});

// Optional: clear collections
db.boardgames.deleteMany({});
db.rankhistory.deleteMany({});

// Insert sample boardgames
db.boardgames.insertMany([
  {
    bgg_id: 1,
    name: "Catan",
    bgg_rank: 100,
    bgg_geek_rating: 6.9,
    bgg_average_rating: 7.1,
    description: "Trade, build, and settle the island of Catan.",
    image_url: null,
    thumbnail_url: null,
    year_published: 1995,
    minplayers: 3,
    maxplayers: 4,
    playingtime: 90,
    minplaytime: 60,
    maxplaytime: 120,
    categories: [],
    families: [],
    mechanics: [],
    designers: []
  },
  {
    bgg_id: 2,
    name: "Gloomhaven",
    bgg_rank: 1,
    bgg_geek_rating: 8.9,
    bgg_average_rating: 8.7,
    description: "A game of Euro-inspired tactical combat in a persistent world.",
    image_url: null,
    thumbnail_url: null,
    year_published: 2017,
    minplayers: 1,
    maxplayers: 4,
    playingtime: 120,
    minplaytime: 90,
    maxplaytime: 150,
    categories: [],
    families: [],
    mechanics: [],
    designers: []
  }
]);

// Insert sample rank history
const now = new Date();
const earlier = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 1 week ago

db.rankhistory.insertMany([
  {
    bgg_id: 1,
    date: earlier,
    bgg_rank: 105,
    bgg_geek_rating: 6.8,
    bgg_average_rating: 7.0
  },
  {
    bgg_id: 2,
    date: earlier,
    bgg_rank: 2,
    bgg_geek_rating: 8.8,
    bgg_average_rating: 8.6
  }
]);
