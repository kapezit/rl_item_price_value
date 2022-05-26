from datetime import datetime
from bs4 import BeautifulSoup
import json
import os
import mysql.connector
from mysql.connector import errorcode
from playwright.sync_api import sync_playwright


##################################
#soup the item page
##################################


def base_url(iid, paintid):
    """Action: Create the url. Requires: itemid as well as paintid."""
    return "https://rl.insider.gg/pc/{}/{}".format(iid, paintid)


def get_page(url):
    """Action: Parse html content with bs4. Requires: url as the parameter."""
    #result = requests.get(url, timeout=12)     ---- used requests first but was not working, switched to playwright to use a "browser"
    #return BeautifulSoup(result.content, 'html.parser')

    for i in range(3):
        try:
            # To get around it
            # # maybe need to only launch this once and then just do requests
            with sync_playwright() as p:
                # Webkit is fastest to start
                browser = p.webkit.launch(headless=True)
                page = browser.new_page()
                #response = page.goto(url)
                webdata = page.content()
                    
            return BeautifulSoup(webdata, 'html.parser')

        except Exception as e:
            print(e)
            print("barfing on " + url)


###### Variables for loop and tables ######


# souping = get_page(base_url(itemid,paintid))

#these are just test values:
#one with million in price - 32,0 
#normal one - 23,1
#min num in the hundreds and max num in the thousands - 3854,8
#no price yet - 1904,8
#4284,0  fennec, many times in shop
#4522,2 not in the item shop
#4549,0  one time in the shop




############################################################
#functions for the basic info - item name / paint  [needs to be fixed before running it again]
############################################################


def soup_name_paint(souping):
    '''Soup scripts, only look for the script with itemData content, strip it of its js elements in order to read it as json/dictionary'''
    
    scripts = souping.findAll('script')
    lst_scripts = [n for n in scripts]

    for script in lst_scripts:
        if "var itemData" in str(script.contents):
            item_data = (str(script.contents).split("\\n")[2])

    item_data_js = item_data[23:-1]
    item_data_js_fix = item_data_js.replace("\\","-")
    item_data_dict = json.loads(item_data_js_fix)

    #name fix, name should include any variety, the code above doesnt do that - any variety also includes Paint (not the best but its working for now)
    #fix how to remove Paint from the name
    title_tag = souping.title.string
    name_of_item = title_tag.split(" on PC")[0].strip()

    return {"item name":name_of_item,"item paint":item_data_dict["itemColor"]}




###### Variables for loop and tables ######

#souping = get_page("https://rl.insider.gg/pc/1052/0")

# item_basics = soup_name_paint(souping)
# # i_name = item_basics["item name"]
# # i_paint =item_basics["item paint"]
# # print(i_name)
# # print(i_paint)
# print(item_basics)





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


# print(soup_price_pc_tag(souping))



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


###### Variables for loop and tables ######
# price_pair = resolve_price(clean_price_tag(soup_price_pc_tag(souping)))
# i_price_min = price_pair['minp']
# i_price_max = price_pair['maxp']






############################################################
#functions for the right side column - Number of days in Shop
############################################################


def soup_item_shop_tag(souping):
    """Souping of the tags present with the item shop information on the right side column. Parent has 3 items, Title, Content, Link to Shop Rotation"""
    item_shop_pc = []
    
    try:
        for each in souping.find(id = "itemShopContainer").findAll("tr"):
            item_shop_pc.append(each.contents)

    except TypeError:
        return("Page not found")

    else:
        return item_shop_pc

#print(soup_item_shop_tag(souping))



def dates_in_shop(soup_item_shop):
    """Isolating the second tag that has the Content within a list. Returns the number of data tags in them is empty (no tr's from above) it has never been in the shop"""
     
    if soup_item_shop == []:
        times_in_shop_value = 0
    else:
        times_in_shop_value = int(len(soup_item_shop))
 
    return times_in_shop_value

#print(dates_in_shop(soup_item_shop_tag(souping)))



###### Variables for loop and tables ######
#i_times_in_shop = dates_in_shop(soup_item_shop_tag(souping))

#print(i_times_in_shop)



####################################################################################
#functions for the right side column - If item has been in the shop, get the latest
####################################################################################


def recent_in_shop(soup_item_shop):
    """Only runs well if item has been in the shop. Getting the tag for the last time the item was in the in-game shop."""

    times_in_shop_v = int(len(soup_item_shop))
    last_time_shop_i = times_in_shop_v - 1
    recent_tag = soup_item_shop[last_time_shop_i]
    return recent_tag

