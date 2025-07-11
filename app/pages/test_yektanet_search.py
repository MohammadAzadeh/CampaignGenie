#!/usr/bin/env python3
"""
Test script for Yektanet search functionality.
"""

from kb import search_yektanet

def test_yektanet_search():
    """Test the Yektanet search function with a sample query."""
    
    # Test query (the one from your example)
    query = "دیوار"
    
    print(f"Searching Yektanet for: '{query}'")
    print("=" * 50)
    
    results = search_yektanet(query)
    
    if results:
        print(f"Found {len(results)} results:")
        print()
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print()
    else:
        print("No results found or error occurred.")
    
    return results

if __name__ == "__main__":
    res = test_yektanet_search() 
    print("=========================")
    print(res)