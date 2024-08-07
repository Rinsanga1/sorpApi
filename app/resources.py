import io
import base64
from flask import abort
from flask_cors import CORS
from flask_restx import Resource
from flask_restx import reqparse
from flask_jwt_extended import jwt_required, create_access_token
from flask_jwt_extended import current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest
from PIL import Image
from app.utils.models import db
from app.utils.predictfn import predictit, init_model
from app.utils.logfns import check_api_key, log_request, log_new_api
from app.utils.logfns import check_admin_login, get_api_request_stats
from app import api
from app import app


app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)


model = init_model()
db.init_app(app)


with app.app_context():
    db.create_all()


authorizations = {
    "adminJWT": {"type": "apiKey", "in": "header", "name": "Authorization"}
}


image_parser = reqparse.RequestParser()
image_parser.add_argument("image", type=FileStorage, location="files", required=True)

json_parser = reqparse.RequestParser()
json_parser.add_argument("b64", type=str, location="json", required=True)

uni_parser = reqparse.RequestParser()
uni_parser.add_argument("x-api-key", type=str, location="headers", required=True)

admin_parser = reqparse.RequestParser()
admin_parser.add_argument("user", type=str, location="json", required=True)
admin_parser.add_argument("pw", type=str, location="json", required=True)

addApi_parser = reqparse.RequestParser()
addApi_parser.add_argument("new_api_key", type=str, required=True)

admin = api.namespace("admin", authorizations=authorizations, description="for admins")


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


@api.route("/getstats")
class GetStat(Resource):
    @api.expect(uni_parser)
    def get(self):
        apiargs = uni_parser.parse_args().get('x-api-key')
        total, valid, invalid = get_api_request_stats(apiargs)

        response = {
            "total_requests": total,
            "valid_requests": valid,
            "invalid_requests": invalid,
        }

        return response


@admin.route("/login")
class admin_login(Resource):
    @admin.expect(admin_parser)
    def post(self):
        admin_user_args = admin_parser.parse_args().get("user")
        admin_pw_args = admin_parser.parse_args().get("pw")

        user_obj = check_admin_login(admin_user_args, admin_pw_args)
        if not user_obj:
            abort(400, "invalid username or email")

        return {"access token": create_access_token(user_obj)}


@admin.route("/apikey")
class add_apikey_admin(Resource):
    method_decorators = [jwt_required()]

    @admin.doc(security="adminJWT")
    @admin.expect(addApi_parser)
    def post(self):
        apiadd_args = addApi_parser.parse_args().get("new_api_key")
        key_maker = current_user.username

        log_new_api(apiadd_args, key_maker)
        return {"new api key added": apiadd_args, "by user": key_maker}


@admin.route("/getstats/<string:x_api_key>")
class GetStatAdmin(Resource):
    method_decorators = [jwt_required()]

    @admin.doc(security="adminJWT")
    def get(self, x_api_key):
        total, valid, invalid = get_api_request_stats(x_api_key)

        response = {
            "total_requests": total,
            "valid_requests": valid,
            "invalid_requests": invalid,
        }

        return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)