#print(recent_in_shop(soup_item_shop_tag(souping)))




def final_ingame_shop(last_time_shop_var):
    """Creating the dict with the last time in shop tag. This needs a variable that calls the recent_in_shop(). Error when item has never been in shop"""
    
    date_string = last_time_shop_var[len(last_time_shop_var)-3].get_text()   
    date_value_datetime = datetime.strptime(date_string, '%b %d, %Y')
    date_value = date_value_datetime.date()
    
    cert_tag = str(last_time_shop_var[len(last_time_shop_var)-2].get_text())
    
    price_tag = int(last_time_shop_var[len(last_time_shop_var)-1].get_text())

    return {"recent date in shop":  date_value, "recent cert in shop": cert_tag, "recent price in shop": price_tag}


#print(final_ingame_shop(recent_in_shop(soup_item_shop_tag(souping))))




############################################################
#functions for the right side column - Item Info
############################################################


def soup_item_info_tag(souping):
    """Souping of the tags present with the item info container - right side column. Need souping var. Two items in the list. Returning without the header."""
    item_info_pc = []
    
    try:
        item_info_pc = souping.find(id = "itemInfoContainer").findAll("tr")

    except TypeError:
        return("Page not found")

    else:
        return item_info_pc





def item_info_content(item_info_tag_var):
    """Getting the content in the info tag - creating dictionary for the contents. Dif order for Gift Packs, diff len of categories. Needs soup_intem_info_tag() or the variable created for it"""

    rarity_value = [child for child in item_info_tag_var[0]]
    type_value = [child for child in item_info_tag_var[1]]
    
    
    if len(item_info_tag_var) == 6:
        series_value = [child for child in item_info_tag_var[2]]
        release_value = "none"
        paints_value = [child for child in item_info_tag_var[3]]
        blueprint_value = [child for child in item_info_tag_var[5]]
    
    elif len(item_info_tag_var) == 7:
        if type_value[1].get_text() == "Gift Pack":
            series_value = ["none"]
            release_value = [child for child in item_info_tag_var[2]]

        else:
            series_value = [child for child in item_info_tag_var[2]]
            release_value = [child for child in item_info_tag_var[3]]
    
        paints_value = [child for child in item_info_tag_var[4]]
        blueprint_value = [child for child in item_info_tag_var[6]]

    elif len(item_info_tag_var) ==8:
        series_value = [child for child in item_info_tag_var[2]]
        release_value = [child for child in item_info_tag_var[3]]
        paints_value = [child for child in item_info_tag_var[5]]
        blueprint_value = [child for child in item_info_tag_var[7]]

    


    s_series_value = len(series_value) - 1
    if s_series_value == 1 and len(series_value[1].get_text()) < 5 :
        s_series_value = 0
  
    
    if "none" in release_value:
        s_release_value = "none"
    else:
        s_release_value = release_value[1].get_text()
        
        if "(" in s_release_value:
            split_release_value = s_release_value.split("(")
            s_release_value= split_release_value[0]
    
        s_release_value_datetime = datetime.strptime(s_release_value, '%b %d, %Y')
        s_release_value = s_release_value_datetime.date()


         
    return {"rarity":rarity_value[1].get_text(), "type":type_value[1].get_text(), "number of series":s_series_value,"release date":s_release_value,"paints available":paints_value[1].get_text(),"has blueprint":blueprint_value[1].get_text()}



###### Variables for loop and tables ######
# souping = get_page("https://rl.insider.gg/pc/2279/0")


# info_right_col = item_info_content(soup_item_info_tag(souping))

# i_rarity = info_right_col["rarity"]
# i_type = info_right_col["type"]
# i_series = info_right_col["number of series"]
# i_release = info_right_col["release date"]
# i_pavail = info_right_col["paints available"]
# i_blue = info_right_col["has blueprint"]

# print(i_type)
# print(i_rarity)
# print(i_series)
# print(i_release)
# print(i_pavail)
# print(i_blue)


##################################
#Connecting to DB
##################################


def get_env_var():
    '''getting credentials from env variable in the os'''
    c1u = os.getenv("MYSQLDB_USER")
    c2p = os.getenv("MYSQLDB_PSW")
    c3h = os.getenv("MYSQLDB_HOST")
    c4d = 'sys'
    return c1u, c2p, c3h, c4d

user_var = get_env_var()[0]
psw_var = get_env_var()[1]
host_var = get_env_var()[2]
datab_var = get_env_var()[3]

##################################



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




