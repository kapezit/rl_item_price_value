from cgi import print_environ_usage
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json



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



souping = get_page(base_url(4522,2))
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




item_basics = soup_name_paint(souping)

item_basics["item name"]
item_basics["item paint"]



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
        return("Page not found.")
    else:
        return price_pc[1]


#print(soup_price_pc_tag(souping))



def clean_price_tag(soup_price_pc_tag):
    """Action: convert list to str to then split, get num or dashes, return only needed characters. If ["0","0"], go to parent"""
    #soup_price_pc_tag = soup_price_pc_tag(souping)
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


def get_price_min():
    """Action: getting min price values from dict"""
    return resolve_price(clean_price_tag(soup_price_pc_tag(souping)))['minp']
    
def get_price_max():
    """Action: getting min price values from dict"""
    return resolve_price(clean_price_tag(soup_price_pc_tag(souping)))['maxp']


price_pair = resolve_price(clean_price_tag(soup_price_pc_tag(souping)))
price_min = price_pair['minp']
price_max = price_pair['maxp']

print(get_price_min(), get_price_max())




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



num_dates_in_shop = dates_in_shop(soup_item_shop_tag(souping))
print(num_dates_in_shop)



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



info_right_col = item_info_content(soup_item_info_tag(souping))

info_right_col["rarity"]
info_right_col["type"]
info_right_col["number of series"]
info_right_col["release date"]
info_right_col["paints available"]
info_right_col["has blueprint"]











##################################
#souping inputs iids and paint (in-progress)
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
    
    for i in range(start_iid,end_iid,batch_size):
        scan_pairs.append([i,i+249])
        
    for iid in range(scan_pairs[user_input_var - 1][0],scan_pairs[user_input_var - 1][1]):
        batch_nums.append(iid)
    return(batch_nums)




# user_input_result = user_input_per_batch()
# iids_list = resolve_batch_num(user_input_result)

paintids_dict = {"default":0,"crimson":1,"lime":2,"black":3,"skyblue":4,"cobalt":5,"burntsienna":6,"forestgreen":7,"purple":8,"pink":9,"orange":10,"grey":11,"titaniumwhite":12,"saffron":13}

