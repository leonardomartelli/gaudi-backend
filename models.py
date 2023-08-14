from typing import Optional, List
from enum import Enum

import numpy
from topopt.boundary_conditions import BoundaryConditions as bc
from topopt.filters import Filter
from topopt.guis import GUI
from topopt.problems import Problem
from topopt.utils import xy_to_id
from topopt.solvers import TopOptSolver
import numpy as np
from queue import SimpleQueue


class RegionType(Enum):
    VOID = 0
    MATERIAL = 1


class SupportType(Enum):
    FIXED = 1
    MOBILE = 0


class Dimensions:
    width: int
    height: int

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def from_json(json: dict):
        width = json['width']
        height = json['height']

        return Dimensions(width, height)


class Position:
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def from_json(json: dict):
        x = json['x']
        y = json['y']

        return Position(x, y)


class ConstantRegion:
    position: Position
    dimensions: Dimensions
    type: RegionType

    def __init__(self, position: Position, dimensions: Dimensions, type: RegionType) -> None:
        self.position = position
        self.dimensions = dimensions
        self.type = type

    def from_json(json: dict):
        position = Position.from_json(json['position'])
        dimensions = Dimensions.from_json(json['dimensions'])
        type = RegionType(json['type'])

        return ConstantRegion(position, dimensions, type)


class Force:
    load: float
    orientation: int
    position: Position
    size: Optional[int]

    def __init__(self, load: float, orientation: int, position: Position, size: Optional[int] = 0) -> None:
        self.load = load
        self.orientation = orientation
        self.position = position
        self.size = size

    def from_json(json: dict):
        orientation = json['orientation']
        position = Position.from_json(json['position'])

        if 'size' in json:
            size = json['size']
        else:
            size = 0

        load = json['load']

        return Force(load, orientation, position, size)


class Support:
    orientation: int
    position: Position
    type: SupportType
    size: Optional[int]

    def __init__(self, orientation: int, position: Position, type: SupportType, size: Optional[int] = 0) -> None:
        self.orientation = orientation
        self.position = position
        self.type = type
        self.size = size

    def from_json(json: dict):
        orientation = json['orientation']
        position = Position.from_json(json['position'])

        if 'size' in json:
            size = json['size']
        else:
            size = 0

        type = json['type']

        return Support(orientation, position, type, size)


class BoundaryConditions:
    supports: List[Support]
    forces: List[Force]
    constant_regions: List[ConstantRegion]

    def __init__(self, supports: List[Support], forces: List[Force], constant_regions: List[ConstantRegion]) -> None:
        self.supports = supports
        self.forces = forces
        self.constant_regions = constant_regions

    def from_json(json: dict):
        supports = []
        for raw_support in json['supports']:
            supports.append(Support.from_json(raw_support))

        forces = []
        for raw_force in json['forces']:
            forces.append(Force.from_json(raw_force))

        constant_regions = []
        for raw_constant_region in json['constantRegions']:
            constant_regions.append(
                ConstantRegion.from_json(raw_constant_region))

        return BoundaryConditions(supports, forces, constant_regions)


class MaterialProperties:
    elasticity: float
    density: float
    flow: float

    def __init__(self, elasticity: float, density: float, flow: float) -> None:
        self.elasticity = elasticity
        self.density = density
        self.flow = flow

    def from_json(json: dict):
        return MaterialProperties(json['elasticity'], json['density'], json['flow'])


class Domain:
    material_properties: MaterialProperties
    dimensions: Dimensions
    volume_fraction: float

    def __init__(self, material_properties: MaterialProperties, dimensions: Dimensions, volume_fraction: float) -> None:
        self.material_properties = material_properties
        self.dimensions = dimensions
        self.volume_fraction = volume_fraction

    def from_json(json: dict):
        mp = MaterialProperties.from_json(json['materialProperties'])
        dimensions = Dimensions.from_json(json['dimensions'])
        vc = json['volumeFraction']

        return Domain(mp, dimensions, vc)


