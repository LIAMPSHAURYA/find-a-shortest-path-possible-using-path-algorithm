"""Route Finder - entry point.

    python main.py                          # open the GUI with data/cities.csv + data/roads.csv
    python main.py --cities a.csv --roads b.csv
    python main.py --from Delhi --to Kochi  # no GUI, print the answer
"""
import argparse
import sys
from pathlib import Path

from algorithms import k_shortest
from graph import DataError, Graph


def main() -> None:
    here = Path(__file__).parent / "data"
    ap = argparse.ArgumentParser(description="Dijkstra route finder")
    ap.add_argument("--cities", default=here / "cities.csv")
    ap.add_argument("--roads", default=here / "roads.csv")
    ap.add_argument("--from", dest="src", help="start city (CLI mode)")
    ap.add_argument("--to", dest="dst", help="destination city (CLI mode)")
    ap.add_argument("-k", type=int, default=1, help="number of routes (CLI mode)")
    args = ap.parse_args()

    try:
        g = Graph.from_csv(args.cities, args.roads)
    except (DataError, OSError) as e:
        sys.exit(f"Could not load data: {e}")

    if args.src or args.dst:
        if args.src not in g.adj or args.dst not in g.adj:
            sys.exit("Unknown city. Valid cities: " + ", ".join(sorted(g.adj)))
        routes = k_shortest(g, args.src, args.dst, args.k)
        if not routes:
            sys.exit("No route exists.")
        for i, r in enumerate(routes, 1):
            print(f"Route {i}: {r.distance:g} km  {' -> '.join(r.path)}")
        return

    from gui import App          # imported late so CLI mode works without tkinter
    App(g).mainloop()


if __name__ == "__main__":
    main()
