# Wordle_bot

This repository contains a python script that that can play the wordle game by itself using concepts I learned from watching 3Blue1Brown's video(https://www.youtube.com/watch?v=v68zYyaEmEA&t=713s&ab_channel=3Blue1Brown) about beating the Wordle game utilizing information theory. Utilizing all of the words that Wordle allows users to guess, the bot is able to choose guesses that would reveal the most information for its next guess.


wordle_answers.txt contains all of the words that Wordle uses in its game


wordle_bot.py utilizes selenium to conduct all of its web automation. With selenium, we are able to open up the wordle web page, enter out guesses using the keyboard,
and retreive the result of our guesses by accessing html attributes from the game board. Using this information, we are able to trim our guess space using the information found as a result of our guess, find the entropy values of the remaining words in the guess space, and then choose the word that has the maximum potential entropy as our next guess. The web page closes after we have found the correct answer.