class Project:
    domain: Domain
    boundary_conditions: BoundaryConditions
    penalization: float
    filter_index: float

    def __init__(self, domain: Domain, boundary_conditions: BoundaryConditions, penalization: float = 3.0, filter_index: float = 1.4) -> None:
        self.domain = domain
        self.boundary_conditions = boundary_conditions
        self.penalization = penalization
        self.filter_index = filter_index

    def from_json(json: dict):
        domain = Domain.from_json(json['domain'])
        bc = BoundaryConditions.from_json(json['boundaryConditions'])
        penalization = float(json['penalization'])
        filter_index = float(json['filterIndex'])

        return Project(domain, bc, penalization, filter_index)


class CustomBoundaryConditions(bc):
    def __init__(self, nelx, nely, boundary_conditions: BoundaryConditions):
        self.boundary_conditions = boundary_conditions
        super().__init__(nelx, nely)

    @property
    def fixed_nodes(self):
        fixed = None

        for support in self.boundary_conditions.supports:
            if support.size > 0:
                if support.orientation == 0:
                    func = np.vectorize(lambda x: xy_to_id(
                        x, support.position.y, self.nelx, self.nely))
                    begin = support.position.x
                else:
                    func = np.vectorize(lambda y: xy_to_id(
                        support.position.x, y, self.nelx, self.nely))
                    begin = support.position.y

                ids = 2 * func(range(begin, begin + support.size))

                supp_points = np.union1d(ids, ids + 1)
            else:
                index = 2 * xy_to_id(support.position.x,
                                     support.position.y, self.nelx, self.nely)

                supp_points = np.arange(index, index+1 + support.type)

            if fixed is not None:
                fixed = np.union1d(fixed, supp_points)
            else:
                fixed = supp_points

        return fixed

    @property
    def forces(self):

        forces_length = len(self.boundary_conditions.forces)

        f = np.zeros((self.ndof, forces_length))

        for i in range(forces_length):
            force = self.boundary_conditions.forces[i]

            if force.size > 0:
                if force.orientation == 0:
                    func = np.vectorize(lambda x: xy_to_id(
                        x, force.position.y, self.nelx, self.nely))
                    begin = force.position.x
                else:
                    func = np.vectorize(lambda y: xy_to_id(
                        force.position.x, y, self.nelx, self.nely))
                    begin = force.position.y
                ids = func(range(begin, begin + force.size))
                f[ids, i] = force.load

            else:
                index = 2 * xy_to_id(force.position.x,
                                     force.position.y, self.nelx, self.nely) + force.orientation
                ids = np.arange(index, index + 1)

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

            X_t, Y_t = np.mgrid[region.position.x: region.position.x + region.dimensions.width + 1,
                                region.position.y: region.position.y + region.dimensions.height + 1]

            if X is None:
                X, Y = X_t.ravel(), Y_t.ravel()
            else:
                X = np.append(X.ravel(), X_t.ravel())
                Y = np.append(Y.ravel(), Y_t.ravel())

        pairs = np.vstack([X.ravel(), Y.ravel()]).T

        to_id = np.vectorize(lambda xy: xy_to_id(
            *xy, nelx=self.nelx - 1, nely=self.nely - 1), signature="(m)->()")

        return to_id(pairs)


class Result():
    def __init__(self, x: numpy.ndarray, volume: float, obj: float, finished: bool = False):
        self.densities = x.tolist()
        self.volume
        self.obj = obj
        self.finished = finished


class GaudiSolver(TopOptSolver):
    def __init__(self, problem: Problem, volfrac: float, filter: Filter, gui: GUI, maxeval=2000, ftol_rel=0.001):
        super().__init__(problem, volfrac, filter, gui, maxeval, ftol_rel)
        self.results = SimpleQueue()

    def objective_function(self, x: np.ndarray, dobj: np.ndarray) -> float:

        obj = super().objective_function(x, dobj)

        result = Result(x, x.sum(), obj)

        self.results.put(result)

        return obj

    def get_result(self):
        return self.results.get()

    def optimize(self, x: np.ndarray) -> np.ndarray:
        final = super().optimize(x)

        self.results.put(Result(final, final.sum(), ))

        return final
