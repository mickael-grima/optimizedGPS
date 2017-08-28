# optimizedGPS

## About the code
This code presented here is related to the work "Dynamic Traffic Constrained Routing Problem - Complexity and Efficient Algorithms".
We can split it into three main parts:  
   - the *structure*: every class representing graphs, GPS graphs and drivers are implemented here  
   - the *data*: scripts to call the different api-s. A special file formatting is implemented as well.  
   - the *problems*: Everything about the algorithms (heuristics and models), simulators are implemented here  
   
The available problems are:  
   - *Heuristics*:  
             - RealGPS  
             - ShortestPathTrafficFree  
             - ShortestPathHeuristic
   - *Models*:  
             - TEGModel: Continuous Time Model based on time expanded graph
   - *Algorithms*:  
             - TEGColumnGenerationAlgorithm  
             - ConstantModelAlgorithm
  
**Important to note** is that the Gurobi solver is used. Any information about how to install it can be found here:  
http://www.gurobi.com/downloads/gurobi-optimizer  
And a documentation here:  
http://www.gurobi.com/documentation/7.5/

## Installation
Even without the Gurobi solver, the code can be used. However the models requiring this solver won't be run.
To install the project, download it and run:  
```bash
python setup.py install
```  
  
Python version = 2.7

To be sure that everything has been installed correctly, you can run the tests:  
```bash
cd optimizedGPS/
python tests/test_runner.py
```

## How to use the code
Here is an example on how to use the code.  
First we can build a simple structure.
```python
from optimizedGPS.structure import GPSGraph, DriversGraph, Driver
from optimizedGPS import labels
  
# Create a GPS Graph with 3 nodes and 3 edges. Each of these edges has a custom congestion function
graph = GPSGraph()
graph.add_edge("0", "1", **{labels.CONGESTION_FUNC: lambda x: x + 2})
graph.add_edge("0", "2", **{labels.CONGESTION_FUNC: lambda x: 2 * x + 2})
graph.add_edge("1", "2", **{labels.CONGESTION_FUNC: lambda x: x + 1})
  
drivers_graph = DriversGraph()
drivers_graph.add_driver(Driver("0", "2", 0))  # Driver from "0" to "2" starting at time 0
drivers_graph.add_driver(Driver("0", "2", 0))  # Driver from "0" to "2" starting at time 0
drivers_graph.add_driver(Driver("0", "2", 1))  # Driver from "0" to "2" starting at time 1
```
  
Some graphs are also available in the data section:
```python
from optimizedGPS.data import data_generator as gen
graph, drivers_graph = gen.generate_bad_heuristic_graphs()
```
  
Or generate grid graph with random number of drivers:
```python
from optimizedGPS.data import data_generator as gen
graph = gen.generate_grid_data(5, 5)
drivers_graph = gen.generate_random_drivers(graph, total_drivers=10)
```
  
Once a graph and a drivers graph are generated, one can build the drivers structure. With it a presolving is possible:
```python
from optimizedGPS.data import data_generator as gen
from optimizedGPS.structure import DriversStructure
graph, drivers_graph = gen.generate_bad_heuristic_graphs()
drivers_structure = DriversStructure(graph, drivers_graph, horizon=40)
drivers_structure.compute_optimal_safety_intervals()
  
driver = drivers_graph.get_all_drivers().next()  # take a random driver
edge = graph.edges()[0]
print drivers_structure.get_safety_interval(driver, edge)
```
This last line prints the time interval outside which the driver won't drive on edge. Such informations are used
for building the model. This presolving can be done using directly a solver.
This solver is also used to solve problems:
```python
from optimizedGPS.data import data_generator as gen
from optimizedGPS.problems import Solver, TEGModel, RealGPS
from optimizedGPS.problems.PreSolver import HorizonPresolver, SafetyIntervalsPresolver
  
graph, drivers_graph = gen.generate_bad_heuristic_graphs()
# If we specify the presolvers but not the horizon, it is important to add HorizonPresolver as well
solver = Solver(graph, drivers_graph, TEGModel, presolvers=[HorizonPresolver.__name__, SafetyIntervalsPresolver.__name__])
  
solver.solve()  # First presolve the problem, then solve it
  
for driver in drivers_graph.get_all_drivers():
    print "Driver's optimal path: %s\nDriver's driving time: %s\n" % (
        solver.get_optimal_driver_path(driver),
        solver.get_driver_driving_time(driver)
    )
  
# We can compare the result with a heuristic
heuristic = RealGPS(graph, drivers_graph)
heuristic.solve()
  
print "Heuristic's final value: %s\nModel's final value: %s" % (
    heuristic.value,
    solver.value
)
```
  
Finally, to compare two different algorithms on the same input or on different input,
it is possible to use the comparator:
```python
from optimizedGPS.data import data_generator as gen
from optimizedGPS.problems import Solver, TEGModel, RealGPS
from optimizedGPS.problems.PreSolver import HorizonPresolver, SafetyIntervalsPresolver
from optimizedGPS.problems import ResultsHandler
  
graphs = list()
graphs.append(gen.generate_bad_heuristic_graphs())
  
graph = gen.generate_grid_data(3, 2)
graph.set_global_congestion_function(lambda x: 3 * x + 2)
drivers_graph = gen.generate_random_drivers(graph, total_drivers=3)
graphs.append((graph, drivers_graph))
  
results_handler = ResultsHandler()
results_handler.append_graphs(*graphs)  # Add the different inputs
results_handler.append_algorithm(
    Solver, TEGModel,
    presolvers=[HorizonPresolver.__name__, SafetyIntervalsPresolver.__name__]
)
results_handler.append_algorithm(RealGPS)
  
results_handler.compare()
```
It prints the value, the running time, and the running status of every run algorithms.
