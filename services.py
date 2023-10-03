from models import Optimization
from threading import Thread
from dto import Project, Result


class OptimizationService():
    optimizations: dict[str, Optimization]
    threads: dict[str, Thread]

    def __init__(self) -> None:
        self.optimizations = {}
        self.threads = {}

    def start_optimization(self, project: Project) -> str:
        optimization = Optimization(project)

        self.optimizations[optimization.identifier] = optimization

        thread = Thread(target=optimization.optimize)
        thread.start()

        self.threads[optimization.identifier] = thread

        return optimization.identifier

    def get_result(self, identifier: str) -> Result:

        if identifier in self.optimizations:
            result = self.optimizations[identifier].get_result()
        else:
            result = None

        return result

    def end_optimization(self, identifier: str) -> None:
        if identifier in self.optimizations:
            self.optimizations.pop(identifier)

            thread = self.threads[identifier]

            thread.join()
