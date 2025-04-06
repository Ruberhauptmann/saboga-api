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
