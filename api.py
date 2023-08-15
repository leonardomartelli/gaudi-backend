from flask import Flask, request, jsonify
from flask_restful import Api
from models import Project, Optimization
import threading

app = Flask(__name__)
api = Api(app)

optimizations = {}


@app.route('/result', methods=['GET'])
def get_result():
    optimization_id = request.args.get('id', type=str)
    result = optimizations[optimization_id].get_result().serialize()

    return jsonify(result)


@app.route('/optimize', methods=['POST'])
def optimize():
    project = Project.from_json(request.json['project'])
    optimization = Optimization(project)
    optimizations[optimization.identifier] = optimization

    thread = threading.Thread(target=optimization.optimize)
    thread.start()

    return optimization.identifier


if __name__ == '__main__':
    app.run()
