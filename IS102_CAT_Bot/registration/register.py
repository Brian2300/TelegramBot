'''
Created on 6 Jul 2017

@author: jiaqi
'''

import logging
from telegram import *
#InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import smtplib
from  email.mime.multipart import MIMEMultipart
from  email.mime.text import MIMEText

import random,string

import registration.verifyRegistration

import hashlib



'''This method check registration status and displays register button'''   
def register(bot, update):
    #chat_id
    chat_id = update.message.chat.id
    #If the user has already registered. 
    # chat_id is in the database and the length of smu_email is greater than 5.
    row_num = registration.verifyRegistration.check_registration_chat_id(chat_id) #row_num is of data type Tuple
    smu_email_id_dbValue = registration.verifyRegistration.check_registration_smu_email_id(chat_id) #smu_email_id_dbValue is of data type Tuple
    
    if row_num[0] != 0 and len(smu_email_id_dbValue[0]) > 5 :#if it is a registered user.
        update.message.reply_text('Welcome back! I recognized that you are a registered user:) \nUse /help to see what I can do for you.')
    else:
        #create button object
        keyboard = [[InlineKeyboardButton("register", callback_data='register')]]
        #reply_mark_up
        reply_markup = InlineKeyboardMarkup(keyboard)   
        #update is the command user typed in "/start" in this case.
        #reply to message--'/start'
        update.message.reply_text('Welcome to CAT! Please register with me:', reply_markup=reply_markup)



'''This method will be executed after the user press the register button.'''
def press_register(bot, update):

    query = update.callback_query
    
    bot.edit_message_text(text="Alright! What is your smu email address? Please make sure you typed in correctly and use the below format: \n\n/email [Your smu email address] \n\nReplace [Your smu email address] with your actual smu email address.\n\nFor example: \n/email is102_cat@sis.smu.edu.sg",
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)



'''This method runs after the user input their smu_email'''
def smu_email_input(bot, update, args):
    #there must be something after the "/email" command.
    if len(args) != 0:
        text = args[0] #text is the email address.
        #chat_id
        chat_id = update.message.chat.id
        tele_username = update.message.chat.username
        
        #The string after "/email" command must contain 'smu.edu.sg'
        if 'smu.edu.sg' in text:
            # The email address user entered cannot exist in database.
            db_tsmu_email_address_row = registration.verifyRegistration.check_smu_email_address_existance(text)  #db_tsmu_email_address_row is of data type Tuple.
            if db_tsmu_email_address_row[0] == 0:
                #The chat_id cannot exits in database.
                db_num_chat_id = registration.verifyRegistration.retrieve_num_chat_id(chat_id)
                if db_num_chat_id[0] == 0:
                    #generate verification code for this update
                    veri_code = generate_verification_code()
                    #store into database chat_id, verification code and temp smu email address.
                    registration.verifyRegistration.first_insert(chat_id,tele_username,veri_code,text)
                    #send email
                    send_email(text,veri_code)
                    update.message.reply_text('An email is sent to you! Please follow the instruction within the email to continue with the registration. \n\nIf you did not receive the email, retry:\n/email [Your smu email address] \n\nAnd make sure you entered your email address correctly.')
                else:
                    #delete the entry
                    registration.verifyRegistration.delete_duplicate_chat_id(chat_id)
                    #generate verification code for this update
                    veri_code = generate_verification_code()                   
                    #store into database chat_id, verification code and temp smu email address.
                    registration.verifyRegistration.first_insert(chat_id,tele_username,veri_code,text)
                    #send email
                    send_email(text,veri_code)
                    update.message.reply_text('An email is sent to you! Please follow the instruction within the email to continue with the registration. \n\nIf you did not receive the email, retry:\n/email [Your smu email address] \n\nAnd make sure you entered your email address correctly.')                    
            else:
                update.message.reply_text('An email has already sent to you! Please follow the instruction within the email to continue with the registration.')
        else:
            update.message.reply_text('Wrong input!!  Please enter your SMU email address.')
    else:
        update.message.reply_text('Wrong input!! Please use the correct format.')



def send_email(text,veri_code):
    #send email
    fromaddr = "is102.register@gmail.com"
    toaddr = text
    
    msg = MIMEMultipart()
    
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Welcome to CAT class! Please verify your email address."
    
    body = """Hi! Help us record your account by verifying your email address.
    
Please enter the below line to the telegram chat with CAT bot! 
    
/code %s
    
If you didn't perform registration with CAT bot, please kindly ignore this email.
    
Regards,
CAT_BOT""" % veri_code                

    
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "IS102CATisefyp!")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()    




'''This method is to randomly generate verification code(a string with 6 lowercase letters) for each of the user.'''
def generate_verification_code():
    return ''.join(random.choice(string.ascii_lowercase) for i in range(6))



"""This method runs after the user input veri_code in telegram"""
def verify_veri_code(bot, update, args):
    # args variable is of data type List. It is a list of strings.
    # retrieve user's chat_id from update.
    chat_id = update.message.chat.id
    #retrieve user's chat_id and veri_code from database.
    db_veri_code = registration.verifyRegistration.retrieve_first_insert(chat_id) # db_veri_code is of data type Tuple.
    #If the code entered by user is the same with the code previously generated.
    if len(args) !=0:

        if args[0] == db_veri_code[0]:
            #store into database smu_email
            registration.verifyRegistration.insert_smu_email(chat_id)
            update.message.reply_text('Ok~ Please let me know your group id. Make sure you use the format below:\n\n/gid [Your Group id]\n\nFor example: \n/gid G10')
        else:
            update.message.reply_text('Oops! Something is wrong. Please make sure your input matches the code I sent you.')
    else:
        update.message.reply_text('Wrong input!! Please use the correct format.')
        
        
        
"""This method runs after the user input their group_id"""
def group_id(bot, update, args):
    # retrieve user's chat_id from update.
    chat_id = update.message.chat.id
        
    if len(args) !=0:
        if args[0][0] == "G" or args[0][0] == "g":
            registration.verifyRegistration.insert_group_id(chat_id, args[0].upper())
            update.message.reply_text('Last step! Choose a password for yourself and remember it. It will be used when you log in to CAT web portal. Make sure you use the format below: \n\n/pwd [Your password] \n\nReplace [Your Password] with your own password.\n\nFor example: \n/pwd tele123 \n\nNOTE: Do not contain any white spaces within your password.')
        else:
            update.message.reply_text('Wrong input!! Your group_id needs to start with a "G" or "g".') 
               
    else:
        update.message.reply_text('Wrong input!! Please use the correct format.') 
        
        
        
"""This method runs after users provide web password."""        
def web_password(bot,update,args):
    # retrieve user's chat_id from update.
    chat_id = update.message.chat.id   
    if len(args) != 0:
        if args[0]=="": # the condition will always be false.           
            #password cannot be empty string.
            update.message.reply_text('Your password cannot be empty! Please enter again!')
        elif len(args) == 1:
            #hash the password.
            pwd_bytes = args[0].encode()
            hash_obj = hashlib.sha1(pwd_bytes)
            hex_dig = hash_obj.hexdigest()
            #insert the hash value(in hex) into database.
            registration.verifyRegistration.insert_password_hash(chat_id,hex_dig)  
            update.message.reply_text('Woohoo! registration is successful! Please use /help to see what can this bot do for you!')
        else:
            #password cannot contain empty spaces.
            update.message.reply_text('Your password cannot contain white spaces! Please enter again!')
    else:
        update.message.reply_text('Wrong input!! Please use the correct format.')
        
        
          
    
    
    
    
