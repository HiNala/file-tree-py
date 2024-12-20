import pytest
from pathlib import Path
from filetree.core.route_analyzer import RouteAnalyzer

@pytest.fixture
def test_directory(tmp_path):
    """Create a test directory structure."""
    # Create test directories
    (tmp_path / "src" / "utils").mkdir(parents=True)
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "lib" / "utils").mkdir(parents=True)
    (tmp_path / "test" / "utils").mkdir(parents=True)
    return tmp_path

def test_similarity_threshold(test_directory):
    """Test route similarity analysis with different thresholds."""
    analyzer = RouteAnalyzer(test_directory, similarity_threshold=0.5)
    similar_routes = analyzer.find_similar_routes()
    
    # With threshold 0.5, we should find multiple similar routes
    assert len(similar_routes) > 0
    
    # All similarities should be >= 0.5
    for route1, route2, similarity in similar_routes:
        assert similarity >= 0.5
        assert isinstance(route1, str)
        assert isinstance(route2, str)
        assert isinstance(similarity, float)

    # Test with higher threshold
    analyzer = RouteAnalyzer(test_directory, similarity_threshold=0.9)
    similar_routes = analyzer.find_similar_routes()
    
    # With threshold 0.9, we should find fewer similar routes
    assert len(similar_routes) < len(analyzer.routes)

def test_path_normalization(test_directory):
    """Test that path separators are normalized correctly."""
    analyzer = RouteAnalyzer(test_directory)
    
    # Test internal _compute_similarity method
    similarity = analyzer._compute_similarity(
        "src\\utils\\helpers",
        "src/utils/common"
    )
    assert similarity > 0.6  # First two components match