def test_get_comments() -> None:
    from sql_unit.annotations import get_comments

    template_str = """
    -- This is a comment
    SELECT * FROM table; -- Another comment
    -- Yet another comment
    """
    comments = get_comments(template_str)
    assert not comments

    template_str = """
/*
    # sql-unit
    #1 item 1
    #2 item 2
    #3 item 3

*/

SELECT * FROM table
where true;
/*
    # sql-unit
    another one
*/

    """
    comments = get_comments(template_str)
    assert (
        comments
        == """
#1 item 1
#2 item 2
#3 item 3
another one
    """.strip()
    )
