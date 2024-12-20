import pytest
from pathlib import Path
from filetree.core.route_analyzer import RouteAnalyzer

def test_similar_routes(mock_file_tree):
    """Test detection of similar directory structures."""
    analyzer = RouteAnalyzer(mock_file_tree)
    analyzer.analyze()
    
    similar_routes = analyzer.get_similar_routes()
    
    # Should detect src/utils and lib/utils as similar
    assert len(similar_routes) > 0
    assert any(
        "src/utils" in str(path1) and "lib/utils" in str(path2)
        for path1, path2, _ in similar_routes
    )

def test_similarity_threshold():
    """Test that similarity threshold is respected."""
    with pytest.fixture(autouse=True) as mock_file_tree:
        analyzer_strict = RouteAnalyzer(mock_file_tree, threshold=0.99)
        analyzer_strict.analyze()
        strict_routes = analyzer_strict.get_similar_routes()
        
        analyzer_loose = RouteAnalyzer(mock_file_tree, threshold=0.5)
        analyzer_loose.analyze()
        loose_routes = analyzer_loose.get_similar_routes()
        
        # Strict threshold should find fewer similar routes
        assert len(strict_routes) < len(loose_routes)

def test_duplicate_routes(mock_file_tree):
    """Test detection of duplicate directory patterns."""
    # Create a duplicate directory structure
    (mock_file_tree / "src2" / "utils").mkdir(parents=True)
    (mock_file_tree / "src2" / "utils" / "helper.py").touch()
    
    analyzer = RouteAnalyzer(mock_file_tree)
    analyzer.analyze()
    
    duplicates = analyzer.get_duplicate_routes()
    
    # Should detect utils directory pattern as duplicate
    assert any(
        pattern == "utils" 
        for pattern, paths in duplicates
    ) 