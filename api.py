from flask import Flask, request, jsonify
from flask_restful import Api
from models import Project
from services import OptimizationService

app = Flask(__name__)
api = Api(app)

service = OptimizationService()


@app.route('/result', methods=['GET'])
def get_result():
    optimization_id = request.args.get('id', type=str)
    result = service.get_result(optimization_id).serialize()

    return jsonify(result)


@app.route('/optimize', methods=['POST'])
def optimize():
    project = Project.from_json(request.json['project'])

    identifier = service.start_optimization(project)

    return identifier


@app.route('/optimization', methods=['DELETE'])
def get_result():
    optimization_id = request.args.get('id', type=str)

    service.end_optimization(optimization_id)

    return optimization_id


if __name__ == '__main__':
    app.run()
