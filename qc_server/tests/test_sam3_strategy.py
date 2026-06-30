from app.services.inference import sam3


def test_simplify_polygon_reduces_collinear_and_clamps():
    pts = [[10, 10], [25, 10], [40, 10], [40, 40], [10, 40]]
    out = sam3.simplify_polygon(pts, epsilon=2.0, width=100, height=100)
    assert out == [[10, 10], [40, 10], [40, 40], [10, 40]]
    assert all(isinstance(x, int) and isinstance(y, int) for x, y in out)


def test_simplify_polygon_clamps_out_of_bounds():
    pts = [[-5, -5], [200, -5], [200, 200], [-5, 200]]
    out = sam3.simplify_polygon(pts, epsilon=2.0, width=100, height=80)
    assert out == [[0, 0], [100, 0], [100, 80], [0, 80]]


def test_simplify_polygon_drops_degenerate():
    assert sam3.simplify_polygon([[1, 1], [2, 2]], epsilon=2.0, width=10, height=10) == []
