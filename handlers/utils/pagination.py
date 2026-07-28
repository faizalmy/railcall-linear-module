"""Pagination utilities for Linear GraphQL queries."""

from typing import Any, Callable, Dict, List, Optional


def paginate_query(
    query_func: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    query: str,
    variables: Dict[str, Any],
    limit: int,
    data_key: str,
    nodes_key: str = "nodes",
) -> List[Dict[str, Any]]:
    """Execute paginated GraphQL query.
    
    Args:
        query_func: Function to execute GraphQL query
        query: GraphQL query string with pagination support
        variables: Query variables
        limit: Maximum number of results
        data_key: Key in response data (e.g., "issues", "teams")
        nodes_key: Key for nodes array (default: "nodes")
        
    Returns:
        List of all results up to limit
        
    Raises:
        ValidationError: If limit is invalid
    """
    all_results: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    
    while len(all_results) < limit:
        # Calculate batch size
        remaining = limit - len(all_results)
        batch_size = min(50, remaining)  # Linear recommends 50 per page
        
        # Add pagination variables
        variables["first"] = batch_size
        if cursor:
            variables["after"] = cursor
        
        # Execute query
        data = query_func(query, variables)
        
        # Extract results
        result_data = data.get(data_key, {})
        nodes = result_data.get(nodes_key, [])
        all_results.extend(nodes)

        # Check for more pages
        page_info = result_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")

        # Guard against a server claiming hasNextPage while returning no cursor or
        # no rows - without this the same page refetches forever.
        if not nodes or not cursor:
            break

    return all_results[:limit]
