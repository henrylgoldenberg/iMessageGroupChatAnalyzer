# iMessageGroupChatAnalyzer
This python script was created to analyze a group chat's tapback (likes, dislikes, etc.) habits. 
It is a fairly simple script that combines Apple's chat database, address book, and some logic to display results.

This idea originally came to me when my friend's and I were discussing who was the funniest out of the group. I figured there must be a way to determine this based on facts. After a little digging, I found a way to query my chat data and find out who really was the funniest in the group. Upon sending these stats, the idea to analyze all the tapback data led me to create this more in depth script that shows tapbacks sent and recieved for any given member in any given group chat. 

Please feel free to use any or all of this code to analyze your own group chats and finally prove who is the funniest (or most 'loved') once and for all!

Notes:
- You will need to find your own address book folder name. That can be found by following the path given in the script.
- You will need to change the 'my_number' variable to your own phone number
- Some query strings were based on this project found here https://github.com/yortos/imessage-analysis/. Thank you for the help getting started!
