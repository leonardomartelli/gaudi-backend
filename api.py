from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from flask_restful import Api, NotFound
from dto import ValidationResult
from models import Project
from services import OptimizationService
from flask_cors import cross_origin

app = Flask(__name__)
api = Api(app)

service = OptimizationService()


@app.route('/result', methods=['GET'])
@cross_origin()
def get_result():
    optimization_id = request.args.get('id', type=str)
    result = service.get_result(optimization_id)

    if result is None:
        raise NotFound

    serialized = result.serialize()

    return jsonify(serialized)


@app.route('/optimize', methods=['POST'])
@cross_origin()
def optimize():
    project = Project.from_json(request.json['project'])

    validations = []
    project.validate(validations)

    if len(validations) > 0:
        return invalid_project(validations)

    identifier = service.start_optimization(project)

    return jsonify(ValidationResult(identifier).serialize())


@app.route('/optimization', methods=['DELETE'])
@cross_origin()
def delete_optimization():
    optimization_id = request.args.get('id', type=str)

    service.end_optimization(optimization_id)

    return optimization_id


@app.errorhandler(BadRequest)
def invalid_project(validations):
    return jsonify(ValidationResult(validation_results=validations).serialize()), 400


if __name__ == '__main__':
    app.run()
