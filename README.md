# iMessageGroupChatAnalyzer
Welcome to the iMessage Group Chat Analyzer. This python script will allow you to analyze your group chat's tapback (likes, dislikes, etc.) habits. 

Requirements:
1) An Apple computer to run this script on
2) iCloud for iMessage enabled on this decive
3) Full disk access for Terminal
4) Python 3

Setup:
1. Ensure full disk access for terminal

1a. Follow these steps if you don't know how to do this

2. In order to have a cleaner output, you will want to allow access to your contacts
  
2a. Navigate to ~/Library/Application Support/AddressBook/Sources/ and find the largest folder. It should be named similar to '6A3869D0-3BC4-41E2-B14B-303DDD547254'
 
2b. Open chatanalyzer.py and change line 123 with your folder name. This will allow your contacts to map to phone numbers.

Instructions:
1) Clone this single-file repo anywhere on your Mac computer
2) Right click on the location it resides and 'New Terminal at Folder'
3) Type 'python3 chatanalyzer.py'
4) Follow the inline instructions to see your group message stats!
