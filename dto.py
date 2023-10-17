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

    def is_valid(self):
        return self.width >= 1 and self.height >= 1


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

    def is_valid(self, max_width: int, max_height: int):
        return self.x >= 0 and self.x <= max_width and self.y >= 0 and self. y <= max_height


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

    def is_valid(self, max_width, max_height):
        return self.dimensions.is_valid() and self.position.is_valid(max_width, max_height) and (self.type == 0 or self.type == 1)


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

    def is_valid(self, max_width, max_height):
        return self.load != 0 and self.position.is_valid(max_width, max_height) and (self.orientation == 0 or self.orientation == 1)


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

    def is_valid(self, max_width, max_height):
        return self.position.is_valid(max_width, max_height) and (self.type == 0 or self.type == 1)


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

    def is_valid(self, dimensions):
        return self.supports_are_valid(dimensions) and self.forces_are_valid(dimensions) and self.constant_regions_are_valid(dimensions)

    def supports_are_valid(self, dimensions: Dimensions):

        if len(self.supports) < 1:
            return False

        for support in self.supports:
            dimensions_is_valid = support.dimensions is not None and support.dimensions.is_valid()

            if ((not dimensions_is_valid or support.type == 0) and len(self.supports) == 1) or not support.is_valid(dimensions.width, dimensions.height):
                return False

        return True

    def forces_are_valid(self, dimensions: Dimensions):

        if len(self.forces) < 1:
            return False

        for force in self.forces:
            if not force.is_valid(dimensions.width, dimensions.height):
                return False

        return True

    def constant_regions_are_valid(self, dimensions: Dimensions):
        for constant_region in self.constant_regions:

            if not constant_region.is_valid(dimensions.width, dimensions.height):
                return False

        return True


class MaterialProperties:
    elasticity: float
    density: float

    def __init__(self, elasticity: float, density: float) -> None:
        self.elasticity = elasticity
        self.density = density

    def from_json(json: dict):
        return MaterialProperties(json['elasticity'], json['density'])

    def is_valid(self):
        return self.elasticity < 1 and self.density <= 1


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

    def is_valid(self):
        return self.material_properties.is_valid() and self.volume_fraction > 0 and self.dimensions.is_valid()


class Project:
    domain: Domain
    boundary_conditions: BoundaryConditions
    penalization: float
    filter_radius: float

    def __init__(self, domain: Domain, boundary_conditions: BoundaryConditions, penalization: float = 3.0, filter_radius: float = 1.4) -> None:
        self.domain = domain
        self.boundary_conditions = boundary_conditions
        self.penalization = penalization
        self.filter_radius = filter_radius

    def from_json(json: dict):
        domain = Domain.from_json(json['domain'])
        bc = BoundaryConditions.from_json(json['boundaryConditions'])
        penalization = float(json['penalization'])
        filter_radius = float(json['filterRadius'])

        return Project(domain, bc, penalization, filter_radius)

    def is_valid(self):
        return self.penalization > 1 and self.filter_radius > 1 and self.domain.is_valid() and self.boundary_conditions.is_valid(self.domain.dimensions)


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
