from flask import Flask, request, jsonify
from flask_cors import CORS  
import requests
import json
import os

app = Flask(__name__)
result_file = 'prediction_result.json'
CORS(app)

noofribbons = 3
noofarrows = 3
noofstars = 3

total_ribbons = 0
total_arrows = 0
total_stars = 0

prediction_threshold = 0.90

def make_prediction(image_file):
    prediction_key = "27dea928805b4e6baf8b46e2854986b7"
    endpoint = 'https://cvobjectdetector-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/060c28e6-5b5f-41cb-8426-5036e6cfa1b9/detect/iterations/Iteration1/image'
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }
    response = requests.post(endpoint, headers=headers, data=image_file.read())

    if response.status_code == 200:
        result = response.json()
        return {
            "BeautyEnhance": noofribbons - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Ribbon" and obj["probability"] >= prediction_threshold),
            "JointEnhance": noofarrows - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Arrow" and obj["probability"] >= prediction_threshold),
            "BoneEnhance": noofstars - sum(1 for obj in result.get("predictions", []) if obj["tagName"] == "Star" and obj["probability"] >= prediction_threshold)
        }
    else:
        return {"Error": f"{response.status_code} - {response.text}"}

def update_result_file(prediction_result):
    existing_data = read_from_json(result_file)

    # Update existing data with the new prediction results
    for key, value in prediction_result.items():
        existing_data[key] = value

    # Update counts in the existing data
    existing_data["total_ribbons"] = total_ribbons
    existing_data["total_arrows"] = total_arrows
    existing_data["total_stars"] = total_stars

    # Write the updated data back to the result file
    write_to_json(existing_data, result_file)

def read_from_json(file_path):
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as json_file:
                loaded_data = json.load(json_file)
                return loaded_data
        else:
            return {}
    except Exception as e:
        return {"Error": f"Unexpected error: {str(e)}"}

def write_to_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)

@app.route('/', methods=['POST', 'GET'])
def detect_objects():
    global total_ribbons, total_arrows, total_stars

    if request.method == 'POST':
        try:
            if 'image' not in request.files:
                return jsonify({"Error": "No image file provided"}), 400

            image_file = request.files['image']

            if image_file.filename == '':
                return jsonify({"Error": "No selected file"}), 400

            # Make predictions
            prediction_result = make_prediction(image_file)

            # Update the result file with the prediction results
            update_result_file(prediction_result)

            # Update global counts
            total_ribbons = prediction_result["BeautyEnhance"]
            total_arrows = prediction_result["JointEnhance"]
            total_stars = prediction_result["BoneEnhance"]

            # Return a response indicating successful image processing
            return jsonify({"Message": "Image processed successfully"})
        except Exception as e:
            return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500

    elif request.method == 'GET':
        # HTML form directly defined within the Python script
        return '''
        <!doctype html>
        <title>Upload an image</title>
        <h1>Upload an image</h1>
        <form method=post enctype=multipart/form-data>
            <input type=file name=image>
            <input type=submit value=Upload>
        </form>
        '''

@app.route('/result', methods=['GET'])
def retrieve_result():
    try:
        # Read the latest result from the JSON file
        result_data = read_from_json(result_file)

        if result_data and "Error" not in result_data:
            # Convert the result data to the desired format
            formatted_result = [
                {"name": "beauty_enhance", "quantity": result_data["BeautyEnhance"], "status": "Needs Restock" if result_data["BeautyEnhance"] <= 1 else "Stocked"},
                {"name": "bone_enhance", "quantity": result_data["BoneEnhance"], "status": "Needs Restock" if result_data["BoneEnhance"] <= 1 else "Stocked"},
                {"name": "joint_enhance", "quantity": result_data["JointEnhance"], "status": "Needs Restock" if result_data["JointEnhance"] <= 1 else "Stocked"}
            ]

            return jsonify({"items": formatted_result})
        else:
            return jsonify({"Error": "Result file is empty"}), 500
    except Exception as e:
        return jsonify({"Error": f"Unexpected error: {str(e)}"}), 500


if __name__ == '__main__':
    initial_counts = read_from_json(result_file)
    total_ribbons = initial_counts.get("total_ribbons")
    total_arrows = initial_counts.get("total_arrows")
    total_stars = initial_counts.get("total_stars")

    if total_ribbons is not None:
        total_ribbons = int(total_ribbons)

    if total_arrows is not None:
        total_arrows = int(total_arrows)

    if total_stars is not None:
        total_stars = int(total_stars)

    app.run(debug=True)




