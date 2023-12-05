# story-generator-dalle

Scripts to generate story and images for a book cover using chatgpt openai apis
and dalle


curl -X POST http://localhost:5000/process-story \
-H "Content-Type: application/json" \
-d $'{
  "userid": "info@littlestorywriter.com",
  "So, who is the brave hero of our story? Could you share the name?": "Jay",
  "Marvelous! And is ___ a daring little girl or a courageous little boy?": "Boy",
  "How many candles will be on ___\u2019s birthday cake? In other words, how old is ___?": "4",
  "Heroes often have companions. \nWho will share ___s adventures in the story?": "robot",
  "What a charming choice! \n\nAnd what is this loyal ___\'s name?": "Nailer",
  "Just to make sure I picture ___ correctly, is this companion a \'he\' or \'she\'?": "male",
  "Setting the tone is key. \nWhat mood shall I weave into the story\u2019s fabric?": "Whimsical and Imaginative",
  "Where do ___ and ___\u2019s footsteps take them? What\u2019s the setting of the story?": "Outer Space",
  "Every story needs a heart. \nWhat\u2019s the theme of ___ and ___\u2019s tale?": "Friendship and Adventure",
  "Stories travel across the globe. In which language shall we tell ___\'s enchanting tale?": "English (British)",
  "Now, let\u2019s get a glimpse of our hero. \nWhat is ___\'s ethnicity?": "African",
  "And to add more detail to her portrait, what is the shade of ___\u2019s skin?": "Medium",
  "What is the color of ___\'s hair that catches the sunlight in our story?": "Black",
  "And for the artist drawing ___\'s courageous moments, how long should the hair be?": "medium long",
  "The final touch is the art. What illustration style shall capture the essence of this story?": "Cut-Paper Collage",
  "tripettoId": "cc3701e9cf",
  "tripettoIndex": 5,
  "tripettoCreateDate": "2023-11-20T10:29:48.000Z",
  "tripettoFingerprint": "7389f01bb4ccdee76146d51d336b031cb9947ed201de457bc1c5d780c3677b2b",
  "tripettoFormReference": "aa9972f9af75f08b3f7c7035e3ea41626e9504f17626ea1c5ca0b3acf219e34d",
  "tripettoFormName": "Book Configurator"
}'
