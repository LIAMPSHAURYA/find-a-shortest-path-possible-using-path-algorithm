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
