# story-generator-dalle

Scripts to generate story and images for a book cover using chatgpt openai apis
and dalle


curl -X POST http://localhost:5000/process-story \
-H "Content-Type: application/json" \
-d $'{
  "userid": "info@littlestorywriter.com",
  "So, who is the brave hero of our story? Could you share the name?": "Jay",
  "Marvelous! And is ___ a daring little girl or a courageous little boy?": "Boy",
  "How many candles will be on ___s birthday cake? In other words, how old is ___?": "4",
  "Heroes often have companions. Who will share ___s adventures in the story?": "robot",
  "What a charming choice! And what is this loyal ___s name?": "Nailer",
  "Just to make sure I picture ___ correctly, is this companion a he or she?": "male",
  "Setting the tone is key. What mood shall I weave into the storys fabric?": "Whimsical and Imaginative",
  "Where do ___ and ___s footsteps take them? Whats the setting of the story?": "Outer Space",
  "Every story needs a heart. Whats the theme of ___ and ___s tale?": "Friendship and Adventure",
  "Stories travel across the globe. In which language shall we tell ___s enchanting tale?": "English (British)",
  "Now, lets get a glimpse of our hero. What is ___s ethnicity?": "African",
  "And to add more detail to her portrait, what is the shade of ___s skin?": "Medium",
  "What is the color of ___s hair that catches the sunlight in our story?": "Black",
  "And for the artist drawing ___s courageous moments, how long should the hair be?": "medium long",
  "The final touch is the art. What illustration style shall capture the essence of this story?": "Cut-Paper Collage",
  "tripettoId": "cc3701e9cf",
  "tripettoIndex": 5,
  "tripettoCreateDate": "2023-11-20T10:29:48.000Z",
  "tripettoFingerprint": "7389f01bb4ccdee76146d51d336b031cb9947ed201de457bc1c5d780c3677b2b",
  "tripettoFormReference": "aa9972f9af75f08b3f7c7035e3ea41626e9504f17626ea1c5ca0b3acf219e34d",
  "tripettoFormName": "Book Configurator"
}'


curl -X POST http://16.171.115.221/process-story \
-H "Content-Type: application/json" \
-d $'{
  "userid": "info@littlestorywriter.com",
  "So, who is the brave hero of our story? Could you share the name?": "Jay",
  "Marvelous! And is ___ a daring little girl or a courageous little boy?": "Boy",
  "How many candles will be on ___s birthday cake? In other words, how old is ___?": "4",
  "Heroes often have companions. Who will share ___s adventures in the story?": "robot",
  "What a charming choice! And what is this loyal ___s name?": "Nailer",
  "Just to make sure I picture ___ correctly, is this companion a he or she?": "male",
  "Setting the tone is key. What mood shall I weave into the storys fabric?": "Whimsical and Imaginative",
  "Where do ___ and ___s footsteps take them? Whats the setting of the story?": "Outer Space",
  "Every story needs a heart. Whats the theme of ___ and ___s tale?": "Friendship and Adventure",
  "Stories travel across the globe. In which language shall we tell ___s enchanting tale?": "English (British)",
  "Now, lets get a glimpse of our hero. What is ___s ethnicity?": "African",
  "And to add more detail to her portrait, what is the shade of ___s skin?": "Medium",
  "What is the color of ___s hair that catches the sunlight in our story?": "Black",
  "And for the artist drawing ___s courageous moments, how long should the hair be?": "medium long",
  "The final touch is the art. What illustration style shall capture the essence of this story?": "Cut-Paper Collage",
  "tripettoId": "cc3701e9cf",
  "tripettoIndex": 5,
  "tripettoCreateDate": "2023-11-20T10:29:48.000Z",
  "tripettoFingerprint": "7389f01bb4ccdee76146d51d336b031cb9947ed201de457bc1c5d780c3677b2b",
  "tripettoFormReference": "aa9972f9af75f08b3f7c7035e3ea41626e9504f17626ea1c5ca0b3acf219e34d",
  "tripettoFormName": "Book Configurator"
}'