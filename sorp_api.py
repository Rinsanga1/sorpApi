from flask import Flask, request, abort
from flask_restx import Api, Resource
from flask_restx import reqparse
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest
import base64
import io
from PIL import Image
from datetime import datetime
from sqlalchemy import func

from models import db, APIRequest, APIKey
from predictfn import predictit, init_model

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db.init_app(app)

api = Api(app, title='Clothing Prediction API',
          description='Takes clothing images and returns solid or pattern')
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)

model = init_model()

with app.app_context():
    db.create_all()


def check_api_key(api_key):
    api_key_record = APIKey.query.filter_by(api_key=api_key).first()
    if api_key_record is not None:
        log_request(api_key_record.id, True)
        return True
    else:
        log_request('Invalid', False)
        return False



def log_request(api_key, is_valid):
    log_entry = APIRequest(api_key=api_key,
                           is_valid=is_valid, timestamp=datetime.now())
    db.session.add(log_entry)
    db.session.commit()
    db.session.close()


image_parser = reqparse.RequestParser()
image_parser.add_argument('image',
                          type=FileStorage, location='files', required=True)

json_parser = reqparse.RequestParser()
json_parser.add_argument('b64',
                         type=str, location='json', required=True)

uni_parser = reqparse.RequestParser()
uni_parser.add_argument('x-api-key',
                        type=str, location='headers', required=True)


@api.route('/predict/json')
@api.expect(json_parser, validate=True)
class Predict(Resource):
    @api.expect(uni_parser, json_parser, validate=True)
    @api.doc(description="predict using base64")
    def post(self):
        api_key = uni_parser.parse_args().get("x-api-key")
        if not check_api_key(api_key):
            log_request(api_key, False)
            abort(401, 'Unauthorized Access: Invalid API Key')

        log_request(api_key, True)
        args = json_parser.parse_args()
        b64_code = args['b64']

        if b64_code.startswith('data:image/jpeg;base64,'):
            start = b64_code.index(',') + 1
            b64_code = b64_code[start:]

        try:
            decoded_data = base64.b64decode(b64_code, validate=True)
        except (ValueError, TypeError):
            raise BadRequest('Invalid Base64 string')

        try:
            image = Image.open(io.BytesIO(decoded_data))
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                image = image.convert("RGB")
        except (IOError, SyntaxError) as e:
            raise BadRequest('Decoded data is not a valid image')

        probability, predicted_class = predictit(image, model)
        probability = str(float(probability) * 100)

        return {
            'probability': probability,
            'predicted_class': predicted_class
        }, 200


@api.route('/predict/formData')
@api.expect(image_parser, validate=True)
class PredictFormFile(Resource):
    @api.expect(uni_parser, image_parser, validate=True)
    @api.doc(description="Takes a form file as input and returns predictions")
    def post(self):
        api_key = uni_parser.parse_args().get("x-api-key")
        if not check_api_key(api_key):
            abort(401, 'Unauthorized Access: Invalid API Key')

        img_file = image_parser.parse_args().get("image")
        # TODO : fix null file error

        if not img_file.content_type.startswith('image/'):
            abort(400, "File is not an image")

        try:
            image_bytes = img_file.read()
            image = Image.open(io.BytesIO(image_bytes))

            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                image = image.convert("RGB")

            probability, predicted_class = predictit(image, model)
            probability = str(float(probability) * 100)

            return {
                'probability': probability,
                'predicted_class': predicted_class
            }, 200

        except (IOError, SyntaxError) as e:
            raise BadRequest('Error processing the image file')


@api.route('/getStats')
class GetStats(Resource):
    def get(self):
        total_requests = db.session.query(func.count(APIRequest.id)).scalar()
        valid_requests = db.session.query(func.count(APIRequest.id)).filter_by(is_valid=True).scalar()
        invalid_requests = db.session.query(func.count(APIRequest.id)).filter_by(is_valid=False).scalar()

        all_requests = db.session.query(APIRequest).all()

        response = {
            'total_requests': total_requests,
            'valid_requests': valid_requests,
            'invalid_requests': invalid_requests,
            'all_requests': [
                {
                    'id': request.id,
                    'api_key': request.api_key,
                    'is_valid': request.is_valid,
                    'timestamp': request.timestamp.isoformat()
                } for request in all_requests
            ]
        }

        return response


if __name__ == '__main__':
    app.run(port=5000, debug=True)
