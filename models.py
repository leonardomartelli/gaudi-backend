

import numpy
from topopt.boundary_conditions import BoundaryConditions as bc
from topopt.filters import Filter
from topopt.guis import GUI
from topopt.problems import Problem, ComplianceProblem
from topopt.utils import xy_to_id
from topopt.solvers import TopOptSolver
from topopt.filters import DensityBasedFilter
from dto import *

from queue import SimpleQueue
import time


class CustomBoundaryConditions(bc):
    def __init__(self, nelx, nely, boundary_conditions: BoundaryConditions):
        self.boundary_conditions = boundary_conditions
        super().__init__(nelx, nely)

    @property
    def fixed_nodes(self):
        fixed = None

        for support in self.boundary_conditions.supports:
            # if support.dimensions is not None:

            # add support for multidimensional supports
            # if support.orientation == 0:
            #     func = numpy.vectorize(lambda x: xy_to_id(
            #         x, support.position.y, self.nelx, self.nely))
            #     begin = support.position.x
            # else:
            #     func = numpy.vectorize(lambda y: xy_to_id(
            #         support.position.x, y, self.nelx, self.nely))
            #     begin = support.position.y

            # ids = 2 * func(range(begin, begin + support.d))

            # supp_points = numpy.union1d(ids, ids + 1)
            # else:
            index = 2 * xy_to_id(support.position.x,
                                 support.position.y, self.nelx, self.nely)

            supp_points = numpy.arange(index, index+1 + support.type)

            if fixed is not None:
                fixed = numpy.union1d(fixed, supp_points)
            else:
                fixed = supp_points

        return fixed

    @property
    def forces(self):

        forces_length = len(self.boundary_conditions.forces)

        f = numpy.zeros((self.ndof, forces_length))

        for i in range(forces_length):
            force = self.boundary_conditions.forces[i]

            if force.size > 0:
                if force.orientation == 0:
                    func = numpy.vectorize(lambda x: xy_to_id(
                        x, force.position.y, self.nelx, self.nely))
                    begin = force.position.x
                else:
                    func = numpy.vectorize(lambda y: xy_to_id(
                        force.position.x, y, self.nelx, self.nely))
                    begin = force.position.y
                ids = func(range(begin, begin + force.size))
                f[ids, i] = force.load

            else:
                index = 2 * xy_to_id(force.position.x,
                                     force.position.y, self.nelx, self.nely) + force.orientation
                ids = numpy.arange(index, index + 1)

            f[ids, i] = force.load

        return f

    @property
    def passive_elements(self):
        return self.get_constant_region(RegionType.VOID)

    @property
    def active_elements(self):
        return self.get_constant_region(RegionType.MATERIAL)

    def get_constant_region(self, region_type: RegionType):

        X, Y = None, None

        for region in self.boundary_conditions.constant_regions:
            if region.type != region_type:
                continue

            X_t, Y_t = numpy.mgrid[region.position.x: region.position.x + region.dimensions.width,
                                   region.position.y: region.position.y + region.dimensions.height]

            if X is None:
                X, Y = X_t.ravel(), Y_t.ravel()
            else:
                X = numpy.append(X.ravel(), X_t.ravel())
                Y = numpy.append(Y.ravel(), Y_t.ravel())

        if X is None:
            return numpy.array([])

        pairs = numpy.vstack([X.ravel(), Y.ravel()]).T

        to_id = numpy.vectorize(lambda xy: xy_to_id(
            *xy, nelx=self.nelx - 1, nely=self.nely - 1), signature="(m)->()")

        return to_id(pairs)


class GaudiSolver(TopOptSolver):
    def __init__(self, problem: Problem, volfrac: float, filter: Filter, gui: GUI, maxeval=2000, ftol_rel=0.001):
        super().__init__(problem, volfrac, filter, gui, maxeval, ftol_rel)
        self.results = SimpleQueue()
        self.last_result: Result = None

    def objective_function(self, x: numpy.ndarray, dobj: numpy.ndarray) -> float:
        obj = super().objective_function(x, dobj)

        result = Result(x, x.sum(), obj)

        self.results.put(result)
        self.last_result = result

        return obj

    def get_result(self) -> Result:
        result = self.results.get()

        if self.results.empty():
            self.results.put(result)

        return result

    def optimize(self, x: numpy.ndarray) -> numpy.ndarray:
        final = super().optimize(x)

        self.results.put(
            Result(final, self.last_result.volume, self.last_result.obj, True))

        return final


class GaudiMockedGUI(GUI):
    def update(self, xPhys, title=None):
        pass

    def __init__(self, problem, title=""):
        pass


class Optimization:
    def __init__(self, project: Project):
        self.project = project

        self.problem = ComplianceProblem(CustomBoundaryConditions(self.project.domain.dimensions.width,  self.project.domain.dimensions.height, self.project.boundary_conditions),
                                         self.project.penalization,
                                         self.project.domain.material_properties.density,
                                         self.project.domain.material_properties.elasticity)

        self.gui = GaudiMockedGUI(self.problem, None)

        self.topopt_filter = DensityBasedFilter(
            self.project.domain.dimensions.width, self.project.domain.dimensions.height, project.filter_index)

        self.solver = GaudiSolver(
            self.problem, self.project.domain.volume_fraction, self.topopt_filter, self.gui)

        self.identifier = hex(int(time.time() * 1000))[2:]

    def get_result(self) -> Result:
        return self.solver.get_result()

    def optimize(self):
        x = numpy.ones(self.project.domain.dimensions.width *
                       self.project.domain.dimensions.height, dtype=float)

        self.solver.optimize(x)
