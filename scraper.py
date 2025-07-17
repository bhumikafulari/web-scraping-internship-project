import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5'
}

BASE_PAGE_URL = "https://www.listif.com/services/electrical-contractors/all?page="
BASE_DOMAIN = "https://www.listif.com"

# Function to decode Cloudflare protected email
def decode_cfemail(encoded_cfemail):
    r = int(encoded_cfemail[:2], 16)
    email = ''.join([chr(int(encoded_cfemail[i:i+2], 16) ^ r) for i in range(2, len(encoded_cfemail), 2)])
    return email

# Get all profile links from listing page
def get_contractor_links(page_url):
    response = requests.get(page_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    items = soup.find_all('div', class_='item item-row')
    links = []

    for item in items:
        a_tag = item.find('a', href=True)
        if a_tag:
            href = a_tag['href']
            full_url = href if href.startswith('http') else BASE_DOMAIN + href
            links.append(full_url)

    return links

# Scrape details from each profile
def scrape_contractor_details(profile_url):
    response = requests.get(profile_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Business Name
    business_name_tag = soup.find('div', attrs={'class': 'element'})
    business_name = ''
    if business_name_tag:
        h3 = business_name_tag.find('h3')
        if h3:
           business_name = h3.get_text(strip=True)


    # Address
    address_tag = soup.find('figure', itemprop='address')
    address = address_tag.get_text(separator=' ', strip=True) if address_tag else ''

    # Phones
    phone_elements = soup.find_all('span', itemprop='telephone')
    phones = [phone.text.strip() for phone in phone_elements]

    # Contact Person
    contact_person = ''
    for figure in soup.find_all('figure'):
        icon = figure.find('i')
        if icon and 'fa-user' in icon.get('class', []):
            # Get the next text after <i> tag (sibling could be tag or string)
            possible_name = icon.next_sibling
            if possible_name and isinstance(possible_name, str):
                contact_person = possible_name.strip()
            elif possible_name:
                contact_person = possible_name.get_text(strip=True)
            break


    # Email (decode Cloudflare protected one)
    email = ''
    for figure in soup.find_all('figure'):
        icon = figure.find('i')
        if icon and 'fa-envelope' in icon.get('class', []):
            span = figure.find('span', class_='__cf_email__')
            if span:
                encoded = span.get('data-cfemail')
                if encoded:
                    email = decode_cfemail(encoded)
                    break


    # Website
    globe_icon = soup.find('i', class_='fa fa-globe')

    # Find the parent <figure> tag and get the <a> tag inside it
    website = ''
    if globe_icon:
        figure = globe_icon.find_parent('figure')
        if figure:
            a_tag = figure.find('a', href=True)
            if a_tag:
               website = a_tag['href'].strip()

    # print("Website:", website if website else "Not found")



    print(f"Scraped: {business_name} | {contact_person} | {email}  | {website} | {phones}")

    return {
        'profile_url': profile_url,
        'business_name': business_name,
        'address': address,
        'phone_numbers': phones,
        'contact_person': contact_person,
        'email': email,
        'website': website
    }

# Main function to iterate pages and save data
def main():
    all_data = []
    total_pages = 250  # Change to scrape more pages


    for page_num in range(1,251):
        print(f"\nScraping page {page_num} of {total_pages}...")
        page_url = BASE_PAGE_URL + str(page_num)

        try:
            contractor_links = get_contractor_links(page_url)
        except Exception as e:
            print(f"❌ Failed to get contractor links on page {page_num}: {e}")
            continue

        for link in contractor_links:
            try:
                details = scrape_contractor_details(link)
                all_data.append(details)
                time.sleep(0.5)  # polite delay
            except Exception as e:
                print(f"❌ Failed to scrape {link}: {e}")

    # Save to DataFrame and CSV
    df = pd.DataFrame(all_data)
    df.to_csv("Electricians.csv", index=False)
    print("\n✅ Data saved to Electricians.csv")

if __name__ == "__main__":
    main()
