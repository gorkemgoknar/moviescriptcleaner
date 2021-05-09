"""
    Clean a script file to conversations.
    Note that first 20-30 lines may not be properly good in output
    As it learns from those lines where char scripts really beging
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

    Format 2  :  Non intended scripts

    CHARNAME : says something
    OTHERCHAR: response

    Some other things that are not dialog\n
"""


import statistics
import os
import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import codecs
import logging
from pprint import pformat


logger = logging.getLogger(__file__)
logger.setLevel(level=logging.INFO)



def convert_file_to_script(filename, test_name_change=False):
    """ Convert a script file that is non standart
    to standart script format
    use test_name_change=True to first test if file should be converted
    if returninf filename is starts with PRO_ then this file should be converted
    a tmp/ folder in file folder is created if converted

    Non standart scripts are like

    NAMECHAR: something said
    OTHERCHAR: responding something else

     """

    ##print("INPUT: " + filename)
    basefile = os.path.basename(filename)
    path = os.path.dirname(filename)
    remove_outfile = False
    col_type_counter = 0
    linecounter = 0 
    threshold = 10 
    outfilename = "PRO_"+basefile
    outpath = path + "./tmp/"
    if not os.path.exists(outpath):
        os.mkdir(outpath)



    with open(filename,encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        with open(os.path.join(outpath,outfilename), "w") as fw:
            for line in lines:
                if test_name_change:
                    linecounter += 1
                    if linecounter>200:
                        logging.debug("Script ok no conversion: "+filename)
                        remove_outfile = True
                        break

                col_in_line = line[:15].find(":")
                name = None
                if col_in_line>0:
                    if test_name_change:
                        col_type_counter += 1
                        if col_type_counter>threshold:
                            logging.debug("Script needs conversion : "+outfilename)
                            
                            return os.path.join(outpath,outfilename)
                        
                    name = " "*10 + line[:col_in_line].upper()+"\n"
                    line = " "*5 + line[col_in_line+1:]+"\n"
                if not test_name_change:
                    if name is not None: 
                        fw.write(name)
                    fw.write(line)
    if remove_outfile:
        os.remove(os.path.join(outpath,outfilename))
        #print("Should remove out file")
        return filename 

    return os.path.join(outpath,outfilename)





def get_left_whitepace_length(text):
    """ Get whitespace length on left side """

    left_space = len(text) - len(text.lstrip(' ')) #space 
    left_tab = len(text) - len(text.lstrip('\t')) #tab
    
    return left_space+left_tab

def get_right_whitepace_length(text):
    """ Get whitespace length on right side """

    right_space = len(text) - len(text.rstrip()) 
    return right_space
    
def is_line_character_name(text,min_whitespace_or_tab=4):
    """ Check if this text is a name on movie script format.
    Multiple conditions are check.
    Usually a name is first line all capital in center :
           SOMENAME
       Some line talked by name
    """
    #see if there is indentation in beginning
    ##TODO try regexp here for tab or space

    if (get_left_whitepace_length(text))<min_whitespace_or_tab:
        return False
    
    if get_right_whitepace_length(text)==0:
        return False
    
    if text.lstrip()[0].isdigit() :
        #do not accept char name starting with digit
        return False 

    if len(text.strip()) > 15 :
        #do not accept longer than 15 char name as name
        return False 

    #check if all caps 
    all_caps = text.isupper()
    if all_caps:
        return True
    
    
    #new check
    ##check if Starts with capital and in 15 chars there is a :
    
    """
    ##this messes 2001
    if all_caps:
        #assume character name is max 15 chars!
        if len(text)<15:
            return True
    """    
    
    return False


def is_next_chapter_or_section(text, second_pass=False):
    """ Check if text is a chapter 
    (Not a name, not whitespace, not dialog ) """
    stripped = text.strip()

    if stripped.startswith("="):
        #ignore math output
        return False

    if len(stripped)<=0:
        ##just an empty line!
        return False
    
    if stripped[0].isdigit() and stripped[-1].isdigit() and  stripped.isupper():
        return True 

    if stripped == len(stripped) * '*' :
        ##line consist of only *)
        return True 

    if not stripped[0].isalpha()  and stripped.count('-')>=3 :
        return True

    if stripped[0].isdigit()  and len(stripped)<4:
        #and stripped[1] == " " 
        #can have answer with digit! but need more for it to be text
        return True
    
    if second_pass and stripped.startswith("["):
        return True
    

    if second_pass is True and stripped[0] == "(" and stripped[-1] ==")":
        ##probaly something about character but ignoring 
        return True
    
    if stripped[-1].isdigit() and len(stripped)<4:
        ##can be a mathematical output so last char can be digit
        #was put here for right page numbers added alpha check
        #= ...3
        return True

    #do not convert to upper case check if upper chars are inside

    if stripped.startswith("INSIDE "):
        return True

    #upper_stripped = stripped.upper()

    if  'CUT TO' in stripped.upper():
        ##should not hit here if it was char continuation anyway
        return True

    #no not a section
    return False
    
def should_bypass_line(text):
    """ If line should be bypassed.
    Bypass conditions:
    all whitespace
    has certain keys in text uppercase (CONTINUE etc)
    Bypass and ignore """
    stripped = text.lstrip()
    
    #contains character action/drama
    #if(text.strip().startswith("(")):
    #    #bypass special char starst
    #    return True

    if "CONTINUE" in text:
        return True
    
    if text.isspace():
        return True
    
    return False

def get_line_length_after_name(text):
    """ Calculate line after splitting with :
    This is used for non standart conversion script """
    splitted = text.split(":")
    #first is name and ends until :
    if len(splitted)>1:
        return len( splitted[1] )
    else:
        return 0

def get_clean_script(filename,debug=False, line_count=None, left_whitespace_start=2, name_trigger=30):
    """ Generate a cleaned script format file.
    Note that this is not a really standart format
    just a format that persona file parser can undersand
    """

    #Start leftspace count
    #will update once 10 character names found
    #usually it is 4 or 6 but found instances where 2 tabs is used
    max_left_whitespace = left_whitespace_start
    
    out_dict = {}
    out_dict["names"] = None
    out_dict["dialog"] = None
    out_dict["name_count"] = 0
    out_dict["num_script_lines"] = 0
    
    with open(filename) as f:
        script_lines = 0
        name_list = []
        
        
        
        try:
            if line_count is None:
                lines = f.readlines()
            else:
                lines = f.readlines()[0:line_count]
        except Exception as e:
            logging.warning(f"Cannot open {filename}")
            #raise(e)
            #print(e)
            return out_dict
            
        prev_line_is_char_or_dialog = False

        dialog = []
        char_line = ""
        char_line_calculated_left_space = [0]

        NAME_TRIGGER = name_trigger
        num_names = 0
        get_left_whitespace_count_after_this_line = False
        
        print_this_line = False
        
        if debug : print_this_line = True
        
        char_not_talking=0

        for line in lines:
            debug_header = ''
            
            if prev_line_is_char_or_dialog:
                debug_header += 'PrevIsLineoRChar,'
                #print_this_line = True

            if should_bypass_line(line):
                #print(f"pass: {line}")
                debug_header += 'Bypassing,'
                prev_line_is_char_or_dialog = False
                #if print_this_line: print(debug_header + line)
                continue
                
            ##line stripping is not done above as name check etc depend on it
            
            if (char_not_talking > 5) or is_next_chapter_or_section(line): 
                ##this is a section make sure we append char talk
                if(get_line_length_after_name(char_line) > 1 ):
                        #check if it is actually line, if it is empty or single char/whitespace bypass it
                        #script_lines += 1
                        dialog.append(char_line)
                        debug_header += 'appendline'
                        if debug: print(char_line)
                        char_line = ""
  

                ##10 line no script assume section
                ##Need for dialogue sepeartion.. Just add a line in dialog
                dialog.append("*"*15)
                debug_header += 'nextSection,'
                if print_this_line: logger.debug(debug_header+ " | " +line)
                if debug: logger.debug("*"*10)
                char_not_talking += 1 
                ##should continue to next line
                

            if is_line_character_name(line, min_whitespace_or_tab=max_left_whitespace):
                prev_line_is_char_or_dialog = True 
                name = line.strip()
                num_names += 1
                name_list.append(name)
                get_left_whitespace_count_after_this_line = True
                
                ##append previous char_line
                if(get_line_length_after_name(char_line) > 1 ):
                        #check if it is actually line, if it is empty or single char/whitespace bypass it
                        #script_lines += 1
                        dialog.append(char_line)
                        debug_header += 'appendline'
                        if debug: logger.debug(char_line)
                        
                #start new char_line
                char_line = "\n\t" + name + " :"
                debug_header += 'NameChar,'
            else:
                if prev_line_is_char_or_dialog:
                    
                    space_length = get_left_whitepace_length(line) 
                    
                    ##need auto left linespace calculation filling the array as tagged
                    if get_left_whitespace_count_after_this_line:
                        char_line_calculated_left_space.append(space_length)
                        get_left_whitespace_count_after_this_line = False
                        debug_header += 'getwhitespace,'
                        
                    if space_length >= max_left_whitespace:
                        char_line += " " + line.strip()
                        #print("Line of char:" + char_line , end= " ")
                        prev_line_is_char_or_dialog = True
                        char_not_talking = 0
                        debug_header += 'charistalking,'
                        if len(char_line_calculated_left_space)>20 and num_names>=NAME_TRIGGER:
                            max_left_whitespace = statistics.median(char_line_calculated_left_space)
                            NAME_TRIGGER = 999999
                            debug_header += 'resetleft,'
                            
                        script_lines += 1
                        if print_this_line: logger.debug(debug_header + " | " + line)
                        #continue

                    else:
                        #end of character or script
                        char_not_talking +=1
                        debug_header += 'charNOTtalking,'
                        prev_line_is_char_or_dialog = False

                else:
                    char_not_talking += 1
                    debug_header += 'notprev,'


                        
                    if(get_line_length_after_name(char_line) > 1 ):
                        #check if it is actually line, if it is empty or single char/whitespace bypass it
                        #script_lines += 1
                        dialog.append(char_line)
                        debug_header += 'appendline'
                        if debug: logger.debug(char_line)
                        char_line = ""


                    if is_next_chapter_or_section(line,second_pass=True) and char_not_talking>5:
                        dialog.append("*"*25)
                        debug_header += 'nextSection,'
                        if print_this_line: print(debug_header+ " | " +line)
                        if debug: logger.debug("*"*10)
                        continue


                
                debug_header +='endelse,'
                if print_this_line: logger.debug(debug_header + " | " +line)
            debug_header +='endLine,'
            if print_this_line: logger.debug(debug_header + " | " +line)
                
                
    out_dict["names"] = set(name_list)
    out_dict["dialog"] = dialog
    out_dict["name_count"] = num_names
    out_dict["num_script_lines"] = script_lines
    
    return out_dict


def get_filename_to_process(filename):
    """Test filename if conversion is needed.
    Convert it if necessary and return filename"""

    if convert_file_to_script(filename, test_name_change=True) != filename:
        logger.info("Converting {}".format(filename))

        filename = convert_file_to_script(filename)
    
    #print("Use this file:"+ filename)
    return filename 


def write_output(out, path,filename ):
    """ Write out to text file in path and filename indicated """

    basefile = os.path.basename(filename)
    out_file = os.path.join(path, basefile)
    with open(out_file, 'w') as f:
        #prev_line = None
        prev_is_section = False
        for line in out["dialog"]:
            ##Check if section
            
            if (prev_is_section) and ('***********' in line):
                continue
            elif '***********' in line:
                prev_is_section = True
            else:
                prev_is_section = False
            
            #if(line != prev_line):
            ###Multi * and same lines ignored
            f.write(f"{line}\n")
    return out_file

def __main():
    """
    Main file runs in current folder with default args
    """

    #description=''
    #epilog=""

    parser = ArgumentParser(description=__doc__, #prog='Movie Script Cleaner',
      formatter_class=RawDescriptionHelpFormatter,
      )



    parser.add_argument("--inputdir", type=str, default="./", help="Path or url of the text scripts. Current directory by default")
    parser.add_argument("--file", type=str, default="", help="File process mode conversion only")
    parser.add_argument("--debug", action='store_true', help="Debug output")
    
    #other examples
    #parser.add_argument("--dataset_cache", type=str, default='./dataset_cache', help="Path or url of the dataset cache")
    #parser.add_argument("--model", type=str, default="openai-gpt", help="Model type (openai-gpt or gpt2)", choices=['openai-gpt', 'gpt2'])  # anything besides gpt2 will load openai-gpt
    #parser.add_argument("--max_history", type=int, default=2, help="Number of previous utterances to keep in history")
    #parser.add_argument("--no_sample", action='store_true', help="Set to use greedy decoding instead of sampling")
    #parser.add_argument("--max_length", type=int, default=20, help="Maximum length of the output utterances")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO )
    
    #logger.warning("Running process %d", args.local_rank)  # This is a logger.warning: it will be printed by all distributed processes
    logger.info("Arguments: %s", pformat(args))



    if args.file != "":
        path = "./tmp/"
        logger.info("Get file to process..")
        filename = get_filename_to_process(args.file)
        logger.info(filename)

        logger.info("Get clean script..")
        ##this will get left starting ones, but may miss some other ones..
        out = get_clean_script(filename,debug=args.debug,name_trigger=25,left_whitespace_start=0)
        logger.info( path + filename)
        logger.info("Write output..")
        outfile = write_output(out,path,filename)
        logger.info("DONE , written to: ", outfile)
        return True 



    goodfiles3 = []
    for filename in os.listdir(args.inputdir):

        if not filename.endswith(".txt"):
            continue
        
        ##do conversion if necessary and get filename of that
        filename = get_filename_to_process(filename)

        ##this will get left starting ones, but may miss some other ones..
        out = get_clean_script(filename,debug=False,name_trigger=25,left_whitespace_start=0)
        
        name_count = 0
        num_script_line =0 
        if "name_count" in out:
            name_count = out["name_count"]
        if "num_script_lines" in out:
            num_script_line = out["num_script_lines"]

        logger.debug(f"Filename:{filename}, counted:{name_count} names, has:{num_script_line} script lines")
        
        if name_count > 5 and  num_script_line > 100 and len(out["dialog"])>10:
            goodfiles3.append([os.path.join(args.inputdir, filename), name_count,num_script_line, "35_0"])
            

    pp = pprint.PrettyPrinter(indent=1)
    logger.info("File List:\n %s", pp.pformat(goodfiles3))




    #make a folder for output
    path = os.path.join(args.inputdir, 'output')
    if not os.path.exists(path):
        os.mkdir(path) 

    good_file_array= goodfiles3

    logger.info("Writing files...")  
    for filename in [row[0] for row in good_file_array]:
        ##will first get array
        out = get_clean_script(filename,debug=args.debug,name_trigger=25,left_whitespace_start=0)
        ##DO IF: if out["name_count"]>5 and out["num_script_lines"]>100 and len(out["dialog"])>10:
        
        outfile = write_output(out,path,filename)
        logger.debug("Written to: %s", outfile)

    logger.info("Files written to:  %s", path)            
    logger.info("DONE")

if __name__ == '__main__':
    __main()
