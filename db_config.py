import logging
import re
from flask_sqlalchemy import SQLAlchemy
import dotenv
from flask import Flask, jsonify, request
import json
from extract_visual_descriptions import extract_visual_description

# Import your modules here
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from LSW_04_image_generation import generate_images_from_prompts

# Initialize Flask app
import logging
import re
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

#  load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class StoryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tripettoId = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Text)
    story_configuration = db.Column(db.Text)
    visual_configuration = db.Column(db.Text)
    story = db.Column(db.Text)
    image_urls = db.Column(db.Text)

# Function to extract image prompts from text
def extract_output_image_prompts(input_text):
    matches = re.findall(r'"prompt_img_\d{2}": "(.*?)"', input_text)
    return {f"prompt_img_{i:02}": prompt for i, prompt in enumerate(matches)}

# Process story endpoint
@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        data = request.json
        tripetto_id = data.get('tripettoId')
        if not tripetto_id:
            return jsonify({'error': 'tripettoId is required'}), 400

        # Convert Tripetto JSON to lists
        order, story_configuration, visual_configuration = convert_tripetto_json_to_lists(data)

        print(order, story_configuration, visual_configuration)
        # Generate story
               # Save to database
        existing_story = StoryData.query.filter_by(tripettoId=tripetto_id).first()
        if existing_story:
            return jsonify({'error': 'A story with this tripettoId already exists'}), 400

        book_data = generate_story(story_configuration)

        # Generate visual description
        visual_description = generate_visual_description(visual_configuration)
        print(visual_description)
        
        # Extract visual description
        visual_descriptions=extract_visual_description(visual_description)
        print(visual_descriptions)

        # Generate image prompts
        image_prompts = generate_image_prompts(book_data, visual_descriptions)
        print(image_prompts)

        # Extract image prompts
        prompts_for_images = extract_output_image_prompts(image_prompts)
        print(prompts_for_images)

        # Generate images from prompts
        image_urls = generate_images_from_prompts(prompts_for_images)
        print(image_urls)

 
        # Save to database
        new_story_data = StoryData(
            tripettoId=tripetto_id,
            order=json.dumps(order),
            story_configuration=json.dumps(story_configuration),
            visual_configuration=json.dumps(visual_configuration),
            story=json.dumps(book_data),
            image_urls=json.dumps(image_urls)
        )
        db.session.add(new_story_data)
        db.session.commit()

        print("Story data saved to database" + str(new_story_data),"with tripetto_id" + str(tripetto_id)  )
        return jsonify({'tripettoId': tripetto_id})

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500



# Endpoint to retrieve story data
@app.route('/get-story-data/<tripetto_id>', methods=['GET'])
def get_story_data(tripetto_id):
    story_data = StoryData.query.filter_by(tripettoId=tripetto_id).first()
    if story_data:
        return jsonify({
            "tripettoId": tripetto_id,
            'order': json.loads(story_data.order),
            'story_configuration': json.loads(story_data.story_configuration),
            'visual_configuration': json.loads(story_data.visual_configuration),
            "story": json.loads(story_data.story),  # Corrected
            'image_urls': json.loads(story_data.image_urls)
        })
    else:
        return jsonify({'error': 'Data not found'}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables within the application context
    app.run(debug=True, host="0.0.0.0", port=5000)
