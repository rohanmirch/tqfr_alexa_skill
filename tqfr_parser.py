from botocore.vendored import requests
from bs4 import BeautifulSoup

def login():  
    ''' Returns a session object that is logged in to access.caltech.edu'''
    #t1 = time.time()
    post_login_url= "https://access.caltech.edu/auth/login_handler?came_from=https://access.caltech.edu/tqfr/reports/list_surveys&login_counter=0"   
    login_info = {
        "login": "rmirchan",
        "password": "59521071RMirch"
    }

    session = requests.Session()
    #Need to send get request to access to get 
    n = session.get(post_login_url)
    soup = BeautifulSoup(n.text, 'html.parser')
    login_info["lt"] = soup.find(id = "lt")['value'];
    #Login to access and get reidrected to TQFR Home page
    p = session.post(post_login_url, data=login_info, verify = True)
    return session

def dump_login_session():
    # Code to dump login session
    pickle_out = open("~/login_session.pickle","wb")
    pickle.dump(login(), pickle_out)
    pickle_out.close()
    
def load_session():
    '''Loads pickled login session. If fail, then re-dump new login session'''
    try:
        pickle_in = open("~/login_session.pickle","rb")
        s = pickle.load(pickle_in)
        return s
    except:
        dump_login_session()
        load_session()

def search_class(session, course_div, course_num):
    url_prefix = "https://access.caltech.edu"
    search_url = "https://access.caltech.edu/tqfr/reports/search"
    
    #t1 = time.time()
    course = course_div + " " + course_num
    class_search_page = session.post(search_url, {"search": course})
    soup = BeautifulSoup(class_search_page.text, 'html.parser')
    tab = soup.find("table", {"class":"tablediv"}).find_all("tr")

    rating = 0
    #Get link to class page from search table
    class_link = "NAN"
    for row in tab:
        cells = row.find_all("td")
        name = cells[0].get_text().lower()
        if course_div.lower() in name and course_num.lower() in name:
            # Get appropriate link
            class_link = url_prefix + row.find("a").get('href')
            # Get rating value
            entries = row.find_all("td")
            rating = float(entries[-1].get_text().split(" ")[0])
            break

    if class_link == "NAN":
        raise Exception("not a valid class search")

    #t2 = time.time() - t1
    #print("search_time: ", t2, " seconds")
    
    #Now send get request to class link page
    course_page = session.get(class_link)
    
    soup = BeautifulSoup(course_page.text, 'html.parser')
    course_title = soup.find("h1", {"class":"survey_title clearfix"}).get_text()
    course_name = soup.find("h1", {"class":"offering_title"}).get_text()

    tables = soup.find_all("table")

    all_tables = []
    #Workload - table 3, Expected grade - Table 5
    params = ["Workload", "Expected grade"]
    my_tables = [3,5]
    final_params = []
    for t in my_tables:
        table = tables[t]
        #Only need top level of numbers
        l = []
        table_rows = table.find_all('tr')[:2]

        for tr in table_rows:
            #print(tr.get_text())
            headers = tr.find_all('th')[1:]
            if headers != []:
                l.append([th.text for th in headers])
                continue
            td = tr.find_all('td')[1:]
            l.append([float(tr.text[:-1]) for tr in td])
            l = [(l[0][i], l[1][i]) for i in range(len(l[1]))]
            l.sort(key = lambda x: x[1])
        all_tables.append(l)
        final_params.append(l[-1])

    #t3 = time.time()-t2-t1
    #print("parse_time: ", t3, " seconds")

    return [course_title, course_name, rating] + final_params


#Manually load the login session at the beginning of each application session
my_session = login()


def get_response_string(course_div, course_num):
    #offering, title, rating, workload, grade = search_class(load_session(), course_div, course_num)
    offering, title, rating, workload, grade = search_class(my_session, course_div, course_num)
    response = "{} was rated {} out of 5. ".format(title, rating)
    response += "{} percent of students said workload was {}. ".format(int(workload[1]), workload[0])
    response += "{} percent of students recevied a grade of {}. ".format(int(grade[1]), grade[0])
    return response
        
