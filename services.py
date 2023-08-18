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
        result = self.optimizations[identifier].get_result()

        return result

    def end_optimization(self, identifier: str) -> None:
        thread = self.threads[identifier]

        thread.join()