# ##################################
# #Main program
# ##################################

iids_list = resolve_batch_num(user_input_per_batch())

#below is the list of items that needed to be rescanned
#iids_list = [1052,1056,1059,1060,1062,1066,1096,1099,1104,1123,1126,1131,1132,1365,1385,1423,1443,1447,1449,1502,1613,1619,1628,1716,1742,1743,2383,2385,2392,2693,2732,2819,2952,2954,2969,2970,3012,3025,3027,3144,3310,3314,3317,3322,3338,3365,3369,3438,3459,3515,3620,3691,3692,3693,3698,3699,3852,3878,3897,3898,3899,3900,3901,3988,3997,4000,4001,4032,4057,4112,4113,4132,4181,4183,4201,4202,4203,4217,4222,4245,4261,4269,4294,4296,4313,4314,4326,4335,4347,4358,4370,4371,4382,4386,4406,4426,4445,4446,4447,4457,4459,4481,4493,4585,4640,4652,4690,4698,4712,4721,4726,4747,4748,4764,4777,4779,4787,4839,4849,4932,494,4962,4997,5069,5079,5148,5170,5177,5178,5179,5180,5182,5184,5218,5267,5304,5318,5337,5341,5345,5348,5362,5449,5457,5496,5562,5584,5593,5618,5619,5628,5666,5746,5749,5751,5814,5816,5846,5881,5924,5966,5972,5985,6007,6019,6130,6193,6201,6221,6242,6377,6378,6493,6781,6806,6845,6864,6893,6944,6984,7003,7049,7057,7078,7081,7087,7185,7220,7333,7334,7357,7364,7378,7395,7402,7441,7442,7443,7448,7449,7464]

for iids in iids_list:
    not_found_count = 0
    print(iids)

    for ipaints in range(14):
        itemid = iids
        paintid = ipaints
        i_idkey = str(itemid) + "_"+ str(paintid)
        # print(i_idkey + " before soup")
              
        
        souping = get_page(base_url(itemid,paintid))


        if soup_price_pc_tag(souping) == "Not found.":
            not_found_count+=1
            if not_found_count == 6:
                # print("Not found +5 times")
                break
            else:
                continue
        else:
            item_basics = soup_name_paint(souping)
            i_name = item_basics["item name"]
            i_paint =item_basics["item paint"]
            # print(i_name)
            # print(i_paint)

            info_right_col = item_info_content(soup_item_info_tag(souping))
            i_rarity = info_right_col["rarity"]
            i_type = info_right_col["type"]
            i_series = info_right_col["number of series"]
            i_release = info_right_col["release date"]
            i_pavail = info_right_col["paints available"]
            i_blue = info_right_col["has blueprint"]
            # print(i_type)        
            # print(i_rarity)
            # print(i_series)
            # print(i_release)
            # print(i_pavail)
            # print(i_blue)

            price_pair = resolve_price(clean_price_tag(soup_price_pc_tag(souping)))
            i_price_min = price_pair['minp']
            i_price_max = price_pair['maxp']
            # print(i_price_min)
            # print(i_price_max)

            i_times_in_shop = dates_in_shop(soup_item_shop_tag(souping))
            # print(i_times_in_shop)

            if i_times_in_shop == 0:
                i_date_shop = "Never"
                i_cert_shop =  "Never"
                i_price_shop = 0

            else:
                info_last_date_shop = final_ingame_shop(recent_in_shop(soup_item_shop_tag(souping)))
                i_date_shop = info_last_date_shop["recent date in shop"]
                i_cert_shop =  info_last_date_shop["recent cert in shop"]
                i_price_shop = info_last_date_shop["recent price in shop"]

            # print(i_date_shop)
            # print(i_cert_shop)
            # print(i_price_shop)



            try:
                cnx = mysql.connector.connect(user= user_var, password= psw_var,
                                host= host_var,
                                database= datab_var)
                cursor = cnx.cursor()
                #insert into name_of_table(column names,...)   VALUES (%s,...)
                query = "INSERT INTO names_rl_items_t2(iid_key, name, paint, type, rarity, num_series, release_date, paints_avail, blueprint, price_min, price_max, num_times_in_shop, last_date_in_shop, last_cert_in_shop, last_price_in_shop)    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)"
                data = [(i_idkey, i_name, i_paint, i_type, i_rarity, i_series, i_release, i_pavail, i_blue, i_price_min, i_price_max, i_times_in_shop, i_date_shop, i_cert_shop, i_price_shop)]
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



        if i_pavail == "No":
            break

print("Program ended")