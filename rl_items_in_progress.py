from bs4 import BeautifulSoup
import requests


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








##################################
#soup the item page
##################################


def base_url(iid, paintid):
    """Action: Create the url. Requires: itemid as well as paintid. Default (no paint) = 0"""
    return "https://rl.insider.gg/pc/{}/{}".format(iid, paintid)


def get_page(url):
    """Action: Parse html content with bs4. Requires: url as the parameter."""
    result = requests.get(url)
    return BeautifulSoup(result.content, 'html.parser')



souping = get_page(base_url(32,0))
#testing - input manually for testing souping functions
#this should later become part of a parent loop that gets id (249 ids per batch), then loops for each color
#one with million in price - 32,0 
#normal one - 23,1
#min num in the hundreds and max num in the thousands - 3854,8
#no price yet - 1904,8





##################################
#functions for the item price
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


print(get_price_min(), get_price_max())




#################