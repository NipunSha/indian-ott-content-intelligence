from ott_intel import parse as P

BOX = """{{Short description|x}}
{{Infobox television
| name = Example Show
| genre = [[Crime film|Crime]]<br>[[Thriller (genre)|Thriller]]
| starring = {{Plainlist|
* [[Actor One]]
* [[Actor Two (actor)|Actor Two]]
* Actor Three
}}
| country = India
| language = Hindi
| num_seasons = 2
| num_episodes = 18<ref>x</ref>
| network = [[SonyLIV]]
| released = {{Start date|2020|5|15|df=y}}
| company = [[Applause Entertainment]]
}}
'''''Example Show''''' is a 2020 Indian [[Hindi]]-language crime thriller television series."""


def test_infobox_fields():
    ib = P.infobox(BOX)
    assert ib["_type"] == "infobox television"
    assert ib["language"] == "Hindi" and P.first_int(ib["num_episodes"]) == 18
    assert P.parse_date(ib["released"]) == "2020-05-15"
    assert P.listify(ib["starring"], limit=2) == ["Actor One", "Actor Two (actor)"]
    assert P.listify(ib["company"]) == ["Applause Entertainment"]


def test_dates_plain_text_and_film_template():
    assert P.parse_date("15 May 2020") == "2020-05-15"
    assert P.parse_date("May 15, 2020") == "2020-05-15"
    assert P.parse_date("{{Film date|df=y|2021|6|4}}") == "2021-06-04"
    assert P.parse_date("2020") is None and P.parse_date("") is None


def test_genre_and_language_mapping():
    assert P.genres("Crime thriller")[:2] == ["Crime", "Thriller"]
    assert P.genres("Drama; Romantic")[0] == "Drama" and P.genres("Action thriller")[0] == "Action"   # text order, not keyword order
    assert P.genres("award-winning drama") == ["Drama"]                                             # "war" must not match inside "award"
    assert P.languages("Tamil and Hindi") == ["Tamil", "Hindi"]
    assert P.genres("romantic comedy") == ["Romance", "Comedy"]
    assert P.genres("", "an Indian horror film") == ["Horror"]
    assert P.languages("", "a 2022 Indian Tamil-language film") == ["Tamil"]
    assert "Indian" not in P.languages("Indian English")


def test_lead_sentence_strips_templates():
    assert "2020 Indian Hindi-language crime thriller" in P.lead_sentence(BOX)
