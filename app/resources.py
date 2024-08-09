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
from app.db_model.models import db
from app.utils.predictfn import predictit, init_model
from app.utils.logfns import (
    check_api_key,
    delete_api_key,
    log_request,
    log_new_api,
    check_api_dupe,
)
from app.utils.logfns import update_api_key, check_id_exist
from app.utils.logfns import check_admin_login, get_api_key_list, get_api_request_stats
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

delete_parser = reqparse.RequestParser()
delete_parser.add_argument("delete", type=int, required=True)

update_parser = reqparse.RequestParser()
update_parser.add_argument("update", type=int, required=True)
update_parser.add_argument("update_valoo", type=str, required=True)

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


""" Display API Key Route """


@api.route("/apikeys")
class GetStat(Resource):
    @api.expect(uni_parser)
    def get(self):
        apiargs = uni_parser.parse_args().get("x-api-key")
        total, valid, invalid = get_api_request_stats(apiargs)

        response = {
            "total_requests": total,
            "valid_requests": valid,
            "invalid_requests": invalid,
        }

        return response


""" Login API Key Route """


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


""" Get API Key Route """


@admin.route("/apikeys", defaults={"id": None})
@admin.route("/apikeys/<int:id>")
@api.param("id", "The API key ID", type="integer", required=False)
class GetStatAdmin(Resource):
    method_decorators = [jwt_required()]

    @admin.doc(security="adminJWT")
    def get(self, id):
        if id is None:
            api_key_list = get_api_key_list()
            return api_key_list, 200

        if check_id_exist(id) is not None:
            api_key_list = get_api_key_list(id)
            return api_key_list, 200
        return "Id doesnt Exist", 404


""" Admin API Route """


@admin.route("/apikeys")
class DeleteKey(Resource):
    method_decorators = [jwt_required()]

    @admin.doc(security="adminJWT")
    @admin.expect(addApi_parser)
    def post(self):  # Append New Key
        apiadd_args = addApi_parser.parse_args().get("new_api_key")
        key_maker = current_user.username
        duplicate_check = check_api_dupe(apiadd_args)
        if duplicate_check is not None:
            abort(400, "API key already exists")
        log_new_api(apiadd_args, key_maker)
        return {"new api key added": apiadd_args}

    @admin.doc(security="adminJWT")
    def get(self):
        api_key_list = get_api_key_list()
        return api_key_list, 200

    @admin.doc(security="adminJWT")
    @api.expect(delete_parser)
    def delete(self):  # Delete Existing Key
        api_args = delete_parser.parse_args().get("delete")
        api_exist_check = check_id_exist(api_args)

        if api_exist_check is not None:
            delete_api_key(api_args)
            return {"deleted": api_args}
        return {"deleted": "no such api key existed"}

    @admin.doc(security="adminJWT")
    @api.expect(update_parser)
    def put(self):  # Update Existing Key
        api_args = update_parser.parse_args().get("update")
        update_args = update_parser.parse_args().get("update_valoo")
        api_exist_check = check_id_exist(api_args)

        if api_exist_check is not None:
            update_api_key(api_args, update_args)
            return {"updated": api_args}
        return {"updated": "no such api key existed"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
