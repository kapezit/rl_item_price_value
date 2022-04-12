from cgi import print_environ_usage
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json
import os
import mysql.connector
from mysql.connector import errorcode


##################################
#soup the item page
##################################


def base_url(iid, paintid):
    """Action: Create the url. Requires: itemid as well as paintid."""
    return "https://rl.insider.gg/pc/{}/{}".format(iid, paintid)


def get_page(url):
    """Action: Parse html content with bs4. Requires: url as the parameter."""
    result = requests.get(url)
    return BeautifulSoup(result.content, 'html.parser')



#souping = get_page(base_url(4522,2))

#testing - input manually for testing souping functions
#this should later become part of a parent loop that gets id (249 ids per batch), then loops for each color
#one with million in price - 32,0 
#normal one - 23,1
#min num in the hundreds and max num in the thousands - 3854,8
#no price yet - 1904,8

#4284,0  fennec, many times in shop
#4522,2 not in the item shop
#4549,0  one time in the shop





############################################################
#functions for the basic info - item name / paint
############################################################


def soup_name_paint(souping):
    '''Soup scripts, only look for the script with itemData content, strip it of its js elements in order to read it as json/dictionary'''
    
    scripts = souping.findAll('script')
    lst_scripts = [n for n in scripts]

    for script in lst_scripts:
        if "var itemData" in str(script.contents):
            item_data = (str(script.contents).split("\\n")[2])

    item_data_js = item_data[23:-1]

    item_data_dict = json.loads(item_data_js)

    return {"item name":item_data_dict["itemName"],"item paint":item_data_dict["itemColor"]}




# item_basics = soup_name_paint(souping)
# item_basics["item name"]
# item_basics["item paint"]



##################################
#functions for the item price - min and max
##################################

def soup_price_pc_tag(souping_page):
    """Action: find the first 'matrixRow0', append contents, return the second tag. Page not found return should end loop, go to parent"""
    price_pc = []
    try:
        for tags in souping_page.find(id = "matrixRow0"):
            price_pc.append(tags.contents)
    except TypeError:
        return("Not found.")
    else:
        return price_pc[1]


#print(soup_price_pc_tag(souping))



def clean_price_tag(soup_price_pc_tag):
    """Action: convert list to str to then split, get num or dashes, return only needed characters. If ["0","0"], go to parent"""
    price_value_text = str(soup_price_pc_tag)
    price_values = []
    
    if "-" not in price_value_text:
        return [['0'],['0']]
    else:
        try:
            for char in price_value_text:
                if char.isdigit() or char in ["-",".","m","k"]:
                    price_values.append(char)
        except ValueError:
            return [['0'],['0']]
        else:
            price_values = price_values[:price_values.index("-")], price_values[price_values.index("-") - (len(price_values)-1):]
            return price_values 


#print(clean_price_tag(soup_price_pc_tag(souping)))



def resolve_price(clean_range):
    """Action: creating a dictionary for price values and resolving decimals with k and m symbols"""
        
    price_dict = {"minp":0, "maxp":0}
    k_multiplier = 1000
    m_multiplier = 1000000

    if "k" in clean_range[1]:
        clean_range[1].remove("k")
        price_dict["maxp"] = float("".join(clean_range[1])) * k_multiplier

        if "k" not in clean_range[0]:
            price_dict["minp"] = float("".join(clean_range[0])) * k_multiplier

        elif "k" in clean_range[0]:
            price_dict["minp"] = float("".join(clean_range[0])) * k_multiplier
        else:
            price_dict["minp"] = float("".join(clean_range[0]))
    
    elif "m" in clean_range[1]:
        clean_range[1].remove("m")
        price_dict["maxp"] = float("".join(clean_range[1])) * m_multiplier

        if "m" in clean_range[0]:
            price_dict["minp"] = float("".join(clean_range[0])) * m_multiplier

        elif "k" in clean_range[0]:
            price_dict["minp"] = float("".join(clean_range[0])) * k_multiplier

        else:
            price_dict["minp"] = float("".join(clean_range[0])) * m_multiplier
    
    else:
        price_dict["maxp"] = float("".join(clean_range[1]))
        price_dict["minp"] = float("".join(clean_range[0]))


    return price_dict

