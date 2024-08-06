from flask import abort
from flask_restx import Resource
from flask_restx import reqparse
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest
import base64
import io
from PIL import Image
from sqlalchemy import func

from app.utils.models import db, APIRequest
from app.utils.predictfn import predictit, init_model
from app.utils.logfns import check_api_key, log_request
from app import api
from app import app

model = init_model()
db.init_app(app)
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)
with app.app_context():
    db.create_all()


@app.before_request
def before_request():
    db.session.remove()


@app.teardown_request
def teardown_request(exception):
    db.session.remove()


image_parser = reqparse.RequestParser()
json_parser = reqparse.RequestParser()
uni_parser = reqparse.RequestParser()
uni_parser.add_argument("x-api-key", type=str,
                        location="headers", required=True)


@api.route("/predict/json")
@api.expect(json_parser, validate=True)
class Predict(Resource):
    @api.expect(uni_parser, json_parser, validate=True)
    @api.doc(description="predict using base64")
    def post(self):
        api_key = uni_parser.parse_args().get("x-api-key")
        if not check_api_key(api_key):
            abort(401, "Unauthorized Access: Invalid API Key")

        log_request(api_key, True)
        args = json_parser.parse_args()
        b64_code = args["b64"]

        if b64_code.startswith("data:image/jpeg;base64,"):
            start = b64_code.index(",") + 1
            b64_code = b64_code[start:]

        try:
            decoded_data = base64.b64decode(b64_code, validate=True)
        except (ValueError, TypeError):
            raise BadRequest("Invalid Base64 string")

        try:
            image = Image.open(io.BytesIO(decoded_data))
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGB")
        except (IOError, SyntaxError) as e:
            raise BadRequest("Decoded data is not a valid image")

        probability, predicted_class = predictit(image, model)
        probability = str(float(probability) * 100)

        return {"probability": probability, "predicted_class": predicted_class}, 200


@api.route("/predict/formData")
@api.expect(image_parser, validate=True)
class PredictFormFile(Resource):
    @api.expect(uni_parser, image_parser, validate=True)
    @api.doc(description="Takes a form file as input and returns predictions")
    def post(self):
        api_key = uni_parser.parse_args().get("x-api-key")
        if not check_api_key(api_key):
            abort(401, "Unauthorized Access: Invalid API Key")

        img_file = image_parser.parse_args().get("image")

        try:
            image_bytes = img_file.read()
            image = Image.open(io.BytesIO(image_bytes))

            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGB")

            probability, predicted_class = predictit(image, model)
            probability = str(float(probability) * 100)

            return {"probability": probability, "predicted_class": predicted_class}, 200

        except (IOError, SyntaxError) as e:
            raise BadRequest("Error processing the image file")


@api.route("/getStats")
class GetStats(Resource):
    def get(self):
        total_requests = db.session.query(func.count(APIRequest.id)).scalar()
        valid_requests = (
            db.session.query(func.count(APIRequest.id))
            .filter_by(is_valid=True)
            .scalar()
        )
        invalid_requests = (
            db.session.query(func.count(APIRequest.id))
            .filter_by(is_valid=False)
            .scalar()
        )

        all_requests = db.session.query(APIRequest).all()

        response = {
            "total_requests": total_requests,
            "valid_requests": valid_requests,
            "invalid_requests": invalid_requests,
            "all_requests": [
                {
                    "id": request.id,
                    "api_key_id": request.api_key,
                    "is_valid": request.is_valid,
                    "timestamp": request.timestamp.isoformat(),
                }
                for request in all_requests
            ],
        }

        return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)
