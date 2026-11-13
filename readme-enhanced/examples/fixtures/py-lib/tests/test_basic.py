from textstats import reading_time, sentences, words


def test_counts():
    assert words("one two three") == 3
    assert sentences("Hi. There!") == 2
    assert reading_time("word " * 400) == 2.0
