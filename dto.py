from typing import Optional, List
from enum import Enum
import numpy


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
    position: Position
    type: SupportType
    dimensions: Optional[Dimensions]

    def __init__(self, position: Position, type: SupportType, dimensions: Optional[Dimensions] = None) -> None:

        self.position = position
        self.type = type
        self.dimensions = dimensions

    def from_json(json: dict):
        position = Position.from_json(json['position'])

        if 'dimensions' in json:
            dimensions = Dimensions.from_json(json['dimensions'])
        else:
            dimensions = None

        type = json['type']

        return Support(position, type, dimensions)


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

        if 'constantRegions' in json:
            for raw_constant_region in json['constantRegions']:
                constant_regions.append(
                    ConstantRegion.from_json(raw_constant_region))

        return BoundaryConditions(supports, forces, constant_regions)


class MaterialProperties:
    elasticity: float
    density: float

    def __init__(self, elasticity: float, density: float) -> None:
        self.elasticity = elasticity
        self.density = density

    def from_json(json: dict):
        return MaterialProperties(json['elasticity'], json['density'])


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


class Result():
    def __init__(self, x: numpy.ndarray, volume: float, obj: float, finished: bool = False):
        self.densities = x.tolist()
        self.volume = volume
        self.obj = obj
        self.finished = finished

    def serialize(self) -> dict():
        data = dict()
        if self.finished:
            data['finished'] = self.finished

        data['densities'] = [round(d, 5) for d in self.densities]
        data['volume'] = self.volume
        data['objective'] = self.obj

        return data
