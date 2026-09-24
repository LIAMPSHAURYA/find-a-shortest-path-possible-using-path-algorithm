"""Run with:  python -m unittest tests -v"""
import itertools
import random
import tempfile
import unittest
from pathlib import Path

from algorithms import dijkstra, k_shortest, path_cost
from graph import DataError, Graph


def random_graph(n=12, extra=10, seed=0):
    rnd = random.Random(seed)
    g = Graph()
    for i in range(n):
        g.add_city(f"C{i}", rnd.random(), rnd.random())
    for i in range(1, n):
        g.add_road(f"C{i}", f"C{rnd.randrange(i)}", rnd.randint(1, 50))
    for _ in range(extra):
        a, b = rnd.sample(list(g.adj), 2)
        g.add_road(a, b, rnd.randint(1, 50))
    return g


def floyd(g):
    d = {a: {b: (0 if a == b else g.adj[a].get(b, float("inf"))) for b in g.adj} for a in g.adj}
    for k, i, j in itertools.product(g.adj, g.adj, g.adj):
        d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


class AlgoTests(unittest.TestCase):
    def test_dijkstra_matches_floyd_warshall(self):
        for seed in range(20):
            g = random_graph(seed=seed)
            ref = floyd(g)
            for a, b in itertools.permutations(g.adj, 2):
                r = dijkstra(g, a, b)
                self.assertAlmostEqual(r.distance, ref[a][b])
                self.assertAlmostEqual(path_cost(g, r.path), r.distance)

    def test_unreachable(self):
        g = Graph()
        g.add_city("A", 0, 0); g.add_city("B", 1, 1)
        self.assertIsNone(dijkstra(g, "A", "B"))

    def test_yen_sorted_unique_and_loop_free(self):
        g = random_graph(seed=3)
        routes = k_shortest(g, "C0", "C9", 5)
        costs = [r.distance for r in routes]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual(len({tuple(r.path) for r in routes}), len(routes))
        for r in routes:
            self.assertEqual(len(set(r.path)), len(r.path))
            self.assertAlmostEqual(path_cost(g, r.path), r.distance)

    def test_blocked_road_is_avoided(self):
        g = random_graph(seed=5)
        best = dijkstra(g, "C0", "C7")
        a, b = best.path[0], best.path[1]
        alt = dijkstra(g, "C0", "C7", blocked_edges=frozenset({frozenset((a, b))}))
        if alt:
            self.assertGreaterEqual(alt.distance, best.distance)
            self.assertNotIn((a, b), list(zip(alt.path, alt.path[1:])))


class CsvTests(unittest.TestCase):
    def _load(self, cities, roads):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "c.csv").write_text(cities)
            (Path(d) / "r.csv").write_text(roads)
            return Graph.from_csv(Path(d) / "c.csv", Path(d) / "r.csv")

    def test_valid(self):
        g = self._load("city,x,y\nA,0,0\nB,1,1\n", "city_a,city_b,km\nA,B,5\n")
        self.assertEqual(g.roads(), [("A", "B", 5.0)])

    def test_unknown_city_reports_line(self):
        with self.assertRaisesRegex(DataError, "line 2"):
            self._load("city,x,y\nA,0,0\n", "city_a,city_b,km\nA,Z,5\n")

    def test_bad_number_and_missing_column(self):
        with self.assertRaises(DataError):
            self._load("city,x,y\nA,zero,0\n", "city_a,city_b,km\n")
        with self.assertRaisesRegex(DataError, "missing"):
            self._load("city,x\nA,0\n", "city_a,city_b,km\n")


if __name__ == "__main__":
    unittest.main()
