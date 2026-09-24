"""Dijkstra (with optional step trace) and Yen's k-shortest simple paths."""
from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field

from graph import Graph


@dataclass
class Route:
    distance: float
    path: list[str]
    settled: int = 0                 # cities finalised by Dijkstra
    ms: float = 0.0                  # running time
    steps: list[tuple] = field(default_factory=list)  # ("settle", u, None) / ("relax", u, v)


def edge_key(a: str, b: str) -> frozenset:
    return frozenset((a, b))


def path_cost(g: Graph, path: list[str]) -> float:
    return sum(g.adj[a][b] for a, b in zip(path, path[1:]))


def dijkstra(g: Graph, src: str, dst: str,
             blocked_edges: frozenset = frozenset(),
             blocked_nodes: frozenset = frozenset(),
             trace: bool = False) -> Route | None:
    """Shortest path with a binary heap: O((V + E) log V). Returns None if unreachable."""
    t0 = time.perf_counter()
    dist = {src: 0.0}
    prev: dict[str, str] = {}
    done: set[str] = set()
    heap = [(0.0, src)]
    steps: list[tuple] = []

    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue                       # stale heap entry
        done.add(u)
        if trace:
            steps.append(("settle", u, None))
        if u == dst:
            break
        for v, w in g.adj[u].items():
            if v in done or v in blocked_nodes or edge_key(u, v) in blocked_edges:
                continue
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
                if trace:
                    steps.append(("relax", u, v))

    if dst not in done:
        return None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    path.reverse()
    return Route(dist[dst], path, len(done), (time.perf_counter() - t0) * 1000, steps)


def k_shortest(g: Graph, src: str, dst: str, k: int = 3,
               blocked_edges: frozenset = frozenset()) -> list[Route]:
    """Yen's algorithm: the k shortest loop-free routes, best first."""
    first = dijkstra(g, src, dst, blocked_edges)
    if first is None:
        return []
    found = [first]
    candidates: list[tuple[float, list[str]]] = []
    seen = {tuple(first.path)}

    while len(found) < k:
        last = found[-1].path
        for i in range(len(last) - 1):
            spur, root = last[i], last[: i + 1]
            banned = set(blocked_edges)
            for r in found:                # forbid edges that earlier routes took after this root
                if r.path[: i + 1] == root and len(r.path) > i + 1:
                    banned.add(edge_key(r.path[i], r.path[i + 1]))
            spur_route = dijkstra(g, spur, dst, frozenset(banned), frozenset(root[:-1]))
            if spur_route:
                total = root[:-1] + spur_route.path
                if tuple(total) not in seen:
                    seen.add(tuple(total))
                    heapq.heappush(candidates, (path_cost(g, total), total))
        if not candidates:
            break
        cost, path = heapq.heappop(candidates)
        found.append(Route(cost, path))
    return found
