#-------------------------------------------------------------------------
# AUTHOR: Lokaranjan Munta
# FILENAME: parser.py
# SPECIFICATION: The program parses the faculty members' name, title, office, phone, email, and website from the
# target HTML code stored in MongoDB. The data is then persisted into the professors MongoDB collection.
# FOR: CS 4250- Assignment #3
# TIME SPENT: 1.5 hours
#-----------------------------------------------------------*/

# Importing Python libraries
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient


def connectDataBase():
    # Create a database connection object using pymongo
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Assignment3"]
    return db


def parser(html):
    # Create BeautifulSoup object with HTML
    bs = BeautifulSoup(html, 'html.parser')
    faculty = []

    # Find section with faculty information
    section = bs.find('section', {'class': 'text-images'})

    if section:
        # Go through each h2 tag (has name)
        for h2tag in section.find_all('h2'):
            # Find the next p tag after h2, has rest of information
            ptag = h2tag.find_next('p')

            if ptag:
                # To store current faculty info
                eachFacultyInformation = {}

                # Name
                # Get name from h2 tag and clean
                eachFacultyInformation['name'] = h2tag.get_text().strip()

                # Title
                # Find "Title" inside the ptag
                titleMarker = ptag.find('strong', text=re.compile('Title'))
                if titleMarker:
                    # next_sibling gets text after titleMarker, clean
                    # Ex: <strong>Title<strong/>: Professor --> : Professor --> Professor
                    title = titleMarker.next_sibling.strip(':').strip()
                    if title:
                        eachFacultyInformation['title'] = title

                # Office
                # Find "Office" inside the ptag
                officeMarker = ptag.find('strong', text=re.compile('Office'))
                if officeMarker:
                    # next_sibling gets text after officeMarker, clean
                    # Ex: <strong>Office</strong>: 8-45 --> : 8-45 --> 8-45
                    office = officeMarker.next_sibling.strip(':').strip()
                    if office:
                        eachFacultyInformation['office'] = office

                # Phone
                # Find "Phone" inside the ptag
                phoneMarker = ptag.find('strong', text=re.compile('Phone'))
                if phoneMarker:
                    # next_sibling gets text after phoneMarker, clean
                    # Ex: <strong>Phone</strong>: (909) 869-3449 --> : (909) 869-3449 --> (909) 869-3449
                    phone = phoneMarker.next_sibling.strip(':').strip()
                    if phone:
                        eachFacultyInformation['phone'] = phone

                # Email
                # Find first a tag
                emailTag = ptag.find('a')
                if emailTag:
                    # get_text() gets email address text
                    email = emailTag.get_text()
                    if email:
                        eachFacultyInformation['email'] = email

                # Website
                # Find a tag that comes after emailTag which has the website
                websiteTag = emailTag.find_next_sibling('a')
                if websiteTag:
                    # ['href'] gets the URL
                    eachFacultyInformation['website'] = websiteTag['href']

                # Add completed faculty to list
                faculty.append(eachFacultyInformation)

    return faculty


def main():
    # Connect to db and find the target page in the pages collection
    db = connectDataBase()
    target_page = db.pages.find_one({"target": True})

    if target_page:
        # Parse the HTML for faculty information
        faculty = parser(target_page['html'])
        if faculty:
            # Insert information into professors collection
            db.professors.insert_many(faculty)

            # Printing values inserted into professors collection
            print(f"Inserted {len(faculty)} Permanent Faculty into professors collection")
            professors = db.professors.find({}, {'_id': 0})
            for professor in professors:
                for field, value in professor.items():
                    print(f"{field.title()}: {value}")
                print()
    else:
        print(f"Target page not found in database")


if __name__ == '__main__':
    main()