#print(resolve_price((['1','0'],['1','1'])))
#print(resolve_price(clean_price_tag(soup_price_pc_tag(souping))))



# price_pair = resolve_price(clean_price_tag(soup_price_pc_tag(souping)))
# price_min = price_pair['minp']
# price_max = price_pair['maxp']





############################################################
#functions for the right side column - Number of days in Shop
############################################################


def soup_item_shop_tag(souping):
    """Souping of the tags present with the item shop information on the right side column. Parent has 3 items, Title, Content, Link to Shop Rotation"""
    item_shop_pc = []
    
    try:
        for tags in souping.find(id = "itemShopContainer"):
            item_shop_pc.append(tags.contents)
    except TypeError:
        return("Page not found")

    else:
        return item_shop_pc




def dates_in_shop(soup_item_shop):
    """Isolating the second tag that has the Content. Returns the number of data tags in them or 0 when it has never been in the shop"""
    tags_with_data = soup_item_shop[1]
               
    if tags_with_data == ['This item has not been in the Item Shop yet.']:
        times_in_shop_value = 0
    else:
        times_in_shop_value = int(len(tags_with_data))


    return times_in_shop_value



#num_dates_in_shop = dates_in_shop(soup_item_shop_tag(souping))





####################################################################################
#functions for the right side column - If item has been in the shop, get the latest
####################################################################################


def recent_in_shop(soup_item_shop):
    """Only runs well if item has been in the shop. Getting the tag for the last time the item was in the in-game shop."""
    tags_with_data = soup_item_shop[1]
        
    times_in_shop_v = int(len(tags_with_data))

    last_time_shop_i = times_in_shop_v - 1

    recent_tag = tags_with_data[last_time_shop_i]

    return recent_tag



def final_ingame_shop(last_time_shop_var):
    """Creating the dict with the last time in shop tag. This needs a variable that calls the recent_in_shop(). Error when item has never been in shop"""
    date_string = last_time_shop_var.contents[len(last_time_shop_var)-3].get_text()   
    date_value_datetime = datetime.strptime(date_string, '%b %d, %Y')
    date_value = date_value_datetime.date()
    
    cert_tag = str(last_time_shop_var.contents[len(last_time_shop_var)-2].get_text())
    
    price_tag = int(last_time_shop_var.contents[len(last_time_shop_var)-1].get_text())

    return {"recent date in shop":  date_value, "recent cert in shop": cert_tag, "recent price in shop": price_tag}




# info_last_date_shop = final_ingame_shop(recent_in_shop(soup_item_shop_tag(souping)))
# info_last_date_shop["recent date in shop"]
# info_last_date_shop["recent cert in shop"]
# info_last_date_shop["recent price in shop"]




############################################################
#functions for the right side column - Item Info
############################################################


def soup_item_info_tag(souping):
    """Souping of the tags present with the item info container - right side column. Need souping var. Two items in the list. Returning without the header."""
    item_info_pc = []
    
    try:
        for tags in souping.find(id = "itemInfoContainer"):
            item_info_pc.append(tags.contents)
    except TypeError:
        return("Page not found")

    else:
        return item_info_pc[1]





def item_info_content(item_info_tag_var):
    """Getting the content in the info tag - creating dictionary for the contents. Needs soup_intem_info_tag() or the variable created for it"""
            
    rarity_value = [child for child in item_info_tag_var[0]]
    type_value = [child for child in item_info_tag_var[1]]
    series_value = [child for child in item_info_tag_var[2]]
    release_value = [child for child in item_info_tag_var[3]]
    paints_value = [child for child in item_info_tag_var[4]]
    blueprint_value = [child for child in item_info_tag_var[6]]

    
    s_series_value = len(series_value) - 1
    if s_series_value == 1 and len(series_value[1].get_text()) < 5 :
        s_series_value = 0
  

    s_release_value = release_value[1].get_text()
    if "(" in s_release_value:
        split_release_value = s_release_value.split("(")
        s_release_value= split_release_value[0]
    s_release_value_datetime = datetime.strptime(s_release_value, '%b %d, %Y')
    s_release_value = s_release_value_datetime.date()

         
    return {"rarity":rarity_value[1].get_text(), "type":type_value[1].get_text(), "number of series":s_series_value,"release date":s_release_value,"paints available":paints_value[1].get_text(),"has blueprint":blueprint_value[1].get_text()}



