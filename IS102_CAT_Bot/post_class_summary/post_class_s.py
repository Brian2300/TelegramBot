'''
Created on 24 Aug 2017

@author: jiaqi
'''

import post_class_summary
from telegram import *
from telegram.ext import MessageHandler, Filters, ConversationHandler
from post_class_summary import post_class_summary_db



"""This method deletes the entries for a particular user in 'left_post_class_question' table as well as 'post_class_summary answer' table"""
def clear_before_start(bot,update):
    #chat_id
    chat_id = update.message.chat.id
    #retrieve smu_email_id by chat_id
    smu_e_id = post_class_summary_db.retrieve_smu_email_id(chat_id)
    
    #Delete the remaining entries for the particular student in 'left_post_class_question' table.
    post_class_summary_db.delete_left(smu_e_id)
    #retrieve current week
    cur_week = post_class_summary_db.retrieve_cur_week()
    #Delete the existing answers for a particular student in current week in 'post_class_summary_answer' table.
    post_class_summary_db.delete_answer(smu_e_id, cur_week) 



"""This method creates status dictionary for ConversationHandler"""
def create_status_dic(bot,update):
    #empty status dictionary
    status = {}
    #chat_id
    query = update.callback_query
    chat_id = query.message.chat_id
    #retrieve group_id by chat_id
    group_id = post_class_summary_db.retrieve_group_id(chat_id)
    #retrieve professor_avatar_id by group_id
    p_avatar_id = post_class_summary_db.retrieve_avatar_id(group_id[0])    
    # count the number of questions by avatar_id
    num_q = post_class_summary_db.num_of_question(p_avatar_id[0])
    
    for i in range(num_q[0]):
        status[i] = [MessageHandler(Filters.text, receive_answer_send_rest_questions)]
        
    status[num_q[0]] = [MessageHandler(Filters.text, update_week)]
    return status



"""This method updates the ' left_post_class_question' table and triggers to send out the first question."""
def post_class_summary(bot,update):
    clear_before_start(bot, update) 
    #retrieve the avatar_id of professor.    
        #chat_id
    chat_id = update.message.chat.id
        #retrieve smu_email_id by chat_id
    smu_email_id = post_class_summary_db.retrieve_smu_email_id(chat_id)
        #retrieve group_id by chat_id
    group_id = post_class_summary_db.retrieve_group_id(chat_id)
        #retrieve professor_avatar_id by group_id
    p_avatar_id = post_class_summary_db.retrieve_avatar_id(group_id[0])      
    #retrieve the question_ids from 'post_class_summary_questions' table by p_avatar_id
    question_list = post_class_summary_db.q_id(p_avatar_id) # question_list is of data type Tuple.
    #print(question_list) # ((1,), (2,), (3,))
    # retrieve the row_count from 'post_class_summary_questions' table by p_avatar_id
    row_count = post_class_summary_db.row_count(p_avatar_id) # row_count is of data type Tuple.
    #update the 'left_post_class_question' table using the retrieved smu_email_id row_num and question_ids.
    for i in range(row_count[0]):
        r = i+1
        q_id = question_list[i][0]
        post_class_summary_db.insert_email_row_num_q_id(smu_email_id,r,q_id) 
    #select MIN() row_num and corresponding question_id from 'left_post_class_question' table
    min_r_q_id = post_class_summary_db.retrieve_minrow_question_id(smu_email_id) #min_r_q_id is of data type Tuple. 
    #retrieve question by using question_id from 'post_class_summary_questions' table
    question = post_class_summary_db.retrieve_question(min_r_q_id[1])
    #send question to the user.
    update.message.reply_text(question[0])
    #return a status 
    status_code = min_r_q_id[0]-1
    return status_code



"""This method is triggered after the user send the answers"""
def receive_answer_send_rest_questions(bot,update):
    #insert information into 'post_class_summary_answer' table.
        #retrieve smu_email_id, group_id by using chat_id.
    chat_id = update.message.chat.id    
    smu_email_id_gid = post_class_summary_db.retrieve_smu_email_id_group_id(chat_id)
        #retrieve question_id from 'left_post_class_question' table.
    row_qid = post_class_summary_db.retrieve_minrow_question_id(smu_email_id_gid[0])
        #retrieve question from 'post_class_summary_questions' table.
    question_hist = post_class_summary_db.retrieve_question(row_qid[1])
        # get answer from user input.
    answer = update.message.text
    #insert
    post_class_summary_db.insert_post_class_answers(smu_email_id_gid[0], row_qid[1], question_hist[0], answer, smu_email_id_gid[1])
    #retrieve the cur_week(trust professor) to update the week.
    cur_week = post_class_summary_db.retrieve_cur_week()   
    post_class_summary_db.update_week_db(smu_email_id_gid[0], cur_week)
    #delete the min entry in 'left_post_class_question' table. 
    post_class_summary_db.delete_min_row_qid(smu_email_id_gid[0], row_qid[0])
    #retrieve the next min row_num and question_id from 'left_post_class_question' table for a particular student.
        #retrieve min_row_num
    new_min_row = post_class_summary_db.retrieve_min_row(smu_email_id_gid[0])
    
    if new_min_row[0] is None:
        reply_keyboard = [['week1', 'week2', 'week3','week4'],
                          ['week5', 'week6', 'week7','week9'],
                          ['week10', 'week11', 'week12','week13']]
         
        update.message.reply_text(
            'Hi! Let me know the current week! ',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)) 
        states_code = row_qid[0]
        #print ("this is %s" % states_code)
        return states_code      
        
    else:
        # retrieve the q_id from 'left_post_class_question' table.
        new_q_id = post_class_summary_db.retrieve_q_id(smu_email_id_gid[0], new_min_row[0])
        # retrieve the question by q_id from 'post_class_summary_questions' table
        new_question = post_class_summary_db.retrieve_question(new_q_id[0])
        update.message.reply_text(new_question[0])
        
        states_code = new_min_row[0]-1
        #print ("this is %s" % states_code)
        return states_code



"""This method handles week updates"""    
def update_week(bot,update):
    #chat_id
    chat_id = update.message.chat.id
    #retrieve student smu_email_id by chat_id   
    smu_em_id = post_class_summary_db.retrieve_smu_email_id(chat_id)
    #week
    week = update.message.text
    week_num = week.split("k",1)[1] 
    #print(week_num)
    #retrieve current week
    cur_week_prof = post_class_summary_db.retrieve_cur_week()    
    #update table 'post_class_summary_answers' using week = 20
    post_class_summary_db.update_all_week_db(smu_em_id,week_num,cur_week_prof)
    #reply and end conversation.
    update.message.reply_text("Your response has been successfully recorded!")
    return ConversationHandler.END    

    



         
      