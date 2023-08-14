import json
from models import Project
from models import CustomBoundaryConditions
from topopt.problems import ComplianceProblem
from topopt.guis import GUI
from topopt.filters import DensityBasedFilter
from topopt.solvers import TopOptSolver
import numpy


class Optimization:
    def __init__(self, project: Project):
        self.project = project

        self.problem = ComplianceProblem(CustomBoundaryConditions(self.project.domain.dimensions.width,  self.project.domain.dimensions.height, self.project.boundary_conditions),
                                         self.project.penalization,
                                         self.project.domain.material_properties.density,
                                         self.project.domain.material_properties.elasticity)

        gui = GUI(self.problem, "Topology Optimization Example")
        topopt_filter = DensityBasedFilter(
            self.project.domain.dimensions.width, self.project.domain.dimensions.height, project.filter_index)
        solver = TopOptSolver(
            self.problem, self.project.domain.volume_fraction, topopt_filter, gui)

        x = self.project.domain.volume_fraction * \
            numpy.ones(self.project.domain.dimensions.width *
                       self.project.domain.dimensions.height, dtype=float)

        x_opt = solver.optimize(x)

    def get_result(self):
        self.queue


file = json.load(open("project-example-beam.json", 'r'))


project = Project.from_json(file)

Optimization(project)

tttt = input('end')
