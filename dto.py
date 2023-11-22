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

    def validate(self, max_width, max_height, validations: List[str]):
        if not self.dimensions.is_valid():
            validations.append(
                f'Região constante com dimensão inválida: Largura = {self.dimensions.width} Altura = {self.dimensions.height}')

        if not self.position.is_valid(max_width, max_height):
            validations.append(
                f'Região constante com posição inválida: X = {self.position.x} Y = {self.position.y}')

        if not (self.type == RegionType.MATERIAL or self.type == RegionType.VOID):
            validations.append('Região constante com tipo inválido')


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

    def validate(self, max_width, max_height, validations: List[str]):
        if self.load == 0:
            validations.append('Força com carga igual a zero')

        if not self.position.is_valid(max_width, max_height):
            validations.append(
                f'Força com posição inválida: X = {self.position.x} Y = {self.position.y}')

        if not (self.orientation == 0 or self.orientation == 1):
            validations.append('Força com orientação inválida')


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

        return Support(position, SupportType(type), dimensions)

    def validate(self, max_width, max_height, validations: List[str]):
        if not self.position.is_valid(max_width, max_height):
            validations.append(
                f'Suporte com posição inválida: X = {self.position.x} Y = {self.position.y}')

        if not (self.type == SupportType.MOBILE or self.type == SupportType.FIXED):
            validations.append('Suporte com tipo inválido')


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

    def validate(self, dimensions, validations: List[str]):
        self.validate_supports(dimensions, validations)
        self.validate_forces(dimensions, validations)
        self.validate_constant_regions(dimensions, validations)

    def validate_supports(self, dimensions: Dimensions, validations: List[str]):

        if len(self.supports) < 1:
            validations.append('O projeto deve ter no mínimo um suporte')
            return

        if all([support.type == SupportType.MOBILE for support in self.supports]) and \
                all([support.dimensions is None or not support.dimensions.is_valid() for support in self.supports]):
            validations.append(
                'O projeto deve ter no mínimo um suporte móvel com dimensões')
            return

        if len(self.supports) == 1:
            support = self.supports[0]
            dimensions_is_valid = support.dimensions is not None and support.dimensions.is_valid()

            if not dimensions_is_valid:
                validations.append(
                    'O projeto deve ter no mínimo um suporte fixo com dimensões, ou dois ou mais suportes fixos')
                return

        elif len(self.supports) == 2:
            support_one = self.supports[0]
            support_two = self.supports[1]

            if support_one.type != support_two.type:
                support_one_dimension_is_valid = support_one.dimensions is not None and support_one.dimensions.is_valid()
                support_two_dimension_is_valid = support_two.dimensions is not None and support_two.dimensions.is_valid()

                if not (support_one_dimension_is_valid or support_two_dimension_is_valid):
                    validations.append(
                        'O projeto não deve ter dois suportes de tipos diferentes, sem dimensões')
                    return

        for support in self.supports:
            support.validate(dimensions.width, dimensions.height, validations)

    def validate_forces(self, dimensions: Dimensions, validations: List[str]):

        if len(self.forces) < 1:
            validations.append('O projeto deve ter no mínimo uma força')
            return

        for force in self.forces:
            force.validate(dimensions.width, dimensions.height, validations)

    def validate_constant_regions(self, dimensions: Dimensions, validations: List[str]):
        for constant_region in self.constant_regions:
            constant_region.validate(
                dimensions.width, dimensions.height, validations)


class MaterialProperties:
    poisson: float
    young: float

    def __init__(self, poisson: float, young: float) -> None:
        self.poisson = poisson
        self.young = young

    def from_json(json: dict):
        return MaterialProperties(json['poisson'], json['young'])

    def validate(self, validations: List[str]):
        if self.poisson == 0:
            validations.append(
                'O coeficiente de Poisson do material deve ser diferente de 0')

        if self.young <= 0:
            validations.append(
                'O módulo de Young do material deve ser maior que 0')


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

    def validate(self, validations: List[str]):
        self.material_properties.validate(validations)

        if self.volume_fraction <= 0:
            validations.append(
                'A fração de volume deve ser maior que zero')

        if not self.dimensions.is_valid():
            validations.append(
                f'Domínio com dimensão inválida: Largura = {self.dimensions.width} Altura = {self.dimensions.height}')


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

    def validate(self, validations: List[str]):
        if self.penalization <= 1:
            validations.append(
                'A penalização deve ser maior que 1')

        if self.filter_radius <= 0:
            validations.append(
                'O raio de filtragem deve ser maior que 0')

        self.domain.validate(validations)

        self.boundary_conditions.validate(self.domain.dimensions, validations)


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


class ValidationResult():
    def __init__(self, optimization_id: str = None, validation_results: List[str] = None):
        self.optimization_id = optimization_id
        self.validation_results = validation_results

    def serialize(self) -> dict():
        data = dict()

        if self.optimization_id is not None:
            data['optimizationId'] = self.optimization_id

        if self.validation_results is not None:
            data['validationResults'] = self.validation_results

        return data
