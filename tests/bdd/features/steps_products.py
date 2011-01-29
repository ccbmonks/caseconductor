'''

Created on Jan 28, 2011
@author: camerondawson
'''
from lettuce import *
from step_helper import *
from step_helper import jstr, add_params

'''
######################################################################

                     PRODUCT STEPS

######################################################################
'''

@step(u'create a new product with (that name|name "(.*)")')
def create_product_with_name_foo(step, stored, name):
    name = get_stored_or_store_product_name(stored, name)
    
    headers = {'Authorization': get_auth_header(),
               'content-type': "application/x-www-form-urlencoded"
               }
               
    post_payload = {"companyid": 9,
                    "name": name,
                    "description": "Lettuce Product Description"
                   }
    
    world.conn.request("POST", add_params(world.path_products), 
                       urllib.urlencode(post_payload, doseq=True), 
                       headers)

    response = world.conn.getresponse()
    verify_status(200, response, "Create new user")



@step(u'product with (that name|name "(.*)") (exists|does not exist)')
def check_user_foo_existence(step, stored, name, existence):
    name = get_stored_or_store_product_name(stored, name)
    search_and_verify_existence(step, world.path_products, 
                    {"name": name}, 
                    "product", existence)


@step(u'add environment "(.*)" to product "(.*)"')
def add_environment_foo_to_product_bar(step, environment, product):
    # this takes 2 requests.  
    #    1: get the id of this product
    #    2: add the environment to the product
    
    # fetch the product's resource identity
    product_id, version = get_product_resid(product)
    
    post_payload = {"name": "Walter's Lab"}
    
    headers = {'content-Type':'text/xml',
               'Content-Length': "%d" % len(post_payload) }

    world.conn.request("POST", add_params(world.path_products + product_id + "/environments", {"originalVersionId": version}), "", headers)
    world.conn.send(post_payload)
    response = world.conn.getresponse()
    verify_status(200, response, "post new environment to product")

@step(u'remove environment "(.*)" from product "(.*)"')
def remove_environment_from_product(step, environment, product):
    # fetch the product's resource identity
    product_id, version = get_product_resid(product)
    environment_id = get_environment_resid(environment)
    
    world.conn.request("DELETE", 
                       add_params(world.path_products + product_id + "/environments/" + environment_id, 
                                  {"originalVersionId": version}))
    response = world.conn.getresponse()
    verify_status(200, response, "delete new environment from product")

@step(u'product "(.*)" (has|does not have) environment "(.*)"')
def product_foo_has_environment_bar(step, product, haveness, environment):
    # fetch the product's resource identity
    product_id, version = get_product_resid(product)
    
    
#    if haveness.strip() == "does not have":

    world.conn.request("GET", add_params(world.path_products + product_id + "/environments"))
    response = world.conn.getresponse()
    verify_status(200, response, "Fetched environments")

    jsonList = get_resp_list(response, "environment")

    found = False
    for item in jsonList:
        assert isinstance(item, dict), "expected a list of dicts in:\n" + jstr(jsonList)
        if (item.get(ns("name")) == environment):
            found = True
    
    shouldFind = (haveness == "has")
    assert_equal(found, shouldFind, "looking for environment of " + environment)








def get_stored_or_store_product_name(stored, name):
    '''
        Help figure out if the test writer wants to use a stored name from a previous step, or if
        the name was passed in explicitly. 
        
        If they refer to a user as 'that name' rather than 'name "foo bar"' then it uses
        the stored one.  Otherwise, the explicit name passed in.  
    '''
    if (stored.strip() == "that name"):
        name = world.product_name
    else:
        world.product_name = name
    return name