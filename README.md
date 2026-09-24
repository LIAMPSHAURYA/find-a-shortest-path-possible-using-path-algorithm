# Route Finder (Python, Dijkstra)

Desktop app that loads cities and roads from CSV files, draws the map, and finds the shortest route with Dijkstra's algorithm.

## Run
Needs Python 3.9+ (tkinter ships with the Windows/macOS installers; on Ubuntu: `sudo apt install python3-tk`). No other packages.

    python main.py                                   # GUI with data/cities.csv + data/roads.csv
    python main.py --cities my_c.csv --roads my_r.csv
    python main.py --from Delhi --to Kochi -k 3      # no GUI, prints 3 best routes
    python -m unittest tests -v                      # run the tests

## Using the GUI
- Pick From/To in the dropdowns (type to search) or click two cities on the map.
- **Find shortest route** shows up to 5 routes (Yen's k-shortest paths), best in bold blue.
- **Animate** replays Dijkstra: orange cities are settled, orange lines are relaxed edges.
- **Right-click a road** to close it (red dashed); routes re-calculate around it.
- Mouse wheel zooms, drag pans, **Reset view** re-fits the map.
- **Load CSV files...** opens any data set in the same format.

## CSV format
    cities.csv:  city,x,y          (x, y only place the city on the map)
    roads.csv:   city_a,city_b,km  (roads are two-way)
Errors (unknown city, bad number, missing column) are reported with the file name and line number.

## Files
| File | Purpose |
|---|---|
| graph.py | Graph class, CSV loading and validation |
| algorithms.py | `dijkstra` (binary heap, optional step trace), `k_shortest` (Yen) |
| gui.py | Tkinter map, animation, closures, zoom/pan |
| main.py | Entry point (GUI or CLI) |
| tests.py | Dijkstra checked against Floyd-Warshall on random graphs, Yen and CSV tests |

## How it works
Dijkstra keeps a min-heap of (distance, city). It pops the closest unsettled city, then tries to improve each neighbour ("relax"). Stale heap entries are skipped, and it stops as soon as the destination is settled. Complexity is O((V + E) log V).
Yen's algorithm finds the next-best routes by re-running Dijkstra with earlier route edges and root-path cities blocked.



___________________________________________________________________________________________________________________________________________________________________




Here are upgrades in four areas, roughly in order of impact. Doing a few well beats doing all of them.

1. Better algorithms (shows deep DSA knowledge)

A* search uses a heuristic (straight-line distance) to explore far fewer cities than Dijkstra. It needs real coordinates and haversine distance; the random test coordinates are not accurate enough to keep it correct.
Bidirectional Dijkstra searches from both ends and meets in the middle, which is usually 2-4x faster.
ALT or Contraction Hierarchies are the preprocessing tricks real map engines use to answer queries in milliseconds on huge graphs.
Multi-stop trips ("Delhi → Jaipur → Agra → Mumbai") turn this into the travelling salesman problem. Use bitmask DP for up to about 15 stops, or nearest-neighbour plus 2-opt for more.
Multi-criteria routing covers distance, time, and toll together, and produces a Pareto set of best trade-offs.
Network analysis: betweenness centrality shows which city matters most, plus connectivity checks and a minimum spanning tree.
One-way roads and time-dependent traffic need a directed graph and weights that change by hour.

2. Real data

Pull real road networks from OpenStreetMap (the osmnx library) and run on 100,000+ nodes instead of 50.
Store data in SQLite instead of CSV.
Add a benchmark mode that compares Dijkstra, A* and bidirectional on nodes explored and milliseconds, with charts. This is what makes the algorithm work look convincing.

3. Better interface

Replace the drawn map with a real map: a web app with Flask or FastAPI serving a JSON API and a Leaflet.js front end. This also lets you deploy it online with a link to share.
Add address search, drag-to-add waypoints, an elevation or distance profile, and export to GPX or PDF.
An option is to use your C++ Dijkstra as the fast engine behind the Python or web layer. That is a strong "two languages, one system" story.

4. Engineering quality (what separates a project from a portfolio piece)

pytest with coverage, type hints checked with mypy, and GitHub Actions running the tests on every commit
A Dockerfile so anyone can run it with one command
Logging, error handling, and a clear README with screenshots or a GIF
A short write-up of the results, such as "A* explored 82% fewer nodes than Dijkstra on 100k nodes"

Suggested path for a standout project

Add A* and bidirectional Dijkstra, then a benchmark screen comparing all three.
Load a real city network from OpenStreetMap.
Put it behind a Flask API with a Leaflet map and deploy it.
Add tests, CI, and a Docker setup.
