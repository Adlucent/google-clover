# This file uses the following encoding: utf-8

from google.api_core.exceptions import InvalidArgument
from google.cloud import aiplatform_v1
from google.oauth2 import service_account
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

from .models import TypeOfModel


def predict(request, config, clvmodel, future=False):
    """
    This function will call the external API in Google Cloud to Predict based on the data passed
    """
    prediction = {'message': ''}
    type_of_model = TypeOfModel(clvmodel.type)

    # Test to ensure that all the data fields in the model are part of the training data set and that they are
    # all present in the request
    model = CLVModelFeatures(clvmodel.data_fields)
    data_set = CLVModelFeatures(config.data_set.data_fields)
    for feature in model.features:
        if feature not in data_set.features:
            prediction['message'] += f'{feature} not present in training data set\n'
            if feature not in request.data.keys() and model.data_mode[feature] == "Required":
                prediction['message'] += f'{feature} not present in request so it will not be processed since it is ' \
                                         f'required\n'

    # Validate to ensure that the model was trained after the last update date of the training data set
    if clvmodel.training_date < config.data_set.update_date:
        prediction['message'] += f'Training Data Set has been updated (config.data_set.update_date) after the model ' \
                                 f'has been trained ({clvmodel.training_date})so request will not be processed\n'

    # TODO: Add prediction functions for each type of model that is added
    if type_of_model == TypeOfModel.VERTEX:
        prediction = vertex_predict_clv(request, config, clvmodel, type_of_model, prediction, future=future)
    elif type_of_model == TypeOfModel.PARETO_NBD or type_of_model == TypeOfModel.BGNBD:
        pass
    else:
        prediction['message'] += f'Type of Model not supported\n'

    return prediction


def vertex_predict_clv(request, config, clvmodel, type_of_model, prediction, future=False):
    # Verify that model address has LOCATION, PROJECT_ID, and ENDPOINT_ID
    address = clvmodel.address
    try:
        location = address['LOCATION']
    except KeyError:
        location = None
        prediction['message'] += {f'LOCATION parameter was not in {type_of_model.name} model address\n'}

    try:
        project_id = address['PROJECT_ID']
    except KeyError:
        project_id = None
        prediction['message'] += {f'PROJECT_ID parameter was not in {type_of_model.name} model address\n'}

    try:
        endpoint_id = address['ENDPOINT_ID']
    except KeyError:
        endpoint_id = None
        prediction['message'] += {f'ENDPOINT_ID parameter was not in {type_of_model.name} model address\n'}

    # Coerce data into type that was passed
    instance_data = {}
    model = CLVModelFeatures(clvmodel.data_fields)
    for feature in model.features:
        required = True if model.data_mode[feature] == "Required" else False
        try:
            request_feature = request.data[feature]
            if model.data_type[feature] == "STRING":
                instance_data[feature] = str(request_feature)
            elif model.data_type[feature] == "INTEGER":
                instance_data[feature] = int(request_feature)
            elif model.data_type[feature] == "FLOAT":
                instance_data[feature] = float(request_feature)
        except KeyError:
            request_feature = None
            instance_data[feature] = request_feature

        if required and request_feature is None:
            prediction['message'] += f"Feature: '{feature}' is not present in the request and it is required\n"
            return prediction


    # Specify API Endpoint Based on the Location
    api_endpoint = f'{location}-aiplatform.googleapis.com'
    client_options = {"api_endpoint": api_endpoint}

    credentials = service_account.Credentials.from_service_account_info(clvmodel.api_key)

    # Initialize client
    client = aiplatform_v1.services.prediction_service.PredictionServiceClient(
        credentials=credentials, client_options=client_options)

    # Initialize instance
    instance = json_format.ParseDict(instance_data, Value())
    instances = [instance]

    # Initialize parameters which are empty for this scenario
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())

    # Configure Endpoint
    endpoint = client.endpoint_path(
        project=project_id, location=location, endpoint=endpoint_id
    )

    # Submit Vertex Predict Request
    try:
        response = client.predict(
            endpoint=endpoint, instances=instances, parameters=parameters
        )

        for struct in response.predictions:
            prediction.update(dict(struct))

        response_message = ""
        if future:
            try:
                current_value = instance_data[clvmodel.metric]
                prediction["value"] -= current_value
                prediction["lower_bound"] -= current_value
                prediction["upper_bound"] -= current_value
                response_message = ""
            except KeyError:
                prediction["value"] = ""
                prediction["lower_bound"] = ""
                prediction["upper_bound"] = ""
                response_message = "Current Value was not passed so Future Only Value can't be determined\n"

    except InvalidArgument as exc:
        response_message = exc.errors[0]

    # prediction.update(instance_data)

    if prediction['message'] != "":
        prediction['message'] += f"{response_message}\n"

    return prediction



class CLVModelFeatures(object):

    def __init__(self, data_fields):
        self.features = []
        self.data_type = {}
        self.data_mode = {}
        if not isinstance(data_fields, list):
            data_fields = [data_fields]

        for data_field in data_fields:
            self.features.append(data_field["name"])
            self.data_type.update({data_field["name"]: data_field["type"]})
            self.data_mode.update({data_field["name"]: data_field["mode"]})

        self.features = sorted(list(set(self.features)))
