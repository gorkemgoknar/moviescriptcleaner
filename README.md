# gg_moviescriptcleaner
Script to clean Movie scripts to get character lines
Provided as is non-commercial use only.

Used to clean movie scripts for persona based chatbot with GPT2, demo in https://www.metayazar.com

Clean a script file to conversations.
Note that first 20-30 lines may not be properly good in output
As it learns from those lines where character lines really begin
and calculates whitespaces.. 

--inputdir  to specify directory for txt files, else use working directory
--file   to specify single file only
--debug  for debug output

Base file formats:
Format 1 :    Standart movie scripts 
                  TITLE

         Some long description etc... 
                  CHARNAME
                (some intent)
             talks some lines etc

                  OTHERCHARNAME
             responds to chat

         Some other things that are not dialog.

Format 2  :  scripts with no indentation

         CHARNAME : says something
         OTHERCHAR: response

         Some other things that are not dialog\n
