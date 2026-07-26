"""Tests for pagination helpers."""

from unittest.mock import Mock

from handlers.utils.pagination import paginate_query


def _page(nodes, has_next, cursor):
    return {"issues": {"nodes": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": cursor}}}


class TestPaginateQuery:
    def test_follows_the_cursor_across_pages(self):
        query_func = Mock(side_effect=[
            _page([{"id": "1"}], True, "cur-1"),
            _page([{"id": "2"}], False, None),
        ])

        results = paginate_query(query_func, "q", {}, limit=10, data_key="issues")

        assert [r["id"] for r in results] == ["1", "2"]
        assert query_func.call_args_list[1].args[1]["after"] == "cur-1"

    def test_stops_at_the_limit(self):
        query_func = Mock(return_value=_page([{"id": str(i)} for i in range(50)], True, "cur"))

        results = paginate_query(query_func, "q", {}, limit=3, data_key="issues")

        assert len(results) == 3

    def test_does_not_loop_forever_without_a_cursor(self):
        """hasNextPage true + endCursor null used to refetch the same page forever."""
        query_func = Mock(return_value=_page([{"id": "1"}], True, None))

        results = paginate_query(query_func, "q", {}, limit=100, data_key="issues")

        assert results == [{"id": "1"}]
        assert query_func.call_count == 1

    def test_does_not_loop_forever_on_empty_pages(self):
        """hasNextPage true with zero rows must also terminate."""
        query_func = Mock(return_value=_page([], True, "cur"))

        results = paginate_query(query_func, "q", {}, limit=100, data_key="issues")

        assert results == []
        assert query_func.call_count == 1