# info_right_col = item_info_content(soup_item_info_tag(souping))
# info_right_col["rarity"]
# info_right_col["type"]
# info_right_col["number of series"]
# info_right_col["release date"]
# info_right_col["paints available"]
# info_right_col["has blueprint"]





##################################
#Batch scanning - user input
##################################


def user_input_per_batch():
    """Action: getting user input to know which batch is going to be scanned"""
    while True:
        try:
            user_input=int(input("Input the batch number between 1-30 :  "))
        except ValueError:
            print("Wrong input, try again.")

        else:
            if user_input > 0 and user_input < 31:
                print("It's working. It's better to do the batch # randomly. Scanning batch number {}...".format(user_input))
                return user_input
            else:
                print("The number needs to be between 1 and 30.")



def resolve_batch_num(user_input_var):
    """Action: take the result from user input and resolve it with a list of item ids that will be scanned"""
    start_iid = 1           #first item id num
    end_iid = 7470          #last item id num - will probably change once the amount of items past this threshold.
    batch_size = 249        #how many items per batch
    scan_pairs = []         #list of possible batches (from 0 to 29 - 249 items in each - for user is 1-30)
    batch_nums = []          
    
    for num in range(start_iid,end_iid,batch_size):
        scan_pairs.append([num,num+249])
        
    for iid in range(scan_pairs[user_input_var - 1][0],scan_pairs[user_input_var - 1][1]):
        batch_nums.append(iid)
    return batch_nums



#iids_list = resolve_batch_num(user_input_per_batch())




##################################
#Connecting to SQL
##################################


def get_env_var():
    '''getting credentials from env variable in the os'''
    USER = os.getenv("MYSQLDB_USER")
    PASSWORD = os.getenv("MYSQLDB_PSW")
    HOST = os.getenv("MYSQLDB_HOST")
    DATABASE = 'sys'
    return USER, PASSWORD, HOST, DATABASE

user_var = get_env_var()[0]
psw_var = get_env_var()[1]
host_var = get_env_var()[2]
datab_var = get_env_var()[3]



#def sql_connect(env0, env1, env2, env3):
 #   '''connecting to SQL server'''
#    cnx = mysql.connector.connect(user = env0, password = env1, host = env2, database = env3)
 #   return cnx


#def sql_insert(col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15 ):
    #query = "INSERT INTO rl_items_t1(iid_key, name, paint, type, rarity, num_series, release_date, paints_avail, blueprint, price_max, price_min, num_days_in_shop, last_date_in_shop, last_cert_in_shop, last_price_in_shop)    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)"
    #data = [(col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15)]
   # return query, data



col1="col1id06"
col2="col2"
col3="col3"
col4="col4"
col5="col5"
col6= 10
col7= "July 4, 2021"
col8="col8"
col9= "col9"
col10= 1000000.5
col11= 100000000.5
col12= 4
col13= "Jan 6, 2022"
col14= "col14"
col15= 100000





try:
    cnx = mysql.connector.connect(user= user_var, password= psw_var,
                                host= host_var,
                                database= datab_var)
    cursor = cnx.cursor()
    query = "INSERT INTO rl_items_t1(iid_key, name, paint, type, rarity, num_series, release_date, paints_avail, blueprint, price_min, price_max, num_times_in_shop, last_date_in_shop, last_cert_in_shop, last_price_in_shop)    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)"
    data = [(col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15)]
    cursor.executemany(query,data)
    cnx.commit()

except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
    cnx.close()







#def sql_cursor(cnx_var):
 #   cursor = cnx_var.cursor()
 #   return cursor

#cursor_var = sql_cursor(sql_connect(get_env_var()[0],get_env_var()[1],get_env_var()[2],get_env_var()[3]))












#insert_in_table = sql_insert(cursor_var, "col1","col2", "col3", "col4", "col5","col6","col7", "col8", "col9", "col10", "col11","col12", "col13", "col14", "col15")
#sql_connect(get_env_var()[0],get_env_var()[1],get_env_var()[2],get_env_var()[3]).commit()




