import xml.etree.ElementTree as ET

from sabogaapi.scraper._fill_in_data import parse_boardgame_data


def test_parse_xml():
    tree = ET.parse("tests/test_scraper.xml")
    item = tree.findall("item")[0]
    data = parse_boardgame_data(item)

    assert data["bgg_id"] == 224517
    assert data["name"] == "Brass: Birmingham"
    assert (
        data["image_url"]
        == "https://cf.geekdo-images.com/x3zxjr-Vw5iU4yDPg70Jgw__original/img/FpyxH41Y6_ROoePAilPNEhXnzO8=/0x0/filters:format(jpeg)/pic3490053.jpg"
    )
    assert (
        data["description"]
        == "Brass: Birmingham is an economic strategy game sequel to Martin Wallace's 2007 masterpiece, Brass. Brass: Birmingham tells the story of competing entrepreneurs in Birmingham during the industrial revolution between the years of 1770 and 1870.\n\nIt offers a very different story arc and experience from its predecessor. As in its predecessor, you must develop, build and establish your industries and network in an effort to exploit low or high market demands. The game is played over two halves: the canal era (years 1770-1830) and the rail era (years 1830-1870). To win the game, score the most VPs. VPs are counted at the end of each half for the canals, rails and established (flipped) industry tiles.\n\nEach round, players take turns according to the turn order track, receiving two actions to perform any of the following actions (found in the original game):\n\n1) Build - Pay required resources and place an industry tile.\n2) Network - Add a rail / canal link, expanding your network.\n3) Develop - Increase the VP value of an industry.\n4) Sell - Sell your cotton, manufactured goods and pottery.\n5) Loan - Take a £30 loan and reduce your income.\n\nBrass: Birmingham also features a new sixth action:\n\n6) Scout - Discard three cards and take a wild location and wild industry card. (This action replaces Double Action Build in original Brass.)\n\n"
    )
    assert data["rank"] == 1
    assert data["average_rating"] == 8.57479
    assert data["geek_rating"] == 8.40067
    assert data["year_published"] == 2018
    assert data["minplayers"] == 2
    assert data["maxplayers"] == 4
    assert data["playingtime"] == 120
    assert data["minplaytime"] == 60
    assert data["maxplaytime"] == 120
